---
description: Manage Railyard agent skills — register, list, get, update, delete entries in /api/v1/skills
argument-hint: [list|get|register|update|delete] [id?]
allowed-tools: [Bash, Read, AskUserQuestion, Task]
---

# Railyard Skills

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-railyard/SKILL.md`.

## Verify Auth

Standard.

## Parse Arguments

- **Action** (default `list`): list, get, register, update, delete.
- **ID** required for get/update/delete.

## Endpoint

`/api/v1/skills`

## Routes

### list

```bash
curl -s "${RAILYARD_URL}/api/v1/skills?limit=50" -H "Authorization: Bearer ${TOKEN}" | jq '.data[] | {id, name, namespace, version}'
```

### get/register/update/delete

Standard CRUD pattern (see `commands/agent.md` for canonical shape). Register prompts for: name, namespace, version, description, capabilities (list), entry_point.

## Delegate

For non-trivial flows, delegate to a fresh Task agent (no dedicated builder; the routing is small).

## Report

JSON or table.
