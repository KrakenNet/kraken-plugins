---
description: Manage documents, knowledge graph, and entity extraction for RAG-powered agents
argument-hint: [ingest|build|explore|search]
allowed-tools: [Bash, Read, AskUserQuestion, Task]
---

# Railyard Knowledge Management

Ingest documents, build knowledge graphs, extract entities, and verify retrieval.

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-railyard/SKILL.md` for API conventions and auth flow.

## Verify Auth

Ensure valid JWT token. If not: "Run /railyard:auth first."

## Parse Arguments

From `$ARGUMENTS`:
- **Action**: `ingest` (default), `build`, `explore`, `search`

## Route by Action

### Ingest

Interview:
1. **"Document title?"**
2. **"Paste the content or describe what to ingest"**
3. **"Document type?"** (optional — for categorization)

Delegate to `knowledge-builder` agent with action: ingest_document.

### Build (Knowledge Graph from Documents)

Interview:
1. List existing documents: `GET /api/v1/documents?limit=50`
2. **"Which document(s) to build a knowledge graph from?"**
3. **"Should I detect communities and generate summaries?"** (yes/no)

Delegate to `knowledge-builder` agent with action: build_kg.

### Explore

Interview:
1. **"What are you looking for?"** (search query)
2. **"Search mode?"**
   - keyword — Text matching
   - semantic — Embedding similarity
   - graph-traversal — Follow relationships

Delegate to `knowledge-builder` agent with action: explore_graph.

### Search (Documents)

Interview:
1. **"What are you searching for?"** (query)
2. **"Search mode?"** (vector | keyword | hybrid)

Execute directly:
```bash
curl -s -X POST "${RAILYARD_URL}/api/v1/documents/search" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"query":"...","mode":"hybrid","top_k":10}'
```

## Report

Show the agent's output to the user.
