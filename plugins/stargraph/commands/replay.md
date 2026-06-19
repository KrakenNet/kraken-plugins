---
description: Counterfactual replay of a Stargraph run from any checkpoint
argument-hint: <run_id> --db <path> [--from-step <n>] [--mutation <json>]
allowed-tools: [Bash, Read, AskUserQuestion]
---

# Stargraph Replay

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-stargraph/SKILL.md`.

## Run

Fork a counterfactual run from a checkpoint in the parent run's SQLite DB. With
no `--mutation`, an empty no-op mutation is used (still produces a cf-derived
`graph_hash`). The cf-run id is minted as `cf-<uuid>`; the parent's checkpoint
rows stay byte-identical post-fork.

```bash
uv run stargraph replay "<run_id>" \
  --db ./.stargraph/run.sqlite \
  --mutation cf/override.json \
  --from-step "${FROM_STEP:-0}" \
  --diff
```

`--mutation FILE.json` loads a `CounterfactualMutation` (state overrides, fact
asserts/retracts, etc.). `--diff` renders the parent-vs-cf `RunDiff` as
canonical IR JSON after forking (omit, or pass `--no-diff`, to print just the
cf-run id).

## Report

new cf-run id (`cf-<uuid>`), fork step, and the parent-vs-cf `RunDiff` summary.
