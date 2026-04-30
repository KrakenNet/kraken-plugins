---
description: Create and configure DSPy agents with tool and governor associations, demonstrations, and execution verification
argument-hint: [create|list] [--module predict|chain_of_thought|react|multi_chain_comparison|refine|parallel|rlm]
allowed-tools: [Bash, Read, AskUserQuestion, Task]
---

# Railyard Agent Management

Create DSPy agents with tool/governor wiring and verified execution.

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-railyard/SKILL.md` for API conventions and auth flow.

## Verify Auth

Ensure valid JWT token. If not: "Run /railyard:auth first."

## Parse Arguments

From `$ARGUMENTS`:
- **Action**: `create` (default), `list`
- **--module**: Pre-select DSPy module type

## Route by Action

### List

```bash
curl -s "${RAILYARD_URL}/api/v1/agents?limit=50" \
  -H "Authorization: Bearer ${TOKEN}" | jq '.data[] | {id, name, status, dspy_module, tool_count, success_rate}'
```

### Create (default)

Interview:

1. **"What should this agent be called?"** (name)

2. **"What is this agent's purpose?"** (description — also informs system_prompt)

3. **"What reasoning approach should it use?"**
   - predict — Simple input→output (fastest, cheapest)
   - chain_of_thought — Step-by-step reasoning (good default)
   - react — Reasoning + tool use (for agents that call tools)
   - multi_chain_comparison — Generate multiple answers, pick best
   - refine — Iterative refinement
   - parallel — Run multiple approaches in parallel
   - rlm — Recursive Language Model (for large context processing)

4. **"Which LLM model?"** (optional — default uses platform default)

5. **"System prompt?"** — If user provides a description, help craft a system prompt. If they have one, use it directly.

6. **"Input/output format?"**
   - "What fields does this agent receive?" → generate input_schema
   - "What fields should it return?" → generate output_schema

7. **"Should this agent use any tools?"**
   - List existing tools: `GET /api/v1/tools?limit=50`
   - User picks existing tools and/or describes new ones
   - For new tools: "I'll create those tools as part of the setup"

8. **"Should a governor validate this agent's input or output?"**
   - List existing governors: `GET /api/v1/governors?limit=50`
   - For each selected: "Inbound (validate input) or outbound (validate output)?"
   - For new governors: "I'll create those governors as part of the setup"

9. **"Any example input/output pairs for few-shot learning?"** (demonstrations, optional)

10. **"Sample input for test execution?"** (recommended)

## Delegate

Delegate to `agent-builder` agent via Task tool with all interview answers + TOKEN + RAILYARD_URL.

## Report

Show the agent's output to the user.
