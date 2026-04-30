---
description: POST /v1/evaluate to a running Fathom engine with facts; show decision, reason, and attestation
argument-hint: [--facts-file <path>] [--ruleset <name>]
allowed-tools: [Bash, Read, Write, AskUserQuestion, Task]
---

# Fathom Evaluate

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-fathom/SKILL.md`.

## Verify Engine

```bash
curl -s "${FATHOM_URL:-http://localhost:8080}/info" -H "Authorization: Bearer ${FATHOM_TOKEN}" | jq '.'
```

Confirm version + ruleset_hash.

## Parse Arguments

- `--facts-file <path>` — JSON with `facts: [...]`. If absent, prompt for inline facts.
- `--ruleset <name>` — optional ruleset selector.

## Delegate

Task tool → `evaluator` agent with the request body.

## Report

Decision + reason + duration_us + attestation token (truncated) + audit_id.
