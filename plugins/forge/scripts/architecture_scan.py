#!/usr/bin/env python3
"""
Forge architecture-fitness scanner.

Sister gate to anti_cheat_scan.py. Where anti-cheat catches lies-about-behavior
(NotImplementedError, hardcoded fakes), this gate catches lies-about-shape
(god objects, shotgun surgery, distributed coupling).

Modes:
  fast       - PostToolUse-equivalent; scans recently modified files; warns only.
  full       - Ralph Loop gate; scans staged + unstaged + untracked; exits non-zero on block.
  baseline   - Snapshot current metrics for every tracked file to
               .forge/baseline-metrics.json. Called by blast-radius-mapper or
               manually before refactor.
  state      - Report current vs. baseline drift counts (for /forge:status).

Strict mode (--strict or FORGE_ARCH_STRICT=1):
  - Override-comment reasons must start with "STRICT_OK:" to be honored.
  - Auto no-op when .forge/prd.json reports any task passes:false (Phase 2 in flight),
    matching anti-cheat strict-degrade discipline.

Override syntax (anywhere in file body for file-level, on line preceding a
def/class for that scope):

    # forge: architecture-exempt reason="legacy ABC-123, planned extraction T15"
    // forge: architecture-exempt reason="STRICT_OK: third-party generated stub"

Each honored override appends a JSONL line to
.forge/architecture-exemptions.jsonl so the exemption surface stays auditable.

Differential rule (when .forge/baseline-metrics.json exists):
  - File metric was under threshold + is now over   -> BLOCK (regression).
  - File metric was over threshold + got worse      -> BLOCK (can't make bad worse).
  - File metric was over + stays equal              -> WARN (legacy carry-over).
  - File metric was over + got better               -> PASS (improvement).
  - File metric stays under threshold               -> PASS.

Languages handled in v1:
  - Python (ast): file_loc, function_loc, class_methods, fan_in.
  - TS / JS / TSX / JSX (regex heuristic): file_loc, class_methods, fan_in.
  - Anything else: file_loc only.

Thresholds (default; override via .forge/architecture.yaml):
  file_loc:      400
  function_loc:  60
  class_methods: 15
  fan_in:        12

Prefers PyYAML; falls back to a hand-rolled parser tight to this schema.
"""

from __future__ import annotations
import argparse
import ast
import datetime as dt
import fnmatch
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path

# ---------- Defaults ----------

DEFAULT_THRESHOLDS = {
    "file_loc": 400,
    "function_loc": 60,
    "class_methods": 15,
    "fan_in": 12,
}

DEFAULT_EXCLUDE = [
    "test/**", "tests/**", "**/*.test.*", "**/*.spec.*",
    "**/*_test.py", "**/test_*.py",
    "node_modules/**", "dist/**", "build/**", ".next/**",
    ".venv/**", "venv/**", "__pycache__/**", ".forge/**",
    ".git/**", "target/**",
]

SKIP_EXTS = {
    ".md", ".lock", ".png", ".jpg", ".jpeg", ".gif", ".svg",
    ".pdf", ".woff", ".woff2", ".ttf", ".ico", ".min.js",
    ".json", ".yaml", ".yml", ".toml", ".ini", ".cfg",
}

PY_EXTS = {".py"}
JSTS_EXTS = {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs"}

OVERRIDE_RE = re.compile(
    r'(?:#|//)\s*forge:\s*architecture-exempt\s+reason="([^"]*)"'
)

# ---------- Config ----------

@dataclass
class Config:
    thresholds: dict
    exclude_paths: list[str]
    overrides_log: str = ".forge/architecture-exemptions.jsonl"

def load_config(path: Path) -> Config:
    if not path.exists():
        return Config(
            thresholds=dict(DEFAULT_THRESHOLDS),
            exclude_paths=list(DEFAULT_EXCLUDE),
        )
    try:
        import yaml  # type: ignore
        raw = yaml.safe_load(path.read_text()) or {}
    except ImportError:
        raw = _minimal_yaml_parse(path.read_text())
    except Exception as e:
        print(f"[arch] failed to parse architecture.yaml: {e}", file=sys.stderr)
        raw = {}
    th = dict(DEFAULT_THRESHOLDS)
    for k, v in (raw.get("thresholds") or {}).items():
        if isinstance(v, int) and v > 0:
            th[k] = v
    excludes = list(raw.get("exclude_paths") or DEFAULT_EXCLUDE)
    log = (raw.get("overrides") or {}).get("log") or ".forge/architecture-exemptions.jsonl"
    return Config(thresholds=th, exclude_paths=excludes, overrides_log=log)

def _minimal_yaml_parse(text: str) -> dict:
    """Tight parser for architecture.yaml schema. No deep nesting."""
    out: dict = {"thresholds": {}, "exclude_paths": [], "overrides": {}}
    section: str | None = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if indent == 0 and stripped.endswith(":"):
            key = stripped[:-1]
            section = key if key in ("thresholds", "exclude_paths", "overrides") else None
            continue
        if section == "thresholds" and ":" in stripped:
            k, _, v = stripped.partition(":")
            v = v.strip()
            try:
                out["thresholds"][k.strip()] = int(v)
            except ValueError:
                pass
        elif section == "exclude_paths" and stripped.startswith("- "):
            out["exclude_paths"].append(_strip_quotes(stripped[2:].strip()))
        elif section == "overrides" and ":" in stripped:
            k, _, v = stripped.partition(":")
            out["overrides"][k.strip()] = _strip_quotes(v.strip())
    return out

def _strip_quotes(s: str) -> str:
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return s[1:-1]
    return s

# ---------- File classification ----------

def should_skip(path: str, exclude_globs: list[str]) -> bool:
    if any(fnmatch.fnmatch(path, pat) for pat in exclude_globs):
        return True
    ext = os.path.splitext(path)[1].lower()
    if ext in SKIP_EXTS:
        return True
    return False

# ---------- Metrics ----------

@dataclass
class FileMetrics:
    file_loc: int = 0
    max_function_loc: int = 0
    max_class_methods: int = 0
    # fan_in is per-symbol, not per-file; stored separately

@dataclass
class FanInHit:
    path: str
    symbol: str
    line: int          # line where def lives
    callers: int

@dataclass
class Violation:
    path: str
    line: int          # 0 = file-level
    kind: str          # file_loc | function_loc | class_methods | fan_in
    metric: int
    threshold: int
    detail: str = ""
    override_reason: str | None = None
    severity: str = "block"  # block | warn

def measure_python(text: str) -> tuple[FileMetrics, list[tuple[str, int, str]]]:
    """Return (metrics, [(symbol, line, kind)]) where kind in {'def','class'}."""
    fm = FileMetrics()
    fm.file_loc = _count_loc(text)
    symbols: list[tuple[str, int, str]] = []
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return fm, symbols
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end = getattr(node, "end_lineno", node.lineno) or node.lineno
            span = max(1, end - node.lineno + 1)
            fm.max_function_loc = max(fm.max_function_loc, span)
            symbols.append((node.name, node.lineno, "def"))
        elif isinstance(node, ast.ClassDef):
            method_count = sum(
                1 for child in node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            )
            fm.max_class_methods = max(fm.max_class_methods, method_count)
            symbols.append((node.name, node.lineno, "class"))
    return fm, symbols

_TS_CLASS_RE = re.compile(r"^\s*(?:export\s+)?(?:abstract\s+)?class\s+(\w+)", re.M)
_TS_METHOD_RE = re.compile(r"^\s*(?:public\s+|private\s+|protected\s+|static\s+|async\s+)*(\w+)\s*\(", re.M)
_TS_FUNC_RE = re.compile(r"^\s*(?:export\s+)?(?:async\s+)?function\s+(\w+)", re.M)
_TS_CONST_FUNC_RE = re.compile(r"^\s*(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s+)?\(", re.M)

def measure_jsts(text: str) -> tuple[FileMetrics, list[tuple[str, int, str]]]:
    fm = FileMetrics()
    fm.file_loc = _count_loc(text)
    symbols: list[tuple[str, int, str]] = []
    lines = text.splitlines()

    # Classes + naive method count (heuristic; brace-matched).
    for m in _TS_CLASS_RE.finditer(text):
        name = m.group(1)
        line = text[:m.start()].count("\n") + 1
        symbols.append((name, line, "class"))
        # Walk forward to find opening brace; count direct-child methods.
        i = m.end()
        depth = 0
        started = False
        method_count = 0
        body_start = -1
        for j in range(i, len(text)):
            c = text[j]
            if c == "{":
                if not started:
                    started = True
                    body_start = j + 1
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0 and started:
                    body = text[body_start:j]
                    for mm in _TS_METHOD_RE.finditer(body):
                        kw = mm.group(1)
                        if kw in ("if", "for", "while", "switch", "return", "catch", "function", "constructor"):
                            continue
                        method_count += 1
                    break
        fm.max_class_methods = max(fm.max_class_methods, method_count)

    # Top-level functions: name only (function_loc not computed for v1 in JS/TS).
    for m in _TS_FUNC_RE.finditer(text):
        line = text[:m.start()].count("\n") + 1
        symbols.append((m.group(1), line, "def"))
    for m in _TS_CONST_FUNC_RE.finditer(text):
        line = text[:m.start()].count("\n") + 1
        symbols.append((m.group(1), line, "def"))
    return fm, symbols

def measure_generic(text: str) -> tuple[FileMetrics, list[tuple[str, int, str]]]:
    return FileMetrics(file_loc=_count_loc(text)), []

def _count_loc(text: str) -> int:
    """Non-blank, non-comment-only lines."""
    n = 0
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith("#") or s.startswith("//"):
            continue
        n += 1
    return n

def measure(path: Path) -> tuple[FileMetrics, list[tuple[str, int, str]]]:
    try:
        text = path.read_text(errors="replace")
    except (OSError, UnicodeDecodeError):
        return FileMetrics(), []
    ext = path.suffix.lower()
    if ext in PY_EXTS:
        return measure_python(text)
    if ext in JSTS_EXTS:
        return measure_jsts(text)
    return measure_generic(text)

# ---------- Fan-in ----------

_IDENT_RE = re.compile(r"\bword\b")  # rebuilt per-symbol

def fan_in_for_symbol(symbol: str, defining_path: str, repo_root: Path) -> int:
    """Cheap fan-in: count files (excluding the defining file) that reference `symbol`.

    Uses ripgrep if available; falls back to git grep; falls back to Python walk.
    Counts file count rather than occurrence count to avoid penalizing tight loops.
    """
    # ripgrep
    rg = _which("rg")
    if rg:
        try:
            r = subprocess.run(
                [rg, "-l", "-w", "--no-messages", symbol, "."],
                capture_output=True, text=True, check=False, cwd=str(repo_root),
            )
            files = {ln.strip() for ln in r.stdout.splitlines() if ln.strip()}
            files.discard(defining_path)
            files.discard(defining_path.lstrip("./"))
            return len(files)
        except OSError:
            pass
    # git grep
    try:
        r = subprocess.run(
            ["git", "grep", "-l", "-w", symbol],
            capture_output=True, text=True, check=False, cwd=str(repo_root),
        )
        if r.returncode in (0, 1):
            files = {ln.strip() for ln in r.stdout.splitlines() if ln.strip()}
            files.discard(defining_path)
            files.discard(defining_path.lstrip("./"))
            return len(files)
    except (OSError, FileNotFoundError):
        pass
    return 0

def _which(cmd: str) -> str | None:
    for p in os.environ.get("PATH", "").split(os.pathsep):
        c = os.path.join(p, cmd)
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    return None

# ---------- Override scanning ----------

def file_level_override(text: str) -> str | None:
    """First override comment in top 20 lines of file -> file-level exempt."""
    head = "\n".join(text.splitlines()[:20])
    m = OVERRIDE_RE.search(head)
    return m.group(1) if m else None

def line_preceding_override(text: str, line: int) -> str | None:
    """Override on the line immediately preceding `line` (1-indexed)."""
    lines = text.splitlines()
    if line < 2 or line - 2 >= len(lines):
        return None
    prev = lines[line - 2]
    m = OVERRIDE_RE.search(prev)
    return m.group(1) if m else None

def override_valid(reason: str, *, strict: bool) -> bool:
    if not reason:
        return False
    if strict and not reason.startswith("STRICT_OK:"):
        return False
    return True

# ---------- Baseline (differential gate) ----------

@dataclass
class Baseline:
    files: dict[str, dict]    # path -> {file_loc, max_function_loc, max_class_methods}

    @classmethod
    def empty(cls) -> "Baseline":
        return cls(files={})

    def get(self, path: str, key: str) -> int | None:
        return (self.files.get(path) or {}).get(key)

def load_baseline(p: Path) -> Baseline:
    if not p.exists():
        return Baseline.empty()
    try:
        raw = json.loads(p.read_text())
    except (OSError, json.JSONDecodeError):
        return Baseline.empty()
    files = raw.get("files") or {}
    if not isinstance(files, dict):
        return Baseline.empty()
    return Baseline(files=files)

# ---------- Exemption logging ----------

def log_exemption(log_path: Path, *, path: str, kind: str, reason: str,
                  metric: int, threshold: int) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": dt.datetime.now(dt.timezone.utc).isoformat(),
        "path": path,
        "kind": kind,
        "metric": metric,
        "threshold": threshold,
        "reason": reason,
    }
    with log_path.open("a") as f:
        f.write(json.dumps(entry) + "\n")

# ---------- Strict-mode degrade (matches anti-cheat) ----------

def phase2_in_progress(prd_json: Path) -> bool:
    if not prd_json.exists():
        return False
    try:
        raw = json.loads(prd_json.read_text())
    except (OSError, json.JSONDecodeError):
        return False
    for t in raw.get("tasks", []) or []:
        if isinstance(t, dict) and t.get("passes") is False:
            return True
    return False

# ---------- Discovery ----------

def git_changed_files() -> list[Path]:
    try:
        cmds = [
            ["git", "diff", "--name-only", "HEAD"],
            ["git", "diff", "--name-only", "--cached"],
            ["git", "ls-files", "--others", "--exclude-standard"],
        ]
        seen: set[str] = set()
        for c in cmds:
            r = subprocess.run(c, capture_output=True, text=True, check=False)
            for line in r.stdout.splitlines():
                line = line.strip()
                if line and line not in seen:
                    seen.add(line)
        return [Path(p) for p in seen if Path(p).exists()]
    except FileNotFoundError:
        return []

def git_tracked_files() -> list[Path]:
    try:
        r = subprocess.run(
            ["git", "ls-files"],
            capture_output=True, text=True, check=False,
        )
        return [Path(p.strip()) for p in r.stdout.splitlines() if p.strip()]
    except FileNotFoundError:
        return []

def recent_files(minutes: int = 5) -> list[Path]:
    cutoff = dt.datetime.now().timestamp() - minutes * 60
    skip = {".git", "node_modules", ".forge", "dist", "build", ".next",
            ".venv", "venv", "__pycache__"}
    out: list[Path] = []
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in skip]
        for fn in files:
            p = Path(root, fn)
            try:
                if p.stat().st_mtime >= cutoff:
                    out.append(p)
            except OSError:
                continue
    return out

# ---------- Scan ----------

def diff_status(cur: int, base: int | None, threshold: int) -> tuple[str, str]:
    """Return (severity, detail). Severity in {pass, warn, block}."""
    if cur <= threshold:
        return "pass", ""
    if base is None:
        return "block", f"{cur} > {threshold} (no baseline)"
    if base <= threshold:
        return "block", f"{cur} > {threshold} (was {base}, threshold crossed)"
    if cur > base:
        return "block", f"{cur} > {base} (already over {threshold}, regressed)"
    if cur == base:
        return "warn", f"{cur} (carry-over; over {threshold} since baseline)"
    return "pass", ""

def scan_file(
    path: Path,
    cfg: Config,
    baseline: Baseline,
    *,
    strict: bool,
    exemption_log: Path,
) -> list[Violation]:
    rel = str(path).lstrip("./")
    if should_skip(rel, cfg.exclude_paths):
        return []
    try:
        text = path.read_text(errors="replace")
    except (OSError, UnicodeDecodeError):
        return []
    fm, symbols = measure(path)
    file_override = file_level_override(text)
    th = cfg.thresholds
    violations: list[Violation] = []

    # File-level checks
    for kind, cur in (
        ("file_loc", fm.file_loc),
        ("max_function_loc", fm.max_function_loc),
        ("max_class_methods", fm.max_class_methods),
    ):
        threshold_key = {
            "file_loc": "file_loc",
            "max_function_loc": "function_loc",
            "max_class_methods": "class_methods",
        }[kind]
        threshold = th[threshold_key]
        if cur <= 0:
            continue
        base = baseline.get(rel, kind)
        sev, detail = diff_status(cur, base, threshold)
        if sev == "pass":
            continue
        # Override: file-level only (function-level needs symbol locator; v1 = file scope).
        if file_override is not None and override_valid(file_override, strict=strict):
            log_exemption(exemption_log, path=rel, kind=threshold_key,
                          reason=file_override, metric=cur, threshold=threshold)
            continue
        violations.append(Violation(
            path=rel, line=0, kind=threshold_key, metric=cur, threshold=threshold,
            detail=detail, severity=sev,
        ))

    # Fan-in (cheap, only when there are defined symbols)
    if symbols:
        repo_root = Path(".").resolve()
        fan_threshold = th["fan_in"]
        for name, line, _kind in symbols:
            if len(name) < 3 or not name.isidentifier():
                continue
            callers = fan_in_for_symbol(name, rel, repo_root)
            if callers <= fan_threshold:
                continue
            override = line_preceding_override(text, line) or file_override
            if override is not None and override_valid(override, strict=strict):
                log_exemption(exemption_log, path=f"{rel}:{name}", kind="fan_in",
                              reason=override, metric=callers, threshold=fan_threshold)
                continue
            violations.append(Violation(
                path=rel, line=line, kind="fan_in", metric=callers,
                threshold=fan_threshold,
                detail=f"{callers} caller files for `{name}` > {fan_threshold}",
                severity="block",
            ))

    return violations

# ---------- Baseline command ----------

def write_baseline(out: Path) -> int:
    cfg = load_config(Path(".forge/architecture.yaml"))
    files = git_tracked_files()
    snapshot: dict[str, dict] = {}
    for f in files:
        rel = str(f).lstrip("./")
        if should_skip(rel, cfg.exclude_paths):
            continue
        if not f.exists():
            continue
        fm, _syms = measure(f)
        if fm.file_loc <= 0 and fm.max_function_loc <= 0 and fm.max_class_methods <= 0:
            continue
        snapshot[rel] = {
            "file_loc": fm.file_loc,
            "max_function_loc": fm.max_function_loc,
            "max_class_methods": fm.max_class_methods,
        }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "captured_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "thresholds": cfg.thresholds,
        "files": snapshot,
    }, indent=2))
    print(f"[arch] baseline written: {len(snapshot)} files -> {out}", file=sys.stderr)
    return 0

# ---------- State report ----------

def print_state(cfg: Config, baseline: Baseline) -> int:
    if not baseline.files:
        print("  architecture:       (no baseline-metrics.json)")
        return 0
    th = cfg.thresholds
    over_before = 0
    over_now = 0
    regressed: list[str] = []
    improved: list[str] = []
    for rel, b in baseline.files.items():
        was_over = (
            b.get("file_loc", 0) > th["file_loc"]
            or b.get("max_function_loc", 0) > th["function_loc"]
            or b.get("max_class_methods", 0) > th["class_methods"]
        )
        if was_over:
            over_before += 1
        p = Path(rel)
        if not p.exists():
            continue
        fm, _ = measure(p)
        is_over = (
            fm.file_loc > th["file_loc"]
            or fm.max_function_loc > th["function_loc"]
            or fm.max_class_methods > th["class_methods"]
        )
        if is_over:
            over_now += 1
        if not was_over and is_over:
            regressed.append(rel)
        elif was_over and not is_over:
            improved.append(rel)
    print(f"  architecture:       baseline {len(baseline.files)} files")
    print(f"    over threshold:   was {over_before}, now {over_now}")
    print(f"    regressed:        {len(regressed)}")
    print(f"    improved:         {len(improved)}")
    if regressed:
        sample = ", ".join(regressed[:3])
        more = f" (+{len(regressed)-3} more)" if len(regressed) > 3 else ""
        print(f"    pending:          {sample}{more}")
    return 0

# ---------- Entry ----------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["fast", "full", "baseline", "state"])
    ap.add_argument("--strict", action="store_true",
                    help="ignore non-STRICT_OK overrides")
    ap.add_argument("--baseline-out", default=".forge/baseline-metrics.json",
                    help="output path for baseline mode")
    args = ap.parse_args()

    cfg = load_config(Path(".forge/architecture.yaml"))

    if args.mode == "baseline":
        return write_baseline(Path(args.baseline_out))

    baseline = load_baseline(Path(".forge/baseline-metrics.json"))

    if args.mode == "state":
        return print_state(cfg, baseline)

    strict = args.strict or os.environ.get("FORGE_ARCH_STRICT") == "1"
    if strict and phase2_in_progress(Path(".forge/prd.json")):
        print("[arch] strict mode requested but Phase 2 in flight "
              "(prd.json has passes:false tasks); running lenient.", file=sys.stderr)
        strict = False

    exemption_log = Path(cfg.overrides_log)

    if args.mode == "fast":
        files = recent_files(minutes=5)
    else:
        files = git_changed_files()
        if not files:
            print("[arch] not a git repo or no changes; skipping full scan", file=sys.stderr)
            return 0

    blocked = 0
    warned = 0
    for f in files:
        for v in scan_file(f, cfg, baseline, strict=strict, exemption_log=exemption_log):
            loc = f"{v.path}:{v.line}" if v.line else v.path
            print(f"[arch:{v.severity}] {loc} [{v.kind}] {v.detail}", file=sys.stderr)
            if v.severity == "block":
                blocked += 1
            else:
                warned += 1

    tag = "strict" if strict else "lenient"
    if args.mode == "fast":
        if blocked or warned:
            print(f"[arch:{tag}] {blocked} blocks, {warned} warnings (fast pass, non-blocking)",
                  file=sys.stderr)
        return 0

    if blocked:
        print(f"[arch:{tag}] BLOCKED: {blocked} block-severity violations "
              f"({warned} warnings). Add `# forge: architecture-exempt reason=\"...\"` "
              f"with justification, or split the file/function.", file=sys.stderr)
        return 1
    if warned:
        print(f"[arch:{tag}] OK: 0 blocks, {warned} warnings (legacy carry-over)",
              file=sys.stderr)
    return 0

if __name__ == "__main__":
    sys.exit(main())
