---
description: Create and manage chat sessions with agents and workflows, send messages, and monitor conversations
argument-hint: [create|list|send|history] [--agent <id>] [--workflow <id>]
allowed-tools: [Bash, Read, AskUserQuestion, Task]
---

# Railyard Chat Management

Create chat sessions connected to agents or workflows, send messages, and view conversation history.

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-railyard/SKILL.md` for API conventions and auth flow.

## Verify Auth

Ensure valid JWT token. If not: "Run /railyard:auth first."

## Parse Arguments

From `$ARGUMENTS`:
- **Action**: `create` (default), `list`, `send`, `history`
- **--agent**: Pre-select agent ID for session
- **--workflow**: Pre-select workflow execution ID for session

## Route by Action

### List

```bash
curl -s "${RAILYARD_URL}/api/v1/chat/sessions" \
  -H "Authorization: Bearer ${TOKEN}" | jq '.data[] | {id, title, status, agent_id, created_at, last_message_at}'
```

### Create (default)

Interview:

1. **"What should this chat session be called?"** (title, optional)

2. **"Connect to an agent or workflow?"**
   - agent — Chat with a specific agent
   - workflow — Monitor/interact with a workflow execution
   - neither — Standalone session

3. If agent: List existing agents `GET /api/v1/agents?limit=50` and ask **"Which agent?"**
   If workflow: Ask **"Workflow execution ID?"**

Delegate to `chat-manager` agent via Task tool with interview answers + TOKEN + RAILYARD_URL.

### Send

Interview:

1. List active sessions: `GET /api/v1/chat/sessions`
2. **"Which session?"** (session_id)
3. **"Message:"** (content)

Execute directly:
```bash
curl -s -X POST "${RAILYARD_URL}/api/v1/chat/sessions/${SESSION_ID}/messages" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"role":"user","content":"..."}'
```

### History

Interview:

1. List active sessions: `GET /api/v1/chat/sessions`
2. **"Which session?"** (session_id)

Execute directly:
```bash
curl -s "${RAILYARD_URL}/api/v1/chat/sessions/${SESSION_ID}/messages?limit=50" \
  -H "Authorization: Bearer ${TOKEN}" | jq '.data[] | {role, content, sequence, created_at}'
```

## Report

Show the output to the user.
