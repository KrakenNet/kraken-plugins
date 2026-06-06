---
description: List checkpoints for a Stargraph run with state + facts diff
argument-hint: <run_id>
allowed-tools: [Bash, Read]
---

# Stargraph Checkpoints

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-stargraph/SKILL.md`.

## Run

```bash
curl -s "${STARGRAPH_URL}/v1/runs/<run_id>/checkpoints" -H "Authorization: Bearer ${STARGRAPH_TOKEN}" | jq '.data[] | {id, node, state_diff_summary, fact_count}'
```

## Report

Table of checkpoints with timestamps + state-diff summary.
