---
description: Inspect execution traces and span trees for debugging agents, tools, governors, and workflows
argument-hint: [list|tree|span] [--entity-type agent|tool|governor|workflow] [--entity-id <id>]
allowed-tools: [Bash, Read, AskUserQuestion]
---

# Railyard Trace Inspector

View execution traces and span trees for debugging and monitoring.

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-railyard/SKILL.md` for API conventions and auth flow.

## Verify Auth

Ensure valid JWT token. If not: "Run /railyard:auth first."

## Parse Arguments

From `$ARGUMENTS`:
- **Action**: `list` (default), `tree`, `span`
- **--entity-type**: Filter by entity type
- **--entity-id**: Filter by entity ID

## Route by Action

### List (default)

Interview (if not provided via args):

1. **"What type of entity?"**
   - agent
   - tool
   - governor
   - workflow

2. List entities of that type and ask **"Which one?"** (entity_id)

Execute:
```bash
curl -s "${RAILYARD_URL}/api/v1/traces?entity_type=${TYPE}&entity_id=${ID}&limit=20" \
  -H "Authorization: Bearer ${TOKEN}" | jq '.data[] | {id, entity_type, entity_id, created_at}'
```

Display as table:
```
| Trace ID | Entity | Created | Spans |
|----------|--------|---------|-------|
| abc-123  | agent  | 2m ago  | 5     |
```

### Tree

View the full span tree for a specific trace.

Interview:

1. If no trace ID provided, run List flow first to pick one
2. **"Which trace?"** (trace_id)

Execute:
```bash
curl -s "${RAILYARD_URL}/api/v1/traces/${TRACE_ID}/tree" \
  -H "Authorization: Bearer ${TOKEN}"
```

Display as indented tree:
```
[trace-id] agent execution (450ms)
  ├── governor_inbound: input-validator (12ms) ✓
  ├── llm_call: chain_of_thought (320ms) ✓
  ├── tool_call: json-validator (45ms) ✓
  └── governor_outbound: output-policy (8ms) ✓
```

### Span

View detailed information for a specific span.

Interview:

1. If no trace/span provided, run Tree flow first
2. **"Which span?"** (span_id)

Execute:
```bash
curl -s "${RAILYARD_URL}/api/v1/traces/${TRACE_ID}/spans/${SPAN_ID}" \
  -H "Authorization: Bearer ${TOKEN}"
```

Display full span detail including input, output, duration, errors.

## Report

Show the output to the user.
