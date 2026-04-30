---
description: List checkpoints for a Harbor run with state + facts diff
argument-hint: <run_id>
allowed-tools: [Bash, Read]
---

# Harbor Checkpoints

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-harbor/SKILL.md`.

## Run

```bash
curl -s "${HARBOR_URL}/v1/runs/<run_id>/checkpoints" -H "Authorization: Bearer ${HARBOR_TOKEN}" | jq '.data[] | {id, node, state_diff_summary, fact_count}'
```

## Report

Table of checkpoints with timestamps + state-diff summary.
