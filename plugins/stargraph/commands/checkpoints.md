---
description: Inspect a Stargraph run's checkpoints — timeline, state at step, CLIPS fact diff
argument-hint: <run_id> --db <path> [--step <n>] [--diff <n> <m>]
allowed-tools: [Bash, Read]
---

# Stargraph Checkpoints

There is no `checkpoints` subcommand or endpoint. Checkpoint, state, and fact
views come from `stargraph inspect` over the SQLite checkpointer DB (default
`./.stargraph/run.sqlite`).

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-stargraph/SKILL.md`.

## Run

```bash
RID="$1"
DB="${DB:-./.stargraph/run.sqlite}"

# Timeline — per-step checkpoint sequence for the run
uv run stargraph inspect "${RID}" --db "${DB}"

# State captured at a specific checkpoint step
uv run stargraph inspect "${RID}" --db "${DB}" --step "${STEP}"

# CLIPS fact delta between two checkpoint steps
uv run stargraph inspect "${RID}" --db "${DB}" --diff "${N}" "${M}"
```

## Report

Table of checkpoint steps from the timeline, with the state snapshot at a given
`--step` and the CLIPS fact delta (added/removed) from `--diff N M`.
