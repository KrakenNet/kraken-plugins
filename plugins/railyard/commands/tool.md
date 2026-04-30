---
description: Create and configure tools for Railyard agents (Python, Shell, API, DSPy implementations)
argument-hint: [create|list] [--method python|shell|api|dspy]
allowed-tools: [Bash, Read, AskUserQuestion, Task]
---

# Railyard Tool Management

Create and test tools that agents can invoke during execution.

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-railyard/SKILL.md` for API conventions and auth flow.

## Verify Auth

Ensure valid JWT token. If not: "Run /railyard:auth first."

## Parse Arguments

From `$ARGUMENTS`:
- **Action**: `create` (default), `list`
- **--method**: Pre-select implementation method

## Route by Action

### List

```bash
curl -s "${RAILYARD_URL}/api/v1/tools?limit=50" \
  -H "Authorization: Bearer ${TOKEN}" | jq '.data[] | {id, name, implementation_method, category, is_active}'
```

### Create (default)

Interview:

1. **"What should this tool be called?"** (name)

2. **"What does this tool do?"** (description)

3. **"Implementation method?"**
   - python — Python script (runs as subprocess)
   - shell — Shell script
   - api — External HTTP API call
   - dspy — DSPy module invocation

4. **Per-method questions:**

   **python:**
   - "Describe what the Python code should do, or paste existing code"
   - Agent generates or uses provided Python code as `content`
   - "What are the input fields?" → generates input_schema
   - "What are the output fields?" → generates output_schema

   **shell:**
   - "Describe the shell command or paste existing script"
   - Agent generates or uses provided shell code as `content`
   - Input/output schema questions

   **api:**
   - "What is the API endpoint URL?"
   - "HTTP method?" (GET/POST/PUT/DELETE)
   - "Does this API need a credential?" → if yes, invoke credential access helper from smart-railyard skill
   - Input/output schema questions

   **dspy:**
   - "Which DSPy module config?"
   - Input/output schema questions

5. **"Category?"** (optional — e.g., validation, analysis, orchestration)

6. **"Provide sample test input?"** (for build-test-fix verification)

## Delegate

Delegate to `tool-builder` agent via Task tool with all interview answers + TOKEN + RAILYARD_URL.

## Report

Show the agent's output to the user.
