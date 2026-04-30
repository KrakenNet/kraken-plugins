---
description: Manage agent memories — create, search, decay, consolidate, and view stats
argument-hint: [create|search|maintain|stats]
allowed-tools: [Bash, Read, AskUserQuestion, Task]
---

# Railyard Memory Management

Manage long-term memories for agents — creation, semantic search, and maintenance.

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-railyard/SKILL.md` for API conventions and auth flow.

## Verify Auth

Ensure valid JWT token. If not: "Run /railyard:auth first."

## Parse Arguments

From `$ARGUMENTS`:
- **Action**: `create` (default), `search`, `maintain`, `stats`

## Route by Action

### Create

Interview:
1. **"Which agent is this memory for?"** (list agents, or "global" for no agent)
2. **"What should the agent remember?"** (content)
3. **"Memory type?"** (e.g., fact, experience, preference, instruction)
4. **"Tags?"** (optional — comma-separated)
5. **"Importance?"** (0.0 to 1.0, default 0.5 — higher = decays slower)

Delegate to `knowledge-builder` agent with action: create_memory.

### Search

Interview:
1. **"What are you looking for?"** (query)
2. **"Filter by agent?"** (optional — list agents)
3. **"Minimum importance?"** (optional)

Execute:
```bash
curl -s -X POST "${RAILYARD_URL}/api/v1/memories/search" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"query":"...","top_k":10,"agent_id":"...","min_importance":0.3}'
```

### Maintain

Interview:
1. **"What maintenance action?"**
   - decay — Apply time-based decay to all memories
   - consolidate — Merge similar memories for an agent

For consolidate:
2. **"Which agent?"** (required)
3. **"Similarity threshold?"** (optional, default from API)

Delegate to `knowledge-builder` agent with action: maintain_memory.

### Stats

Execute directly:
```bash
curl -s "${RAILYARD_URL}/api/v1/memories/stats" \
  -H "Authorization: Bearer ${TOKEN}" | jq '.data'
```

## Report

Show results to user.
