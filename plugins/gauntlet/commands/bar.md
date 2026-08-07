---
description: Find and validate the quality bar for the current Gauntlet Loop. Dispatches bar-scout, runs the five soundness checks, writes .gauntlet/bar.md. The loop cannot stage a trial until this passes.
argument-hint: [--ref <path-or-url>...] [--recheck]
allowed-tools: [Bash, Read, Write, Edit, Glob, Grep, Agent, WebSearch, WebFetch, AskUserQuestion]
---

# /gauntlet:bar

The bar is the load-bearing part of the method. Read
`${CLAUDE_PLUGIN_ROOT}/skills/gauntlet-loop/SKILL.md` and the domain recipe named in
`.gauntlet/charter.md`.

## Preconditions

`.gauntlet/charter.md` must exist. If not, run `/gauntlet:new` first.

## Dispatch the scout

```
Agent({
  subagent_type: "gauntlet:bar-scout",
  prompt: "Goal + domain from .gauntlet/charter.md. User-supplied references: <--ref values, if any>.
           Read the matching domain recipe. Propose 3-4 candidate bars, pick the harshest inspectable
           one, run the five soundness checks with evidence, name the cheapest cheat and its
           counter-check, write .gauntlet/bar.md. Report FAILs honestly — do not write PASS to unblock."
})
```

With `--recheck`, re-run the checks against the existing `.gauntlet/bar.md` instead — use this when
every piece has been winning for several waves, which usually means the bar went soft.

## Gate

`ab.py` parses `.gauntlet/bar.md` and refuses to stage a trial unless all five checks read
`- <check>: PASS`. Verify it clears:

```bash
python3 -c "
import sys,re
t=open('.gauntlet/bar.md').read().lower()
m=[c for c in ['inspectable','external','held-out','discriminating','un-gameable'] if f'- {c}: pass' not in t]
print('BAR NOT SOUND — missing PASS: '+', '.join(m) if m else 'BAR SOUND — loop can start')
sys.exit(1 if m else 0)"
```

If a check fails, **do not soften it**. Surface which one failed and why, and either find a different
candidate or tell the user what would have to be true for this one to hold. A bar that fails
`held-out` or `un-gameable` will produce a run that looks like it is improving and is not.

The `discriminating` check is the one to verify by hand: our current output must actually lose to the
bar today. If it already wins, the bar is decoration.

## Then

Show the user the bar, the five verdicts, and the rejected candidates. Run `/gauntlet:run`.
