---
description: Manage Railyard chatbot flows — list, get, create (full or quick-create), update, delete via /api/v1/chatbots
argument-hint: [list|get|create|quick-create|update|delete] [id?]
allowed-tools: [Bash, Read, AskUserQuestion, Task]
---

# Railyard Chatbots

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-railyard/SKILL.md`.

## Verify Auth

Standard.

## Endpoints

- `/api/v1/chatbots`
- `/api/v1/chatbots/quick-create` — single-call POST that scaffolds agent + workflow + chat session.

## Routes

### list / get / update / delete — standard CRUD.

### create

Interview: name, description, agent_id (or `--new-agent`), workflow_id (or `--new-workflow`), greeting, persona.

### quick-create

```bash
curl -s -X POST "${RAILYARD_URL}/api/v1/chatbots/quick-create" -H "Authorization: Bearer ${TOKEN}" -H "Content-Type: application/json" -d '{"name":"...","description":"...","greeting":"..."}'
```

Render the trio (agent_id, workflow_id, session_id) it returns.

## Report

JSON envelope.
