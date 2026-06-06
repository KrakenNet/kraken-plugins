---
description: Inspect a Stargraph run — events, state diff per checkpoint, fact stream, graph hash
argument-hint: <run_id> [--events] [--facts] [--diff]
allowed-tools: [Bash, Read]
---

# Stargraph Inspect

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-stargraph/SKILL.md`.

## Verify Server

`GET ${STARGRAPH_URL}/health`.

## Run

```bash
RID="$1"

# Run header — status, graph_hash, started/finished, trigger
curl -fsS "${STARGRAPH_URL}/v1/runs/${RID}" \
  -H "Authorization: Bearer ${STARGRAPH_TOKEN}" | \
  jq '{run_id, status, graph_hash, started_at, finished_at, trigger}'

# Checkpoints — node, step, state diff summary
curl -fsS "${STARGRAPH_URL}/v1/runs/${RID}/checkpoints" \
  -H "Authorization: Bearer ${STARGRAPH_TOKEN}" | \
  jq '.data[] | {step, node, next, fact_count, state_diff_summary}'

# Events — full timeline (if --events)
if [[ "$*" == *--events* ]]; then
  curl -fsS "${STARGRAPH_URL}/v1/runs/${RID}/events" \
    -H "Authorization: Bearer ${STARGRAPH_TOKEN}" | jq .
fi

# Facts at terminal step (if --facts)
if [[ "$*" == *--facts* ]]; then
  curl -fsS "${STARGRAPH_URL}/v1/runs/${RID}/facts" \
    -H "Authorization: Bearer ${STARGRAPH_TOKEN}" | \
    jq '.data[] | {template, slots, origin, source, confidence}'
fi
```

## Report

- Status, graph_hash (full + short), wall time, total steps, total facts
- Node-by-node table: step → node → outcome → key state changes
- Any `disagreement` facts (dual-truth divergences)
- Provenance breakdown: counts by `origin` (llm/tool/rule/model/external)
- If `status == FAILED` or `HALTED`: error/halt rule + offending facts
