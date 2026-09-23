#!/usr/bin/env python3
"""Blind A/B staging, verdicts, and receipts for the Gauntlet Loop.

The builder must never grade itself, and a critic that knows which side is the
reference is not blind. This script is the mechanism that makes both true:

  stage   copy candidate + reference into A/ and B/ under a random assignment,
          write the mapping OUTSIDE the trial dir (hook-denied), sha256 every
          staged file into the ledger
  verdict record the critic's blind pick; refuse to overwrite an existing one
  reveal  resolve the pick against the sealed mapping, append WIN/LOSS/TIE
  ledger  print the receipt trail

Run `stage` and `reveal` as the lead. Run `verdict` as the critic.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import shutil
import sys
import time
from pathlib import Path

ROOT_ENV = "GAUNTLET_ROOT"
REQUIRED_CHECKS = ["inspectable", "external", "held-out", "discriminating", "un-gameable"]


def root() -> Path:
    return Path(os.environ.get(ROOT_ENV, ".gauntlet")).resolve()


def die(msg: str, code: int = 1):
    print(f"gauntlet: {msg}", file=sys.stderr)
    sys.exit(code)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def append_ledger(event: dict):
    led = root() / "ledger.jsonl"
    led.parent.mkdir(parents=True, exist_ok=True)
    event = {"ts": time.time(), **event}
    with led.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(event, sort_keys=True) + "\n")


def require_sound_bar() -> str:
    """The loop does not start without a bar that passed all five checks."""
    bar = root() / "bar.md"
    if not bar.is_file():
        die(
            "no bar. `.gauntlet/bar.md` is missing — run /gauntlet:bar first.\n"
            "A Gauntlet Loop without a concrete external bar is just an agent "
            "grading its own homework."
        )
    text = bar.read_text(encoding="utf-8")
    low = text.lower()
    missing = [c for c in REQUIRED_CHECKS if f"- {c}: pass" not in low]
    if missing:
        die(
            "bar has not cleared the soundness gate. Missing PASS for: "
            + ", ".join(missing)
            + "\nEach check must appear in .gauntlet/bar.md as a line "
            '`- <check>: PASS — <evidence>`.'
        )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def copy_into(dest: Path, paths: list[str]) -> list[dict]:
    """Copy artifacts into a side directory, recording a receipt for each file."""
    dest.mkdir(parents=True, exist_ok=True)
    receipts = []
    for p in paths:
        src = Path(p)
        if not src.exists():
            die(f"artifact not found: {src}")
        if src.is_dir():
            target = dest / src.name
            shutil.copytree(src, target, dirs_exist_ok=True)
            for f in sorted(target.rglob("*")):
                if f.is_file():
                    receipts.append({"path": str(f.relative_to(dest)), "sha256": sha256(f)})
        else:
            target = dest / src.name
            shutil.copy2(src, target)
            receipts.append({"path": str(target.relative_to(dest)), "sha256": sha256(target)})
    if not receipts:
        die(f"nothing staged into {dest} — empty artifact set")
    return receipts


BRIEF = """# Blind comparison brief

You are judging two artifacts. One of them is the reference bar. One of them is our work.
**You are not told which is which, and you must not try to find out.**

- Trial: `{trial}`
- Piece: `{piece}`
- Round: {round}

## Goal

{goal}

## The bar

{bar}

## What to do

1. Inspect `A/` and `B/` directly — open the files, run them, render them, measure them.
   Judge the actual artifact. Never judge a summary or a description of one.
2. Decide which is better *against the goal and the bar above*. Not which is more impressive,
   more complex, or more effortful. Better.
3. Name the single largest meaningful gap between the loser and the winner — concrete and
   actionable enough that someone could close it without asking you a follow-up question.
4. Record it:

```
python3 {ab} verdict {trial} --winner A|B --gap "<the biggest gap, specific>"
```

   Use `--tie` instead of `--winner` only when you genuinely cannot separate them.

Do not read anything outside this directory. Do not look for who produced which side.
Ties and near-ties are losses for whichever side is ours, so do not hedge to be kind.
"""


def cmd_stage(args):
    bar_sha = require_sound_bar()
    r = root()
    seed = args.seed if args.seed is not None else random.SystemRandom().randrange(2**31)
    rng = random.Random(seed)
    trial = args.trial or f"{args.piece}-r{args.round}-{rng.randrange(16**6):06x}"

    trial_dir = r / "ab" / trial
    if trial_dir.exists():
        die(f"trial already staged: {trial}")
    key_path = r / "keys" / f"{trial}.json"
    key_path.parent.mkdir(parents=True, exist_ok=True)

    cand_side = "A" if rng.random() < 0.5 else "B"
    ref_side = "B" if cand_side == "A" else "A"

    cand_receipts = copy_into(trial_dir / cand_side, args.cand)
    ref_receipts = copy_into(trial_dir / ref_side, args.ref)

    # Filenames leak. `A/ours.png` next to `B/cod_reference.png` tells the critic
    # exactly which side is ours and the blind comparison is over before it starts.
    cand_names = sorted(x["path"] for x in cand_receipts)
    ref_names = sorted(x["path"] for x in ref_receipts)
    if cand_names != ref_names and not args.allow_name_mismatch:
        shutil.rmtree(trial_dir, ignore_errors=True)
        die(
            "staged filenames differ between the two sides, which tells the critic "
            "which one is ours:\n"
            f"  candidate: {cand_names}\n"
            f"  reference: {ref_names}\n"
            "Rename the inputs so both sides present identical paths (e.g. both "
            "`artifact.png`), or pass --allow-name-mismatch if the names genuinely "
            "carry no signal."
        )

    goal = Path(args.goal_file).read_text(encoding="utf-8").strip() if args.goal_file else args.goal
    bar = Path(args.bar_file).read_text(encoding="utf-8").strip() if args.bar_file else (r / "bar.md").read_text(encoding="utf-8").strip()
    if not goal:
        die("--goal or --goal-file is required")

    (trial_dir / "brief.md").write_text(
        BRIEF.format(
            trial=trial, piece=args.piece, round=args.round, goal=goal, bar=bar,
            ab=Path(__file__).resolve(),
        ),
        encoding="utf-8",
    )

    key = {
        "trial": trial,
        "candidate_side": cand_side,
        "reference_side": ref_side,
        "seed": seed,
        "bar_sha256": bar_sha,
    }
    key_path.write_text(json.dumps(key, sort_keys=True), encoding="utf-8")
    os.chmod(key_path, 0o600)

    append_ledger({
        "event": "staged",
        "trial": trial,
        "piece": args.piece,
        "round": args.round,
        "bar_sha256": bar_sha,
        "candidate_files": cand_receipts,
        "reference_files": ref_receipts,
    })

    print(f"trial: {trial}")
    print(f"brief: {trial_dir / 'brief.md'}")
    print(f"dir:   {trial_dir}")
    print("\nDispatch a FRESH gauntlet:critic with only the path above. Do not tell it")
    print("which side is ours, do not pass builder notes, and do not summarise the work.")


def cmd_verdict(args):
    trial_dir = root() / "ab" / args.trial
    if not trial_dir.is_dir():
        die(f"no such trial: {args.trial}")
    vpath = trial_dir / "verdict.json"
    if vpath.exists():
        die(
            f"verdict already recorded for {args.trial}. A trial is judged once.\n"
            "If the artifact changed, stage a new round."
        )
    if not args.tie and args.winner not in ("A", "B"):
        die("--winner must be A or B (or pass --tie)")
    if not args.gap or not args.gap.strip():
        die("--gap is required: name the largest remaining gap, specifically")

    verdict = {
        "trial": args.trial,
        "winner": None if args.tie else args.winner,
        "tie": bool(args.tie),
        "gap": args.gap.strip(),
        "notes": Path(args.notes_file).read_text(encoding="utf-8") if args.notes_file else None,
    }
    vpath.write_text(json.dumps(verdict, indent=2, sort_keys=True), encoding="utf-8")
    append_ledger({"event": "verdict", "trial": args.trial, **{k: verdict[k] for k in ("winner", "tie", "gap")}})
    print(f"recorded: {args.trial} -> {'TIE' if args.tie else args.winner}")
    print("Stop here. Revealing which side was ours is the lead's job, not yours.")


def cmd_reveal(args):
    r = root()
    vpath = r / "ab" / args.trial / "verdict.json"
    kpath = r / "keys" / f"{args.trial}.json"
    if not vpath.is_file():
        die(f"no verdict yet for {args.trial} — the critic has not judged it")
    if not kpath.is_file():
        die(f"no key for {args.trial}")
    verdict = json.loads(vpath.read_text(encoding="utf-8"))
    key = json.loads(kpath.read_text(encoding="utf-8"))

    if verdict["tie"]:
        outcome = "TIE"
    elif verdict["winner"] == key["candidate_side"]:
        outcome = "WIN"
    else:
        outcome = "LOSS"

    append_ledger({
        "event": "resolved",
        "trial": args.trial,
        "outcome": outcome,
        "candidate_side": key["candidate_side"],
        "gap": verdict["gap"],
    })
    print(f"{args.trial}: {outcome}  (ours was {key['candidate_side']})")
    print(f"gap: {verdict['gap']}")
    if outcome != "WIN":
        print("\nThe bar still wins. Send the gap back to this piece's builder and run another round.")


def cmd_ledger(args):
    led = root() / "ledger.jsonl"
    if not led.is_file():
        die("no ledger yet")
    rows = [json.loads(l) for l in led.read_text(encoding="utf-8").splitlines() if l.strip()]
    if args.json:
        print(json.dumps(rows, indent=2))
        return
    resolved = [r for r in rows if r.get("event") == "resolved"]
    staged = {r["trial"]: r for r in rows if r.get("event") == "staged"}
    for r in resolved:
        s = staged.get(r["trial"], {})
        print(f"{r['outcome']:5} {s.get('piece','?'):24} r{s.get('round','?'):<3} {r['gap'][:80]}")
    wins = sum(1 for r in resolved if r["outcome"] == "WIN")
    print(f"\n{len(resolved)} resolved trials — {wins} win, {len(resolved)-wins} still short of the bar")
    pending = [t for t in staged if not any(r["trial"] == t for r in resolved)]
    if pending:
        print(f"{len(pending)} staged, awaiting verdict: {', '.join(sorted(pending))}")


def main():
    ap = argparse.ArgumentParser(prog="ab.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("stage", help="stage a blind A/B trial (lead)")
    s.add_argument("--piece", required=True)
    s.add_argument("--round", type=int, required=True)
    s.add_argument("--cand", action="append", required=True, help="our artifact (file or dir); repeatable")
    s.add_argument("--ref", action="append", required=True, help="reference artifact (file or dir); repeatable")
    s.add_argument("--goal")
    s.add_argument("--goal-file")
    s.add_argument("--bar-file", help="defaults to .gauntlet/bar.md")
    s.add_argument("--trial", help="explicit trial id")
    s.add_argument("--seed", type=int)
    s.add_argument("--allow-name-mismatch", action="store_true",
                   help="stage even when the two sides' filenames differ (they can leak which side is ours)")
    s.set_defaults(func=cmd_stage)

    v = sub.add_parser("verdict", help="record a blind verdict (critic)")
    v.add_argument("trial")
    v.add_argument("--winner", choices=["A", "B"])
    v.add_argument("--tie", action="store_true")
    v.add_argument("--gap", required=True)
    v.add_argument("--notes-file")
    v.set_defaults(func=cmd_verdict)

    rv = sub.add_parser("reveal", help="resolve a verdict against the sealed mapping (lead)")
    rv.add_argument("trial")
    rv.set_defaults(func=cmd_reveal)

    lg = sub.add_parser("ledger", help="print the receipt trail")
    lg.add_argument("--json", action="store_true")
    lg.set_defaults(func=cmd_ledger)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
