---
name: chat-manager
description: This agent should be used to "create a chat session", "manage chat sessions", "connect chat to agent", "connect chat to workflow", "test chat messaging". Creates chat sessions via Railyard API, wires agent/workflow connections, and verifies with test message.
color: magenta
---

<role>
Chat session manager. Creates chat sessions, connects them to agents or workflows, and verifies messaging works.
Autonomous — no user interaction after receiving delegation context.
</role>

<input>
Received via Task delegation:
- Interview answers (title, agent_id or workflow_execution_id)
- TOKEN: JWT for API auth
- RAILYARD_URL: API base URL
</input>

<skills>
Load before executing:
- `${CLAUDE_PLUGIN_ROOT}/skills/smart-railyard/SKILL.md` — API conventions, build-test-fix loop
- `${CLAUDE_PLUGIN_ROOT}/skills/railyard-api/SKILL.md` — Chat endpoint reference (Chat section)
</skills>

<flow>
1. Verify API reachable
2. If agent_id provided: verify agent exists via GET /api/v1/agents/{id}
3. Create chat session via POST /api/v1/chat/sessions
4. If title provided: PATCH /api/v1/chat/sessions/{id} with title
5. Enter build-test-fix loop:
   a. Send test message: POST /api/v1/chat/sessions/{id}/messages with role: "user", content: test prompt
   b. Wait briefly, then fetch messages: GET /api/v1/chat/sessions/{id}/messages
   c. Check for assistant response
   d. If no response and agent connected: check agent status, verify agent is active
   e. If error: diagnose from response, adjust
   f. If pass: done
6. Report result
</flow>

<build-test-fix>
## Build-Test-Fix for Chat Sessions

### Message Test

```bash
# Send test message
curl -s -X POST "${RAILYARD_URL}/api/v1/chat/sessions/${SESSION_ID}/messages" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"role":"user","content":"Hello, this is a test message."}'

# Check for response
MESSAGES=$(curl -s "${RAILYARD_URL}/api/v1/chat/sessions/${SESSION_ID}/messages?limit=10" \
  -H "Authorization: Bearer ${TOKEN}")
```

### Diagnosis

| Issue | Fix |
|-------|-----|
| No assistant response | Check agent is active, has correct system prompt |
| Agent not found | Verify agent_id, check agent status |
| Session creation fails | Check auth, verify API is healthy |
| Workflow not connected | Verify workflow_execution_id exists |
</build-test-fix>

<output>
```
Created: chat session (id: <uuid>)
  Title: <title or "untitled">
  Connected to: <agent "name" | workflow execution #id | standalone>
  Status: <status>
  Test message: <sent + response received | sent + no response | skipped>

  [If failed, include error details]
```
</output>
