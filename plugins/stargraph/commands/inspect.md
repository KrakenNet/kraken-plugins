---
description: Inspect a Stargraph run — timeline, state at step, CLIPS fact diff
argument-hint: <run_id> --db <path> [--step <n>] [--diff <n> <m>]
allowed-tools: [Bash, Read]
---

# Stargraph Inspect

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-stargraph/SKILL.md`.

## Run

`stargraph inspect` is a read-only inspector over a SQLite checkpointer DB
(default `./.stargraph/run.sqlite`). The mode selector is `--diff` > `--step`
> timeline; both `--diff` and `--step` require `--db`.

```bash
RID="$1"
DB="${DB:-./.stargraph/run.sqlite}"

# Timeline view — per-step node lifecycle, enriched with the audit log
uv run stargraph inspect "${RID}" --db "${DB}" --log-file ./.stargraph/run.jsonl

# State-at-step view — IR-canonical state dict at step N (if --step)
if [[ "$*" == *--step* ]]; then
  uv run stargraph inspect "${RID}" --db "${DB}" --step "${STEP}"
fi

# Fact-diff view — CLIPS facts asserted/retracted between step N and M (if --diff)
if [[ "$*" == *--diff* ]]; then
  uv run stargraph inspect "${RID}" --db "${DB}" --diff "${N}" "${M}"
fi
```

Without `--db`, passing only `--log-file PATH` streams raw JSONL events
(legacy mode); an empty filter result there exits non-zero (force-loud).

## Report

- From the timeline: status, graph_hash (full + short), total steps
- Node-by-node table: step → node → outcome → key state changes (`--step` per step)
- Fact delta from `--diff N M`: CLIPS facts added/removed, with their `origin`/`source`
- Provenance breakdown: counts by documented `origin` (`tool`/`llm`/`rule`/`system`)
- If terminal status is `failed`: the halt/error rule + offending facts
