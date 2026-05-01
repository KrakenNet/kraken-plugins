---
description: Counterfactual replay of a Harbor run from any checkpoint
argument-hint: <run_id> [--from <checkpoint>] [--patch <json>]
allowed-tools: [Bash, Read, AskUserQuestion]
---

# Harbor Replay

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-harbor/SKILL.md`.

## Verify Server

Standard. Confirm graph_hash of the run matches current graph; warn on mismatch.

## Run

```bash
curl -s -X POST "${HARBOR_URL}/v1/runs/<run_id>/replay" \
  -H "Authorization: Bearer ${HARBOR_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"from_checkpoint":"<cp>","patch": <json>}'
```

## Report

new run_id, divergence point, comparison summary vs original.
