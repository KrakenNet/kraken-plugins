---
description: Create and configure multi-step workflows with stages, steps, routing rules, and execution verification
argument-hint: [create|list|execute <id>] [--nickname=<text>]
allowed-tools: [Bash, Read, AskUserQuestion, Task]
---

# Railyard Workflow Management

Create multi-step workflows with conditional branching, tool/agent calls, and human approvals.

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-railyard/SKILL.md` for API conventions and auth flow.

## Verify Auth

Ensure valid JWT token. If not: "Run /railyard:auth first."

## Parse Arguments

From `$ARGUMENTS`:
- **Action**: `create` (default), `list`, `execute <id>`
- Workflow ID for execute action
- **`--nickname=<text>`** (optional) — when set on an execution-creating action, include `"execution_name": "<nickname>"` in the POST body so the run is easier to identify in lists/traces.

## Route by Action

### List

```bash
curl -s "${RAILYARD_URL}/api/v1/workflows?limit=50" \
  -H "Authorization: Bearer ${TOKEN}" | jq '.data[] | {id, name, is_active}'
```

### Execute

```bash
# With optional --nickname=<text>, add execution_name to identify the run
curl -s -X POST "${RAILYARD_URL}/api/v1/workflows/${WORKFLOW_ID}/execute" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"trigger_type":"manual","trigger_data":{},"execution_name":"nightly-smoke"}'
```

#### Steps & Trace — Cursor Pagination (preferred)

`/api/v1/executions/{id}/steps` and `/api/v1/executions/{id}/trace` clamp `limit` at 200 and return a cursor in `meta.next_cursor`. Loop until empty:

```bash
# Cursor pagination — preferred for >200 rows
curl -s "${RAILYARD_URL}/api/v1/executions/<id>/steps?cursor=<token>&limit=200" \
  -H "Authorization: Bearer ${TOKEN}"
```

Loop pattern:

```bash
URL="${RAILYARD_URL}/api/v1/executions/${EXEC_ID}/steps?limit=200"
while [ -n "$URL" ]; do
  RESP=$(curl -s "$URL" -H "Authorization: Bearer ${TOKEN}")
  echo "$RESP" | jq '.data[]'
  NEXT=$(echo "$RESP" | jq -r '.meta.next_cursor // empty')
  [ -z "$NEXT" ] && break
  URL="${RAILYARD_URL}/api/v1/executions/${EXEC_ID}/steps?limit=200&cursor=${NEXT}"
done
```

Same pattern for `/trace`. `?offset=&limit=` remains a documented fallback when no cursor is returned.

## Live Tail

For long executions, attach to the live event stream:

WS endpoint: `${RAILYARD_URL}/api/v1/ws/v1/executions/<exec_id>/events`

Query params:
- `since=<seq>` — replay from a specific event sequence using ExecutionHub buffer (last 1000 events).

Tooling: see `smart-railyard` § "WS Streaming Helpers".

### Create (default)

Interview:

1. **"What should this workflow be called?"** (name)

2. **"What does this workflow accomplish?"** (description — helps agent understand step design)

3. **Stage/step design** (iterative):
   For each stage:
   - "What's the name of this stage?"
   - "Should it run in parallel with other stages?" (yes/no)
   - "Does it require human approval?" (yes/no)

   For each step within the stage:
   - "What should this step do?"
   - "Step type?"
     - agent_call — Call an agent (list existing or describe new)
     - tool_call — Call a tool (list existing or describe new)
     - governor_check — Run policy check (list existing or describe new)
     - human_approval — Pause for human review
   - "Any conditions for when this step runs?" (expression or skip)
   - "What happens if this step fails?" (stop / skip to step / retry / escalate)
   - "Add another step to this stage?" (yes/no)

   After each stage: "Add another stage?" (yes/no)

4. **Input/output mapping** (for multi-step data flow):
   - "How should data flow between steps?" (agent helps wire mappings)

5. **Routing rules** (optional):
   - "Should events auto-trigger this workflow?"
   - If yes: attribute, operator, value, priority

6. **"Provide sample trigger data for test execution?"** (recommended)

## Delegate

Delegate to `workflow-builder` agent via Task tool with all interview answers + TOKEN + RAILYARD_URL.

## Report

Show the agent's output to the user.
