#!/usr/bin/env python3
"""
Forge graph store + query.

SQLite-backed. Two tables: nodes (typed entities) and edges (typed relations).

Node kinds (spec):    spec_ac, story, decision, journey, state, component,
                       interface, open_question, risk, reuse_candidate
Node kinds (code):    file, symbol, test         (deferred v0.3)
Node kinds (outcome): run, task_run, gate_event, blocker, pattern

Edge relations:       covers, depends_on, cites, conflicts_with, implements,
                       mentions, touched, fired_gate, blocked_by, resolved_by,
                       similar_to, uses_pattern

This module is a LIBRARY + thin CLI. graph_build.py is the indexer.
ralph-coder shells out to: `forge-graph context-for-task <id> --max-tokens N`.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import sqlite3
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

DB_PATH = Path(".forge/memory/graph.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS nodes (
  id TEXT PRIMARY KEY,
  kind TEXT NOT NULL,
  title TEXT,
  body TEXT,
  source_path TEXT,
  source_line INTEGER,
  tags_json TEXT DEFAULT '[]',
  mtime REAL,
  fingerprint TEXT,
  created_at REAL
);
CREATE TABLE IF NOT EXISTS edges (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  src TEXT NOT NULL,
  dst TEXT NOT NULL,
  rel TEXT NOT NULL,
  weight REAL DEFAULT 1.0,
  props_json TEXT DEFAULT '{}',
  created_at REAL,
  UNIQUE(src, dst, rel)
);
CREATE INDEX IF NOT EXISTS idx_nodes_kind ON nodes(kind);
CREATE INDEX IF NOT EXISTS idx_nodes_path ON nodes(source_path);
CREATE INDEX IF NOT EXISTS idx_edges_src ON edges(src);
CREATE INDEX IF NOT EXISTS idx_edges_dst ON edges(dst);
CREATE INDEX IF NOT EXISTS idx_edges_rel ON edges(rel);
"""

# ---------- store ----------

@contextmanager
def connect(db_path: Path = DB_PATH):
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()

def fingerprint(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="replace")).hexdigest()[:16]

def slug(s: str) -> str:
    return "".join(c if c.isalnum() else "-" for c in s.lower()).strip("-")[:60]

def upsert_node(conn, *, node_id: str, kind: str, title: str, body: str = "",
                source_path: str = "", source_line: int = 0,
                tags: list[str] | None = None, mtime: float | None = None) -> str:
    fp = fingerprint(f"{kind}|{title}|{body}")
    conn.execute(
        """INSERT INTO nodes (id, kind, title, body, source_path, source_line,
                              tags_json, mtime, fingerprint, created_at)
           VALUES (?,?,?,?,?,?,?,?,?,?)
           ON CONFLICT(id) DO UPDATE SET
             kind=excluded.kind, title=excluded.title, body=excluded.body,
             source_path=excluded.source_path, source_line=excluded.source_line,
             tags_json=excluded.tags_json, mtime=excluded.mtime,
             fingerprint=excluded.fingerprint""",
        (node_id, kind, title, body, source_path, source_line,
         json.dumps(tags or []), mtime or time.time(), fp, time.time()),
    )
    return node_id

def upsert_edge(conn, src: str, dst: str, rel: str,
                weight: float = 1.0, props: dict | None = None):
    conn.execute(
        """INSERT INTO edges (src, dst, rel, weight, props_json, created_at)
           VALUES (?,?,?,?,?,?)
           ON CONFLICT(src,dst,rel) DO UPDATE SET
             weight=excluded.weight, props_json=excluded.props_json""",
        (src, dst, rel, weight, json.dumps(props or {}), time.time()),
    )

def drop_nodes_for_path(conn, source_path: str):
    """Used by incremental rebuilder when a source file changed."""
    rows = conn.execute("SELECT id FROM nodes WHERE source_path = ?", (source_path,)).fetchall()
    ids = [r["id"] for r in rows]
    for nid in ids:
        conn.execute("DELETE FROM edges WHERE src = ? OR dst = ?", (nid, nid))
        conn.execute("DELETE FROM nodes WHERE id = ?", (nid,))

# ---------- query helpers ----------

def render_bullets(rows, max_tokens: int) -> list[str]:
    """Pack rows into bullets until token budget consumed (4 chars ~ 1 token)."""
    out = []
    used = 0
    for r in rows:
        cite = f" ({r['source_path']}:{r['source_line']})" if r["source_path"] else ""
        line = f"- [{r['kind']}] {r['title']}{cite}"
        if r["body"]:
            snippet = " ".join(r["body"].split())[:140]
            line += f" — {snippet}"
        cost = len(line) // 4
        if used + cost > max_tokens:
            break
        out.append(line)
        used += cost
    return out

def neighbors(conn, node_id: str, rels: list[str] | None = None, direction: str = "out"):
    if direction == "out":
        sql = "SELECT n.* FROM edges e JOIN nodes n ON n.id = e.dst WHERE e.src = ?"
    else:
        sql = "SELECT n.* FROM edges e JOIN nodes n ON n.id = e.src WHERE e.dst = ?"
    params: list = [node_id]
    if rels:
        sql += " AND e.rel IN (" + ",".join("?" * len(rels)) + ")"
        params.extend(rels)
    return conn.execute(sql, params).fetchall()

# ---------- CLI ----------

def cmd_status(args):
    if not DB_PATH.exists():
        print("graph: not initialized; run `forge-graph rebuild`")
        return 0
    with connect() as c:
        kinds = c.execute("SELECT kind, COUNT(*) n FROM nodes GROUP BY kind ORDER BY n DESC").fetchall()
        rels = c.execute("SELECT rel, COUNT(*) n FROM edges GROUP BY rel ORDER BY n DESC").fetchall()
        total_nodes = c.execute("SELECT COUNT(*) FROM nodes").fetchone()[0]
        total_edges = c.execute("SELECT COUNT(*) FROM edges").fetchone()[0]
    print(f"graph: {total_nodes} nodes, {total_edges} edges")
    print("  nodes by kind:")
    for r in kinds:
        print(f"    {r['kind']}: {r['n']}")
    if rels:
        print("  edges by rel:")
        for r in rels:
            print(f"    {r['rel']}: {r['n']}")
    return 0

def cmd_query(args):
    """Keyword / tag search across all nodes. Cheap LIKE-based."""
    with connect() as c:
        kw = args.query.strip()
        sql = """SELECT * FROM nodes
                 WHERE title LIKE ? OR body LIKE ? OR tags_json LIKE ?
                 ORDER BY mtime DESC LIMIT 50"""
        wild = f"%{kw}%"
        rows = c.execute(sql, (wild, wild, wild)).fetchall()
        if args.kind:
            rows = [r for r in rows if r["kind"] == args.kind]
    for line in render_bullets(rows, args.max_tokens):
        print(line)
    return 0

def cmd_context_for_task(args):
    """Pull focused context for a Ralph task:
       - the task_run/task node + its description
       - covered ACs
       - components implicated
       - decisions / risks mentioned
       - prior task_runs that touched same files (outcome edges)
       Capped by max-tokens.
    """
    task_id = args.task_id
    with connect() as c:
        # find task node (kind=task_run with source ".forge/prd.json", id derived as task:<id>)
        task = c.execute("SELECT * FROM nodes WHERE id = ?", (f"task:{task_id}",)).fetchone()
        sections: list[tuple[str, list]] = []
        if task:
            sections.append(("Task", [task]))
            covered = neighbors(c, f"task:{task_id}", ["covers"])
            if covered:
                sections.append(("Acceptance criteria covered", covered))
            implementing = neighbors(c, f"task:{task_id}", ["implements"])
            if implementing:
                sections.append(("Components / interfaces", implementing))
            # files (touched edges live on task_runs after Ralph runs; cheap files list lives on task props)
            files = c.execute("""
                SELECT n.* FROM edges e JOIN nodes n ON n.id = e.dst
                WHERE e.src = ? AND e.rel = 'mentions' AND n.kind = 'file'
            """, (f"task:{task_id}",)).fetchall()
            if files:
                sections.append(("Files in scope", files))
            # prior outcomes for same files
            prior = c.execute("""
                SELECT DISTINCT tr.* FROM edges e1
                JOIN edges e2 ON e1.dst = e2.dst AND e1.rel='touched' AND e2.rel='touched'
                JOIN nodes tr ON tr.id = e1.src
                WHERE e2.src = ? AND e1.src != ?
                ORDER BY tr.mtime DESC LIMIT 5
            """, (f"task:{task_id}", f"task:{task_id}")).fetchall()
            if prior:
                sections.append(("Prior task runs touching same files", prior))
        decisions = c.execute("""
            SELECT * FROM nodes WHERE kind IN ('decision','risk','open_question')
            ORDER BY mtime DESC LIMIT 10
        """).fetchall()
        if decisions:
            sections.append(("Decisions / risks / open questions", decisions))

    remaining = args.max_tokens
    for heading, rows in sections:
        if remaining <= 50:
            break
        print(f"## {heading}")
        bullets = render_bullets(rows, remaining)
        for b in bullets:
            print(b)
            remaining -= len(b) // 4
        print()
    return 0

def cmd_open_questions(args):
    with connect() as c:
        rows = c.execute("SELECT * FROM nodes WHERE kind='open_question' ORDER BY mtime DESC").fetchall()
        if args.topic:
            t = args.topic.lower()
            rows = [r for r in rows if t in (r["title"] or "").lower() or t in (r["body"] or "").lower()]
    for b in render_bullets(rows, args.max_tokens):
        print(b)
    return 0

def cmd_record_outcome(args):
    """Called by ralph-coder post-task. Records task_run outcome edges.
    Args: --task-id X --status passed|blocked --files a,b --gates static:pass,test:fail
    """
    files = [f.strip() for f in (args.files or "").split(",") if f.strip()]
    gates = [g.strip() for g in (args.gates or "").split(",") if g.strip()]
    run_id = f"taskrun:{args.task_id}:{int(time.time())}"
    with connect() as c:
        upsert_node(c, node_id=run_id, kind="task_run",
                    title=f"run of {args.task_id} ({args.status})",
                    body=f"gates: {','.join(gates)}",
                    source_path=".forge/prd.json")
        upsert_edge(c, run_id, f"task:{args.task_id}", "instance_of")
        for f in files:
            file_id = f"file:{f}"
            upsert_node(c, node_id=file_id, kind="file", title=f, source_path=f)
            upsert_edge(c, run_id, file_id, "touched")
        for g in gates:
            if ":" not in g:
                continue
            name, outcome = g.split(":", 1)
            gid = f"gate:{run_id}:{name}"
            upsert_node(c, node_id=gid, kind="gate_event",
                        title=f"{name} {outcome}", body=outcome)
            upsert_edge(c, run_id, gid, "fired_gate", props={"outcome": outcome})
    print(f"recorded {run_id}", file=sys.stderr)
    return 0

def cmd_export_graphify(args):
    """Dump nodes+edges as JSONL suitable for /graphify ingestion."""
    out_path = Path(args.out or ".forge/memory/graph-export.jsonl")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with connect() as c, out_path.open("w") as f:
        for r in c.execute("SELECT * FROM nodes").fetchall():
            f.write(json.dumps({"type": "node", **dict(r)}, ensure_ascii=False, default=str) + "\n")
        for r in c.execute("SELECT * FROM edges").fetchall():
            f.write(json.dumps({"type": "edge", **dict(r)}, ensure_ascii=False, default=str) + "\n")
    print(f"exported to {out_path}")
    return 0

def cmd_rebuild(args):
    """Convenience: delegate to graph_build.py."""
    import subprocess
    builder = Path(__file__).parent / "graph_build.py"
    return subprocess.call([sys.executable, str(builder)])

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("status"); s.set_defaults(fn=cmd_status)
    q = sub.add_parser("query"); q.add_argument("query"); q.add_argument("--kind")
    q.add_argument("--max-tokens", type=int, default=1500); q.set_defaults(fn=cmd_query)
    c = sub.add_parser("context-for-task"); c.add_argument("task_id")
    c.add_argument("--max-tokens", type=int, default=2000); c.set_defaults(fn=cmd_context_for_task)
    oq = sub.add_parser("open-questions"); oq.add_argument("--topic")
    oq.add_argument("--max-tokens", type=int, default=1000); oq.set_defaults(fn=cmd_open_questions)
    ro = sub.add_parser("record-outcome")
    ro.add_argument("--task-id", required=True)
    ro.add_argument("--status", required=True, choices=["passed", "blocked", "in_progress"])
    ro.add_argument("--files", default="")
    ro.add_argument("--gates", default="")
    ro.set_defaults(fn=cmd_record_outcome)
    e = sub.add_parser("export-graphify"); e.add_argument("--out"); e.set_defaults(fn=cmd_export_graphify)
    rb = sub.add_parser("rebuild"); rb.set_defaults(fn=cmd_rebuild)
    args = ap.parse_args()
    sys.exit(args.fn(args))

if __name__ == "__main__":
    main()
