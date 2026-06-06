---
description: Counterfactual replay of a Stargraph run from any checkpoint
argument-hint: <run_id> [--from <checkpoint>] [--patch <json>]
allowed-tools: [Bash, Read, AskUserQuestion]
---

# Stargraph Replay

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-stargraph/SKILL.md`.

## Verify Server

Standard. Confirm graph_hash of the run matches current graph; warn on mismatch.

## Run

```bash
curl -s -X POST "${STARGRAPH_URL}/v1/runs/<run_id>/replay" \
  -H "Authorization: Bearer ${STARGRAPH_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"from_checkpoint":"<cp>","patch": <json>}'
```

## Report

new run_id, divergence point, comparison summary vs original.
