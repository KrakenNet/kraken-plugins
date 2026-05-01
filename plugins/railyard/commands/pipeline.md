---
description: Manage Railyard tool-execution pipelines via /api/v1/pipelines
argument-hint: [list|get|create|update|delete|run] [id?]
allowed-tools: [Bash, Read, AskUserQuestion, Task]
---

# Railyard Pipelines

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-railyard/SKILL.md`.

## Verify Auth

Standard.

## Endpoint

`/api/v1/pipelines`

## Routes

### list / get / delete — standard CRUD.

### create

Interview:
- name
- description
- steps (ordered list of {tool_id, args_template})
- error_policy (fail-fast | continue | retry-with-backoff)

### update

PUT with the full body.

### run

```bash
curl -s -X POST "${RAILYARD_URL}/api/v1/pipelines/<id>/run" -H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json" -d '{"input": {...}}'
```

## Report

Pipeline definition + last run status.
