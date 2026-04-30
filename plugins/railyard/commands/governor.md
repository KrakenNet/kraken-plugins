---
description: Create and configure CLIPS-based governors with rules, facts, streams, and routes for policy enforcement
argument-hint: [create|list] [--stateful] [--stateless]
allowed-tools: [Bash, Read, AskUserQuestion, Task]
---

# Railyard Governor Management

Create CLIPS-based governors for policy enforcement on agent inputs/outputs.

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-railyard/SKILL.md` for API conventions and auth flow.

## Verify Auth

Ensure valid JWT token. If not: "Run /railyard:auth first."

## Parse Arguments

From `$ARGUMENTS`:
- **Action**: `create` (default), `list`
- **--stateful**: Pre-select stateful governor
- **--stateless**: Pre-select stateless governor

## Route by Action

### List

```bash
curl -s "${RAILYARD_URL}/api/v1/governors?limit=50" \
  -H "Authorization: Bearer ${TOKEN}" | jq '.data[] | {id, name, status, stateful}'
```

### Create (default)

Interview:

1. **"What should this governor be called?"** (name)

2. **"What does this governor do?"** (description)

3. **"Should it remember state between invocations?"**
   - Stateful — facts persist across evaluations (good for tracking, counting, rate limiting)
   - Stateless — facts reset each evaluation (good for validation, filtering)

4. **Rules** (repeat until user says done):
   - "Describe a rule this governor should enforce"
   - Agent will translate to CLIPS syntax and show for confirmation
   - "Priority for this rule?" (lower = runs first, default 10)
   - "Add another rule?" (yes/no)

5. **Facts** (repeat until user says done):
   - "Does this governor need any initial data or templates?"
   - If yes: "Describe the data structure"
   - Agent generates deftemplate + slot_definitions
   - "Add another fact?" (yes/no)

6. **Streams** (optional):
   - "Should this governor connect to external data sources or outputs?"
   - If yes: name, direction (inbound/outbound), type (http/kafka/memory/webhook), config
   - "Add another stream?" (yes/no)

7. **Routes** (optional, only if streams exist):
   - "Should data flow between streams?"
   - If yes: input stream → output stream, filter expression, transform expression
   - "Add another route?" (yes/no)

8. **"Provide sample test input for verification?"** (recommended)

## Delegate

Delegate to `governor-builder` agent via Task tool with all interview answers + TOKEN + RAILYARD_URL.

## Report

Show the agent's output to the user, including build-test-fix loop results.
