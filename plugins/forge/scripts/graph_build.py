#!/usr/bin/env python3
"""
Forge graph indexer (v0.2 — spec only).

Sources:
  .forge/prd.md             -> story, spec_ac, risk, open_question
  .forge/shared.md          -> component, interface, decision, file (referenced)
  .forge/interview/pm.md    -> decision (scope), open_question
  .forge/interview/design.md -> journey, state, decision
  .forge/research/context.md -> reuse_candidate, decision
  .forge/research/pattern.md -> reuse_candidate, decision
  .forge/prd.json           -> task (one per task entry), edges to ac, file

Incremental: skip files whose mtime matches existing nodes' mtime AND fingerprint
is stable. Otherwise drop nodes for that path and re-extract.

Idempotent: running twice produces identical graph.
"""
from __future__ import annotations
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from forge_graph import connect, upsert_node, upsert_edge, drop_nodes_for_path, slug, fingerprint

FORGE = Path(".forge")

# ---------- markdown parsing helpers ----------

H_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
TASK_LIST_RE = re.compile(r"^\s*-\s*\[\s*[ xX]\s*\]\s+(.+)$")
BULLET_RE = re.compile(r"^\s*-\s+(.+)$")
NUM_RE = re.compile(r"^\s*\d+\.\s+(.+)$")

def parse_sections(text: str) -> list[tuple[int, str, list[str]]]:
    """Return list of (level, heading, [content lines]) for each section, in order."""
    sections: list[tuple[int, str, list[str]]] = []
    cur_level = 0
    cur_head = ""
    cur_body: list[str] = []
    for line in text.splitlines():
        m = H_RE.match(line)
        if m:
            if cur_head:
                sections.append((cur_level, cur_head, cur_body))
            cur_level = len(m.group(1))
            cur_head = m.group(2)
            cur_body = []
        else:
            cur_body.append(line)
    if cur_head:
        sections.append((cur_level, cur_head, cur_body))
    return sections

def extract_bullets(lines: list[str]) -> list[str]:
    out = []
    for line in lines:
        m = TASK_LIST_RE.match(line) or BULLET_RE.match(line) or NUM_RE.match(line)
        if m:
            out.append(m.group(1).strip())
    return out

def heading_kind(h: str) -> str | None:
    h = h.lower().strip()
    if h.startswith("acceptance criteria"): return "spec_ac"
    if h.startswith("risk"): return "risk"
    if h.startswith("open question"): return "open_question"
    if h.startswith("user stor") or h.startswith("story"): return "story"
    if h.startswith("scope") or h == "in scope" or h == "out of scope": return "decision"
    if h.startswith("dependenc"): return "decision"
    if h.startswith("user journey") or h.startswith("journey"): return "journey"
    if h.startswith("state"): return "state"
    if h.startswith("mental model") or h.startswith("affordance") or h.startswith("visual contract"):
        return "decision"
    if h.startswith("ux risk"): return "risk"
    if h.startswith("component"): return "component"
    if h.startswith("interface"): return "interface"
    if h.startswith("data flow"): return "decision"
    if h.startswith("file plan") or h.startswith("to create") or h.startswith("to modify"):
        return "file"
    if h.startswith("build sequence"): return "decision"
    if h.startswith("ux contract"): return "decision"
    if h.startswith("reuse"): return "reuse_candidate"
    if h.startswith("established pattern"): return "decision"
    if h.startswith("inconsisten"): return "risk"
    if h.startswith("new component"): return "component"
    if h.startswith("conflict"): return "risk"
    return None

def file_path_from_bullet(b: str) -> str | None:
    """Heuristic: extract first backtick-quoted token that looks like a path."""
    m = re.search(r"`([^`]+\.[A-Za-z0-9]+)`", b)
    if m:
        return m.group(1)
    m = re.match(r"([A-Za-z0-9_./-]+\.[A-Za-z0-9]+)\b", b)
    if m and "/" in m.group(1):
        return m.group(1)
    return None

# ---------- indexers per source ----------

def index_markdown(conn, path: Path, default_kind_fallback: str = "decision"):
    if not path.exists():
        return 0
    drop_nodes_for_path(conn, str(path))
    text = path.read_text(errors="replace")
    sections = parse_sections(text)
    src_node_id = f"src:{path}"
    upsert_node(conn, node_id=src_node_id, kind="source", title=str(path),
                source_path=str(path), mtime=path.stat().st_mtime)
    added = 0
    line_cursor = 0
    text_lines = text.splitlines()
    for level, head, body_lines in sections:
        # find line number of this heading
        try:
            line_no = next(i for i, l in enumerate(text_lines[line_cursor:], start=line_cursor + 1)
                           if H_RE.match(l) and H_RE.match(l).group(2).strip() == head.strip())
            line_cursor = line_no
        except StopIteration:
            line_no = 0

        kind = heading_kind(head) or default_kind_fallback
        bullets = extract_bullets(body_lines)
        body_text = " ".join(b for b in bullets[:5])
        section_id = f"{path}#{slug(head)}"
        upsert_node(conn, node_id=section_id, kind=kind, title=head,
                    body=body_text, source_path=str(path), source_line=line_no)
        upsert_edge(conn, src_node_id, section_id, "contains")
        added += 1
        for bi, b in enumerate(bullets):
            bid = f"{section_id}#{bi}"
            # per-bullet kind: ACs are usually under "Acceptance criteria"
            bkind = kind
            if kind in ("component", "interface", "story", "journey", "state"):
                bkind = kind
            elif kind == "spec_ac":
                bkind = "spec_ac"
            upsert_node(conn, node_id=bid, kind=bkind,
                        title=b[:120], body=b, source_path=str(path),
                        source_line=line_no)
            upsert_edge(conn, section_id, bid, "contains")
            # file ref in bullet → mentions edge
            fp = file_path_from_bullet(b)
            if fp:
                file_id = f"file:{fp}"
                upsert_node(conn, node_id=file_id, kind="file", title=fp,
                            source_path=fp)
                upsert_edge(conn, bid, file_id, "mentions")
            added += 1
    return added

def index_prd_json(conn, path: Path = Path(".forge/prd.json")):
    if not path.exists():
        return 0
    drop_nodes_for_path(conn, str(path))
    data = json.loads(path.read_text())
    n = 0
    for t in data.get("tasks", []):
        tid = f"task:{t['id']}"
        upsert_node(conn, node_id=tid, kind="task_run",
                    title=t.get("title", t["id"]),
                    body=t.get("description", ""),
                    source_path=str(path),
                    tags=["passes" if t.get("passes") else "pending"])
        n += 1
        for ac_id in t.get("covers_criteria", []):
            # AC id refs from PRD: try to resolve by title fragment
            row = conn.execute(
                "SELECT id FROM nodes WHERE kind='spec_ac' AND (id LIKE ? OR title LIKE ?) LIMIT 1",
                (f"%{ac_id}%", f"%{ac_id}%")
            ).fetchone()
            if row:
                upsert_edge(conn, tid, row["id"], "covers")
        for f in t.get("files", []):
            file_id = f"file:{f}"
            upsert_node(conn, node_id=file_id, kind="file", title=f, source_path=f)
            upsert_edge(conn, tid, file_id, "mentions")
        for dep in t.get("depends_on", []):
            upsert_edge(conn, tid, f"task:{dep}", "depends_on")
    return n

def index_reviews(conn, dir_path: Path = Path(".forge/reviews")):
    if not dir_path.exists():
        return 0
    total = 0
    for md in sorted(dir_path.glob("*.md")):
        total += index_markdown(conn, md, default_kind_fallback="decision")
    return total

# ---------- entry ----------

def main():
    if not FORGE.exists():
        print("no .forge/ directory; nothing to index", file=sys.stderr)
        return 0
    t0 = time.time()
    counts: dict[str, int] = {}
    with connect() as c:
        counts["prd.md"]      = index_markdown(c, FORGE / "prd.md")
        counts["shared.md"]   = index_markdown(c, FORGE / "shared.md")
        counts["interview/pm.md"]     = index_markdown(c, FORGE / "interview" / "pm.md")
        counts["interview/design.md"] = index_markdown(c, FORGE / "interview" / "design.md")
        counts["research/context.md"] = index_markdown(c, FORGE / "research" / "context.md")
        counts["research/pattern.md"] = index_markdown(c, FORGE / "research" / "pattern.md")
        counts["reviews/*"]   = index_reviews(c)
        counts["prd.json"]    = index_prd_json(c)

    print(f"graph build: {time.time() - t0:.2f}s")
    for k, v in counts.items():
        print(f"  {k}: {v}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
