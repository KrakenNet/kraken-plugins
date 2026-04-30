---
description: Manage routing rules, requests, and request types via /api/v1/{routing-rules,requests,request-types}
argument-hint: [rules|requests|types] [list|get|create|update|delete|test] [id?]
allowed-tools: [Bash, Read, AskUserQuestion]
---

# Railyard Routing Rules and Requests

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-railyard/SKILL.md`.

## Verify Auth

Standard.

## Resources

- `/api/v1/routing-rules` — rules that match an incoming request to an agent/workflow.
- `/api/v1/requests` — request log + replay.
- `/api/v1/request-types` — request schema registry.

## Routes

### rules list/get/create/update/delete — standard CRUD. `create` interview: name, match (CLIPS pattern), target (agent_id|workflow_id), priority.

### rules test

```bash
curl -s -X POST "${RAILYARD_URL}/api/v1/routing-rules/test" -H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json" -d '{"facts":[...]}' | jq '.data'
```

### requests list/get — standard. `get` includes the request payload + matched rule + outcome.

### types list/get/create — standard CRUD.

## Report

Table of rules with priority + match summary.
