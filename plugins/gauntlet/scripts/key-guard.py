#!/usr/bin/env python3
"""PreToolUse guard: keep the A/B mapping unreadable while a trial is being judged.

`ab.py stage` writes which side is ours to `.gauntlet/keys/<trial>.json`. If any
agent can read that file, the critic is no longer blind and the whole loop
degrades into the builder grading itself with extra steps.

This hook denies any tool call whose input references that directory. `ab.py`
reads the key in-process during `reveal`, which no hook intercepts, so the lead
can still resolve trials.

Exit 0 = allow, exit 2 = deny (stderr is shown to the model).
"""
import json
import sys

GUARDED = ".gauntlet/keys"


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0  # never break the session on a malformed event

    blob = json.dumps(payload.get("tool_input", {}))
    if GUARDED not in blob and "gauntlet/keys" not in blob:
        return 0

    print(
        "BLOCKED by gauntlet: .gauntlet/keys/ holds the sealed A/B mapping for "
        "in-flight trials. Reading it would tell you which side is ours and make "
        "the critic's judgment worthless.\n"
        "To resolve a trial, run `ab.py reveal <trial>` — it reads the key itself "
        "and appends the outcome to the ledger.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
