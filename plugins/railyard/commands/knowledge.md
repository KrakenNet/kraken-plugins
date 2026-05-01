---
description: Manage documents, knowledge graph, and entity extraction for RAG-powered agents
argument-hint: [ingest|build|explore|search|embeddings|retrieval|kg-summaries|kg-entities|kg-communities]
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
- **Action / Resource**: `ingest` (default), `build`, `explore`, `search`, `embeddings`, `retrieval`, `kg-summaries`, `kg-entities`, `kg-communities`

## Endpoint Map

| Resource | Endpoint | Notes |
|----------|----------|-------|
| documents | `/api/v1/documents` | CRUD; `POST /documents/search` for hybrid/keyword/vector search |
| embeddings | `/api/v1/embeddings` | CRUD on stored vectors; `POST /embeddings/search` for vector search |
| retrieval | `/api/v1/retrieval` | `POST` query — returns ranked chunks |
| kg-summaries | `/api/v1/knowledge-graph/summaries` | Filter by `community_id`, paginated |
| kg-entities | `/api/v1/knowledge-graph/entities` | Filter by `kb_id`, `entity_type`; supports `?include=relationships` |
| kg-communities | `/api/v1/knowledge-graph/communities` | Filter by `kb_id`, `level` (0=top-level) |

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

### Embeddings

Standard CRUD plus vector search.

Interview for create:
- **model** (e.g. `text-embedding-3-small`)
- **dimensions** (integer; must match the model)
- **source_doc_id** (optional — link embedding back to its source document)

For search:
- **query** (text), **k** (top-k), **filter** (optional metadata filter)

```bash
# Vector search
curl -s -X POST "${RAILYARD_URL}/api/v1/embeddings/search" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"query":"...","k":10,"filter":{}}'
```

Delegate complex flows to `knowledge-builder` agent.

### Retrieval

Single endpoint that returns ranked chunks across documents/embeddings.

Interview:
- **query**, **k**, **filter** (optional), **kb_id** (scope retrieval to a knowledge base)

```bash
curl -s -X POST "${RAILYARD_URL}/api/v1/retrieval" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"query":"...","k":10,"filter":{},"kb_id":"..."}'
```

### kg-summaries

List/inspect community summaries.

Interview:
- **community_id** (required to filter; otherwise paginated list)

```bash
curl -s "${RAILYARD_URL}/api/v1/knowledge-graph/summaries?community_id=${COMMUNITY_ID}&limit=50" \
  -H "Authorization: Bearer ${TOKEN}"
```

### kg-entities

List/inspect entities; optionally include relationships.

Interview:
- **kb_id** (required), **entity_type** (optional filter)
- Append `?include=relationships` to fetch outgoing/incoming edges inline.

```bash
curl -s "${RAILYARD_URL}/api/v1/knowledge-graph/entities?kb_id=${KB_ID}&entity_type=${TYPE}&include=relationships" \
  -H "Authorization: Bearer ${TOKEN}"
```

### kg-communities

List communities; level=0 returns top-level partitions.

Interview:
- **kb_id** (required), **level** (integer; 0=top-level)

```bash
curl -s "${RAILYARD_URL}/api/v1/knowledge-graph/communities?kb_id=${KB_ID}&level=0" \
  -H "Authorization: Bearer ${TOKEN}"
```

## Report

Show the agent's output to the user.
