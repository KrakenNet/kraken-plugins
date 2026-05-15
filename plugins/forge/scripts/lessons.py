#!/usr/bin/env python3
"""
Reflexion-style lessons store. Append-only markdown bullets.
File: .forge/lessons.md

Schema per line:
  - [tag1,tag2] lesson body — context where applies

CLI:
  lessons.py add "<tags>" "<lesson>"     append, dedup by exact-match
  lessons.py list [--tag X] [--max N]    print bullets, newest first, capped
  lessons.py prune [--keep N]            keep newest N (default 50)
  lessons.py context [--tags ...] [--max-tokens 800]
                                          return ~max-tokens of relevant bullets
                                          for injection into agent prompt
"""
from __future__ import annotations
import argparse, datetime as dt, sys, re
from pathlib import Path

LESSONS = Path(".forge/lessons.md")
HEADER = "# Forge Lessons\n\nAppend-only. Newest first. Prune via `forge-lessons prune`.\n\n"

def _read():
    if not LESSONS.exists():
        return []
    text = LESSONS.read_text()
    body = text.split("---\n", 1)[-1] if "---" in text else text
    return [l for l in body.splitlines() if l.startswith("- ")]

def _write(bullets):
    LESSONS.parent.mkdir(parents=True, exist_ok=True)
    LESSONS.write_text(HEADER + "---\n" + "\n".join(bullets) + "\n")

def _parse_tags(bullet: str) -> set[str]:
    m = re.match(r"- \[([^\]]+)\]", bullet)
    if not m:
        return set()
    return {t.strip() for t in m.group(1).split(",") if t.strip()}

def cmd_add(args):
    tags = ",".join(t.strip() for t in args.tags.split(",") if t.strip())
    lesson = args.lesson.strip()
    if not lesson:
        return 1
    today = dt.date.today().isoformat()
    new = f"- [{tags}] {lesson} ({today})"
    existing = _read()
    if any(new[: new.rfind(" (")] == b[: b.rfind(" (")] if " (" in b else False for b in existing):
        return 0
    _write([new] + existing)
    return 0

def cmd_list(args):
    for b in _read()[: args.max]:
        if args.tag and args.tag not in _parse_tags(b):
            continue
        print(b)
    return 0

def cmd_prune(args):
    bullets = _read()
    _write(bullets[: args.keep])
    print(f"pruned to {min(len(bullets), args.keep)} bullets", file=sys.stderr)
    return 0

def cmd_context(args):
    """Return bullets that match any requested tag, capped by token budget."""
    want = set(t.strip() for t in (args.tags or "").split(",") if t.strip())
    bullets = _read()
    selected = []
    used = 0
    for b in bullets:
        if want and not (_parse_tags(b) & want):
            continue
        cost = len(b) // 4
        if used + cost > args.max_tokens:
            break
        selected.append(b)
        used += cost
    if not selected:
        return 0
    print("## Lessons (from prior runs)")
    for b in selected:
        print(b)
    return 0

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add"); a.add_argument("tags"); a.add_argument("lesson"); a.set_defaults(fn=cmd_add)
    l = sub.add_parser("list"); l.add_argument("--tag"); l.add_argument("--max", type=int, default=50); l.set_defaults(fn=cmd_list)
    p = sub.add_parser("prune"); p.add_argument("--keep", type=int, default=50); p.set_defaults(fn=cmd_prune)
    c = sub.add_parser("context"); c.add_argument("--tags", default=""); c.add_argument("--max-tokens", type=int, default=800); c.set_defaults(fn=cmd_context)
    args = ap.parse_args()
    sys.exit(args.fn(args))

if __name__ == "__main__":
    main()
