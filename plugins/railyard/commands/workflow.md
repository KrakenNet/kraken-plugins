---
description: Create and configure multi-step workflows with stages, steps, routing rules, and execution verification
argument-hint: [create|list|execute <id>]
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

## Route by Action

### List

```bash
curl -s "${RAILYARD_URL}/api/v1/workflows?limit=50" \
  -H "Authorization: Bearer ${TOKEN}" | jq '.data[] | {id, name, is_active}'
```

### Execute

```bash
curl -s -X POST "${RAILYARD_URL}/api/v1/workflows/${WORKFLOW_ID}/execute" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"trigger_type":"manual","trigger_data":{}}'
```

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
