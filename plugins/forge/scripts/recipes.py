#!/usr/bin/env python3
"""
Failure recipe DB. Append-only JSONL.
File: .forge/recipes.jsonl

Each line is one recipe:
{
  "category": "locked-test-wrong" | "lint-fail" | "anti-cheat-block" | "test-fail" |
              "adversarial-fail" | "missing-context" | "env" | "external-flaky" | "other",
  "symptom": "short matchable string (gate output / error message / pattern)",
  "resolution": "what worked",
  "task_id": "auth-middleware",
  "files": ["src/auth/middleware.ts"],
  "occurred_at": "2026-05-14T...",
  "resolved_at": "2026-05-14T..."   or null if unresolved
}

CLI:
  recipes.py add --category X --symptom "..." --resolution "..." [--task Y] [--files a,b]
  recipes.py lookup "<symptom-like string>" [--category X] [--max N] [--max-tokens 1000]
  recipes.py list [--category X] [--max N]
  recipes.py stats
"""
from __future__ import annotations
import argparse, datetime as dt, json, re, sys
from collections import Counter
from pathlib import Path
from difflib import SequenceMatcher

RECIPES = Path(".forge/recipes.jsonl")

def _read() -> list[dict]:
    if not RECIPES.exists():
        return []
    out = []
    for line in RECIPES.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out

def _append(rec: dict):
    RECIPES.parent.mkdir(parents=True, exist_ok=True)
    with RECIPES.open("a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")

def _tokenize(s: str) -> set[str]:
    return set(re.findall(r"[A-Za-z_][A-Za-z0-9_]+", s.lower()))

def _score(query: str, recipe: dict) -> float:
    """Hybrid: token Jaccard + sequence ratio. Cheap, no embeddings."""
    qt = _tokenize(query)
    rt = _tokenize(recipe.get("symptom", "") + " " + recipe.get("resolution", ""))
    if not qt or not rt:
        jacc = 0.0
    else:
        jacc = len(qt & rt) / len(qt | rt)
    seq = SequenceMatcher(None, query.lower(), recipe.get("symptom", "").lower()).ratio()
    return 0.6 * jacc + 0.4 * seq

def cmd_add(args):
    files = [f.strip() for f in (args.files or "").split(",") if f.strip()]
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    rec = {
        "category": args.category,
        "symptom": args.symptom,
        "resolution": args.resolution,
        "task_id": args.task,
        "files": files,
        "occurred_at": now,
        "resolved_at": now if args.resolution else None,
    }
    _append(rec)
    print(f"recipe added: {args.category}", file=sys.stderr)
    return 0

def cmd_lookup(args):
    recs = _read()
    if args.category:
        recs = [r for r in recs if r.get("category") == args.category]
    scored = sorted(((_score(args.query, r), r) for r in recs), key=lambda x: x[0], reverse=True)
    scored = [(s, r) for s, r in scored if s > 0.1][: args.max]
    if not scored:
        return 0
    print("## Past recipes for similar failure")
    used = 0
    for s, r in scored:
        block = f"- [{r['category']}] symptom: {r['symptom']!r}\n  resolution: {r['resolution']}\n  (score {s:.2f}, task {r.get('task_id') or '?'}, files {r.get('files') or []})"
        cost = len(block) // 4
        if used + cost > args.max_tokens:
            break
        print(block)
        used += cost
    return 0

def cmd_list(args):
    recs = _read()
    if args.category:
        recs = [r for r in recs if r.get("category") == args.category]
    for r in recs[-args.max :]:
        print(json.dumps(r, ensure_ascii=False))
    return 0

def cmd_stats(args):
    recs = _read()
    if not recs:
        print("no recipes yet")
        return 0
    cats = Counter(r.get("category", "?") for r in recs)
    print(f"total: {len(recs)}")
    for c, n in cats.most_common():
        print(f"  {c}: {n}")
    return 0

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("--category", required=True)
    a.add_argument("--symptom", required=True)
    a.add_argument("--resolution", required=True)
    a.add_argument("--task", default=None)
    a.add_argument("--files", default="")
    a.set_defaults(fn=cmd_add)
    l = sub.add_parser("lookup")
    l.add_argument("query")
    l.add_argument("--category")
    l.add_argument("--max", type=int, default=5)
    l.add_argument("--max-tokens", type=int, default=1000)
    l.set_defaults(fn=cmd_lookup)
    ll = sub.add_parser("list"); ll.add_argument("--category"); ll.add_argument("--max", type=int, default=20); ll.set_defaults(fn=cmd_list)
    s = sub.add_parser("stats"); s.set_defaults(fn=cmd_stats)
    args = ap.parse_args()
    sys.exit(args.fn(args))

if __name__ == "__main__":
    main()
