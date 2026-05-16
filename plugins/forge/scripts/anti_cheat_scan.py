#!/usr/bin/env python3
"""
Forge anti-cheat scanner.

Modes:
  fast         - PostToolUse hook; scans recently modified files; warns only.
  full         - Ralph Loop gate; scans staged + unstaged + untracked; exits non-zero on block.
  stubs-state  - Reports scaffolded-stub allowlist health (counts) for /forge:status.

Allowlist sources (checked in order):

  1. .forge/scaffolded-stubs.json (state-derived; written by skeleton-scaffolder)
     {
       "scaffolded_at": "ISO-8601",
       "stubs": [
         {"path": "...", "stub_sha256": "...", "pattern": "...", "task": "..."}
       ]
     }
     A hit is allowed iff the file's current SHA-256 matches the recorded
     stub_sha256 (i.e. file has not been modified since scaffold). Any change
     to the file auto-expires its entry — no human action required.

  2. .forge/anti-cheat.yaml (legacy human-managed):

       allowlist:
         - pattern: <tag>          # NOT_IMPLEMENTED, EMPTY_BODY, SKIPPED_TEST, HARDCODED_FAKE,
                                   # MOCK_IN_PROD, TODO_MARKER, MAGIC_OK
           paths:                  # glob patterns; if omitted, allowlist applies everywhere
             - "src/scaffold/**"
           reason: "scaffold-stage stubs"     # in strict mode, must start with "STRICT_OK:"
           expires_at: "2026-05-21"           # ignored in strict mode

Strict mode (--strict or FORGE_ANTI_CHEAT_STRICT=1):
  - YAML allowlist entries are honored only if reason starts with "STRICT_OK:".
  - expires_at is ignored.
  - SHA-based entries from scaffolded-stubs.json still apply (state-justified).
  - Auto no-op when .forge/prd.json reports any task passes:false (Phase 2 in flight).

Prefers PyYAML; falls back to a hand-rolled parser tight to this schema if PyYAML missing.
"""

from __future__ import annotations
import argparse
import datetime as dt
import fnmatch
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ---------- Patterns ----------

@dataclass
class Pattern:
    tag: str
    severity: str               # "block" or "warn"
    regex: re.Pattern
    only_in: str | None = None  # "test", "prod", or None for any
    path_filter: re.Pattern | None = None

PATTERNS: list[Pattern] = [
    Pattern("NOT_IMPLEMENTED", "block",
            re.compile(r"NotImplementedError|raise NotImplemented(?!Error)\b")),
    Pattern("EMPTY_BODY", "block",
            re.compile(r"^\s*pass\s*(?:#.*)?$"),
            only_in="prod"),
    Pattern("SKIPPED_TEST", "block",
            re.compile(r"@skip\b|pytest\.mark\.skip|\.skip\(|\bxit\(|\bit\.skip\("),
            only_in="test"),
    Pattern("HARDCODED_FAKE", "block",
            re.compile(r"""getenv\s*\(\s*["'][^"']+["']\s*,\s*["'](?:fake|test|dummy|placeholder|changeme|secret|password)""", re.I)),
    Pattern("MOCK_IN_PROD", "block",
            re.compile(r"^\s*(?:import\s+mock\b|from\s+mock\s+import|from\s+unittest\.mock\s+import)"),
            only_in="prod"),
    Pattern("TODO_MARKER", "warn",
            re.compile(r"\b(?:TODO|FIXME|XXX|HACK)\b")),
    Pattern("MAGIC_OK", "warn",
            re.compile(r"return\s+[\"'](?:ok|success|done|yes)[\"']", re.I)),
]

# ---------- File classification ----------

TEST_PATH_RE = re.compile(r"(^|/)(tests?|spec)(/|$)|[._-]test\.|[._-]spec\.")
SKIP_PATHS = (
    ".git/", "node_modules/", ".forge/", "dist/", "build/", ".next/",
    ".venv/", "venv/", "__pycache__/", ".pytest_cache/", "target/",
)
SKIP_EXTS = {".md", ".lock", ".png", ".jpg", ".jpeg", ".gif", ".svg",
             ".pdf", ".woff", ".woff2", ".ttf", ".ico", ".min.js"}

def should_skip(path: str) -> bool:
    if any(seg in path for seg in SKIP_PATHS):
        return True
    ext = os.path.splitext(path)[1].lower()
    if ext in SKIP_EXTS:
        return True
    return False

def is_test_file(path: str) -> bool:
    return bool(TEST_PATH_RE.search(path))

# ---------- Scaffolded-stub state ----------

@dataclass
class StubEntry:
    path: str
    stub_sha256: str
    pattern: str = ""
    task: str = ""

def load_scaffolded_stubs(path: Path) -> dict[str, StubEntry]:
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        print(f"[anti-cheat] failed to parse scaffolded-stubs.json: {e}", file=sys.stderr)
        return {}
    out: dict[str, StubEntry] = {}
    for item in raw.get("stubs", []) or []:
        if not isinstance(item, dict):
            continue
        p = item.get("path")
        sha = item.get("stub_sha256")
        if not p or not sha:
            continue
        out[str(p)] = StubEntry(
            path=str(p),
            stub_sha256=str(sha),
            pattern=str(item.get("pattern", "")),
            task=str(item.get("task", "")),
        )
    return out

def file_sha256(path: Path) -> str | None:
    try:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None

@dataclass
class StubsState:
    total: int = 0
    still_stub: list[str] = field(default_factory=list)
    filled_in: list[str] = field(default_factory=list)
    stale: list[str] = field(default_factory=list)   # path recorded but file missing

def compute_stubs_state(stubs: dict[str, StubEntry]) -> StubsState:
    s = StubsState(total=len(stubs))
    for path, entry in stubs.items():
        p = Path(path)
        if not p.exists():
            s.stale.append(path)
            continue
        cur = file_sha256(p)
        if cur == entry.stub_sha256:
            s.still_stub.append(path)
        else:
            s.filled_in.append(path)
    return s

# ---------- YAML allowlist (legacy) ----------

@dataclass
class AllowEntry:
    pattern: str
    paths: list[str] = field(default_factory=list)
    reason: str = ""
    expires_at: dt.date | None = None

    def applies(self, tag: str, path: str, *, strict: bool = False) -> bool:
        if self.pattern != tag:
            return False
        if strict:
            if not self.reason.startswith("STRICT_OK:"):
                return False
        elif self.expires_at and dt.date.today() > self.expires_at:
            return False
        if not self.paths:
            return True
        return any(fnmatch.fnmatch(path, pat) for pat in self.paths)

def load_allowlist(allowlist_path: Path) -> list[AllowEntry]:
    if not allowlist_path.exists():
        return []
    try:
        import yaml  # type: ignore
        raw = yaml.safe_load(allowlist_path.read_text()) or {}
    except ImportError:
        raw = _minimal_yaml_parse(allowlist_path.read_text())
    except Exception as e:
        print(f"[anti-cheat] failed to parse allowlist: {e}", file=sys.stderr)
        return []

    entries: list[AllowEntry] = []
    for item in raw.get("allowlist", []) or []:
        if not isinstance(item, dict):
            continue
        exp = item.get("expires_at")
        exp_date: dt.date | None = None
        if isinstance(exp, str):
            try:
                exp_date = dt.date.fromisoformat(exp)
            except ValueError:
                pass
        elif isinstance(exp, dt.date):
            exp_date = exp
        entries.append(AllowEntry(
            pattern=str(item.get("pattern", "")),
            paths=list(item.get("paths") or []),
            reason=str(item.get("reason", "")),
            expires_at=exp_date,
        ))
        if exp_date and dt.date.today() > exp_date:
            print(f"[anti-cheat] WARN: allowlist entry for '{item.get('pattern')}' expired {exp}", file=sys.stderr)
    return entries

def _minimal_yaml_parse(text: str) -> dict:
    """Last-resort parser for the fixed allowlist schema. No nesting beyond what's documented."""
    out: dict = {"allowlist": []}
    cur: dict | None = None
    in_allowlist = False
    in_paths = False
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line or line.lstrip().startswith("#"):
            continue
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if stripped.startswith("allowlist:") and indent == 0:
            in_allowlist = True
            continue
        if not in_allowlist:
            continue
        if stripped.startswith("- "):
            cur = {}
            out["allowlist"].append(cur)
            kv = stripped[2:]
            if ":" in kv:
                k, _, v = kv.partition(":")
                cur[k.strip()] = _strip_quotes(v.strip())
            in_paths = False
            continue
        if cur is None:
            continue
        if stripped.startswith("paths:"):
            cur["paths"] = []
            in_paths = True
            continue
        if in_paths and stripped.startswith("- "):
            cur["paths"].append(_strip_quotes(stripped[2:].strip()))
            continue
        if ":" in stripped:
            k, _, v = stripped.partition(":")
            cur[k.strip()] = _strip_quotes(v.strip())
            in_paths = False
    return out

def _strip_quotes(s: str) -> str:
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return s[1:-1]
    return s

# ---------- Strict-mode degrade check ----------

def phase2_in_progress(prd_json: Path) -> bool:
    """Return True if any task in prd.json has passes:false."""
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

# ---------- Scan ----------

@dataclass
class Hit:
    path: str
    line: int
    tag: str
    severity: str
    excerpt: str

# Per-process SHA cache: avoid hashing a file once per hit.
_sha_cache: dict[str, str | None] = {}

def _cached_sha(path: str) -> str | None:
    if path not in _sha_cache:
        _sha_cache[path] = file_sha256(Path(path))
    return _sha_cache[path]

def hit_is_allowed(
    rel: str,
    tag: str,
    *,
    stubs: dict[str, StubEntry],
    allowlist: list[AllowEntry],
    strict: bool,
) -> bool:
    # 1. SHA-based stub allowlist (state-justified, valid in strict + lenient).
    entry = stubs.get(rel)
    if entry is not None:
        cur = _cached_sha(rel)
        if cur is not None and cur == entry.stub_sha256:
            return True
        # SHA mismatch -> auto-expired; fall through.
    # 2. Legacy YAML allowlist.
    return any(a.applies(tag, rel, strict=strict) for a in allowlist)

def scan_file(
    path: Path,
    allowlist: list[AllowEntry],
    *,
    stubs: dict[str, StubEntry] | None = None,
    strict: bool = False,
) -> list[Hit]:
    rel = str(path)
    stubs = stubs or {}
    if should_skip(rel):
        return []
    try:
        text = path.read_text(errors="replace")
    except (OSError, UnicodeDecodeError):
        return []

    is_test = is_test_file(rel)
    hits: list[Hit] = []
    for lineno, line in enumerate(text.splitlines(), start=1):
        for p in PATTERNS:
            if p.only_in == "test" and not is_test:
                continue
            if p.only_in == "prod" and is_test:
                continue
            if not p.regex.search(line):
                continue
            if hit_is_allowed(rel, p.tag, stubs=stubs, allowlist=allowlist, strict=strict):
                continue
            hits.append(Hit(rel, lineno, p.tag, p.severity, line.strip()[:200]))
    return hits

def recent_files(minutes: int = 5) -> list[Path]:
    cutoff = dt.datetime.now().timestamp() - minutes * 60
    out: list[Path] = []
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if not any(("/" + d + "/").startswith("/" + s.rstrip("/") + "/") for s in SKIP_PATHS)]
        for fn in files:
            p = Path(root, fn)
            try:
                if p.stat().st_mtime >= cutoff:
                    out.append(p)
            except OSError:
                continue
    return out

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
        return [Path(p) for p in seen]
    except FileNotFoundError:
        return []

# ---------- Stubs-state report ----------

def print_stubs_state() -> int:
    stubs = load_scaffolded_stubs(Path(".forge/scaffolded-stubs.json"))
    if not stubs:
        print("  scaffolded stubs:   (no scaffolded-stubs.json)")
        return 0
    s = compute_stubs_state(stubs)
    print(f"  scaffolded stubs:   {s.total} total")
    print(f"    still stub:       {len(s.still_stub)}")
    print(f"    filled in:        {len(s.filled_in)}")
    print(f"    stale (missing):  {len(s.stale)}")
    if s.still_stub:
        sample = ", ".join(s.still_stub[:3])
        more = f" (+{len(s.still_stub)-3} more)" if len(s.still_stub) > 3 else ""
        print(f"    pending:          {sample}{more}")
    return 0

# ---------- Entry ----------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["fast", "full", "stubs-state"])
    ap.add_argument("--strict", action="store_true",
                    help="ignore expires_at; require STRICT_OK: prefix on YAML entries.")
    args = ap.parse_args()

    if args.mode == "stubs-state":
        return print_stubs_state()

    strict = args.strict or os.environ.get("FORGE_ANTI_CHEAT_STRICT") == "1"

    # Degrade strict to lenient while Phase 2 is in flight.
    if strict and phase2_in_progress(Path(".forge/prd.json")):
        print("[anti-cheat] strict mode requested but Phase 2 in flight "
              "(prd.json has passes:false tasks); running lenient.", file=sys.stderr)
        strict = False

    allowlist = load_allowlist(Path(".forge/anti-cheat.yaml"))
    stubs = load_scaffolded_stubs(Path(".forge/scaffolded-stubs.json"))

    if args.mode == "fast":
        files = recent_files(minutes=5)
    else:
        files = git_changed_files()
        if not files:
            print("[anti-cheat] not a git repo or no changes; skipping full scan", file=sys.stderr)
            return 0

    blocked = 0
    warned = 0
    for f in files:
        for h in scan_file(f, allowlist, stubs=stubs, strict=strict):
            print(f"[anti-cheat:{h.severity}] {h.path}:{h.line} [{h.tag}] {h.excerpt}", file=sys.stderr)
            if h.severity == "block":
                blocked += 1
            else:
                warned += 1

    tag = "strict" if strict else "lenient"
    if args.mode == "fast":
        if blocked or warned:
            print(f"[anti-cheat:{tag}] {blocked} blocks, {warned} warnings (fast pass, non-blocking)", file=sys.stderr)
        return 0

    if blocked:
        print(f"[anti-cheat:{tag}] BLOCKED: {blocked} block-severity hits ({warned} warnings)", file=sys.stderr)
        return 1
    if warned:
        print(f"[anti-cheat:{tag}] OK: 0 blocks, {warned} warnings", file=sys.stderr)
    return 0

if __name__ == "__main__":
    sys.exit(main())
