---
name: railyard-api
description: This skill should be used when any railyard builder agent needs to know API endpoints, request/response schemas, field types, enum values, or sub-resource relationships for agents, tools, governors, workflows, credentials, documents, knowledge graph, memories, chat sessions, knowledge bases, integrations, inbound sources, LLM models, traces, or export/import. Embedded API reference for all Railyard domains.
version: 1.0.0
user-invocable: false
---

# Railyard API Reference

Embedded API knowledge for builder agents. Base URL and auth handled by smart-railyard skill.

## Health & Dashboard

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/health | Returns `{"status":"healthy"}` |
| GET | /api/v1/ready | Returns `{"status":"ready"}` or 503 |
| GET | /api/v1/dashboard/stats | Aggregated platform statistics |

## Credentials

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/credentials | List (paginated). Filter: `?provider=X` |
| POST | /api/v1/credentials | Create credential |
| GET | /api/v1/credentials/{id} | Get credential |
| PUT | /api/v1/credentials/{id} | Update credential |
| DELETE | /api/v1/credentials/{id} | Delete credential |
| POST | /api/v1/credentials/{id}/test | Test credential connectivity |

**Create credential:**
```json
{
  "name": "string (required)",
  "credential_type": "api_key|oauth2|basic_auth|bearer_token|custom (required)",
  "value": "object (required, structure varies by type)",
  "provider": "string (optional)",
  "endpoint_url": "string (optional)",
  "description": "string (optional)",
  "is_active": true
}
```

**Value structures by type:**
- `api_key`: `{"key": "..."}`
- `oauth2`: `{"client_id": "...", "client_secret": "...", "access_token": "...", "refresh_token": "...", "token_type": "..."}`
- `basic_auth`: `{"username": "...", "password": "..."}`
- `bearer_token`: `{"token": "..."}`
- `custom`: any JSON object

## Agents

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/agents | List (paginated) |
| POST | /api/v1/agents | Create (starts `paused`) |
| GET | /api/v1/agents/{id} | Get agent |
| PUT | /api/v1/agents/{id} | Update (partial) |
| DELETE | /api/v1/agents/{id} | Delete agent |
| POST | /api/v1/agents/{id}/execute | Execute (must be `active`) |
| POST | /api/v1/agents/{id}/execute/batch | Batch execute |

**Create agent:**
```json
{
  "name": "string (required)",
  "dspy_module": "predict|chain_of_thought|react|multi_chain_comparison|refine|parallel|rlm (required)",
  "system_prompt": "string (optional)",
  "model": "string (optional)",
  "temperature": 0.7,
  "type": "string (optional)",
  "description": "string (optional)",
  "max_concurrent": 5,
  "timeout": 30,
  "retries": 3,
  "input_schema": {"type": "object", ...},
  "output_schema": {"type": "object", ...},
  "signature": {...},
  "color": "#hex",
  "icon": "string"
}
```

**Execute agent:**
```json
{
  "input": {"key": "value"},
  "session_id": "uuid (optional)",
  "include_trace": true,
  "include_demonstrations": true
}
```

### Agent Sub-resources

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/agents/{id}/tools | List linked tools |
| POST | /api/v1/agents/{id}/tools | Link tool: `{"tool_id": "uuid"}` |
| DELETE | /api/v1/agents/{id}/tools/{toolId} | Unlink tool |
| GET | /api/v1/agents/{id}/governors | List governor maps |
| POST | /api/v1/agents/{id}/governors | Map: `{"governor_id":"uuid","is_input":true,"priority":1}` |
| PUT | /api/v1/agents/{id}/governors/{mapId} | Update map |
| DELETE | /api/v1/agents/{id}/governors/{mapId} | Delete map |
| GET | /api/v1/agents/{id}/demonstrations | List demos |
| POST | /api/v1/agents/{id}/demonstrations | Create demo |
| PUT | /api/v1/agents/{id}/demonstrations/{demoId} | Update demo |
| DELETE | /api/v1/agents/{id}/demonstrations/{demoId} | Delete demo |
| GET | /api/v1/agents/{id}/sessions | List sessions |
| GET | /api/v1/agents/{id}/trace | List traces |
| GET | /api/v1/agents/{id}/monitor | WebSocket monitoring |
| GET | /api/v1/agents/{id}/memory-sources | List memory sources |
| POST | /api/v1/agents/{id}/memory-sources | Configure memory source |
| GET | /api/v1/agents/{id}/credentials | List credential assignments |
| POST | /api/v1/agents/{id}/credentials | Assign credential |
| GET | /api/v1/agents/{id}/knowledge-bases | List associated KBs |
| POST | /api/v1/agents/{id}/mcp | MCP integration |

**Create demo:**
```json
{
  "input_data": {"question": "..."},
  "output_data": {"answer": "..."},
  "is_successful": true,
  "notes": "string"
}
```

## Tools

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/tools | List. Filters: `?category=X&method=Y` |
| POST | /api/v1/tools | Create tool |
| GET | /api/v1/tools/{id} | Get tool |
| PUT | /api/v1/tools/{id} | Update (partial) |
| DELETE | /api/v1/tools/{id} | Delete tool |
| POST | /api/v1/tools/{id}/test | Test execution |
| GET | /api/v1/tools/methods | List implementation methods |
| POST | /api/v1/tools/methods | Create method |

**Create tool:**
```json
{
  "name": "string (required)",
  "implementation_method": "python|shell|api|dspy (required)",
  "content": "string (inline code, optional)",
  "file_path": "string (external script, optional)",
  "url": "string (for API tools, optional)",
  "description": "string",
  "category": "string",
  "input_schema": {...},
  "output_schema": {...},
  "arguments": {...},
  "env": {"KEY": "VALUE"},
  "is_active": true
}
```

**Test tool:**
```json
{"data": {"key": "value"}, "schema": {...}}
```

### Tool Sub-resources

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/tools/{id}/governors | List governor maps |
| POST | /api/v1/tools/{id}/governors | Create map |
| PUT | /api/v1/tools/{id}/governors/{mapId} | Update map |
| DELETE | /api/v1/tools/{id}/governors/{mapId} | Delete map |

## Governors

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/governors | List (paginated) |
| POST | /api/v1/governors | Create (defaults `idle`) |
| GET | /api/v1/governors/{id} | Get governor |
| PUT | /api/v1/governors/{id} | Update |
| DELETE | /api/v1/governors/{id} | Delete (auto-stops) |
| POST | /api/v1/governors/{id}/start | Start CLIPS engine |
| POST | /api/v1/governors/{id}/stop | Stop CLIPS engine |
| GET | /api/v1/governors/{id}/status | Runtime status |
| POST | /api/v1/governors/{id}/test | One-shot test |
| GET | /api/v1/governors/{id}/trace | Trace entries |
| POST | /api/v1/governors/{id}/validate | Validate rules syntax |
| GET | /api/v1/governors/{id}/monitor | WebSocket monitoring |
| GET | /api/v1/governors/{id}/ws | Governor WebSocket connection |

**Create governor:**
```json
{
  "name": "string (required)",
  "description": "string",
  "stateful": true,
  "icon": "string",
  "color": "#hex"
}
```

### Governor Sub-resources

**Rules:**

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/governors/{id}/rules | List rules |
| POST | /api/v1/governors/{id}/rules | Create rule |
| GET | /api/v1/governors/{id}/rules/{ruleId} | Get rule |
| PUT | /api/v1/governors/{id}/rules/{ruleId} | Update (sets X-Restart-Required if running) |
| DELETE | /api/v1/governors/{id}/rules/{ruleId} | Delete rule |

```json
{
  "name": "string (required)",
  "description": "string",
  "rule_content": "(defrule name \"doc\" ... => ...)",
  "priority": 10,
  "is_enabled": true
}
```

**Facts:**

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/governors/{id}/facts | List static facts |
| POST | /api/v1/governors/{id}/facts | Create fact |
| GET | /api/v1/governors/{id}/facts/runtime | Live facts from CLIPS (must be running) |
| GET | /api/v1/governors/{id}/facts/{factId} | Get fact |
| PUT | /api/v1/governors/{id}/facts/{factId} | Update fact |
| DELETE | /api/v1/governors/{id}/facts/{factId} | Delete fact |

```json
{
  "name": "string (required)",
  "fact_content": "(template-name (slot1 value1) (slot2 value2))",
  "is_template": false,
  "is_enabled": true,
  "slot_definitions": {"slot-name": "type"}
}
```

**Streams:**

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/governors/{id}/streams | List streams |
| POST | /api/v1/governors/{id}/streams | Create stream |
| GET | /api/v1/governors/{id}/streams/{streamId} | Get stream |
| PUT | /api/v1/governors/{id}/streams/{streamId} | Update stream |
| DELETE | /api/v1/governors/{id}/streams/{streamId} | Delete stream |

```json
{
  "name": "string (required)",
  "direction": "inbound|outbound",
  "stream_type": "http|kafka|memory|webhook",
  "config": {"endpoint": "/webhook/input", ...},
  "is_enabled": true
}
```

**Routes:**

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/governors/{id}/routes | List routes |
| POST | /api/v1/governors/{id}/routes | Create route |
| GET | /api/v1/governors/{id}/routes/{routeId} | Get route |
| PUT | /api/v1/governors/{id}/routes/{routeId} | Update route |
| DELETE | /api/v1/governors/{id}/routes/{routeId} | Delete route |

```json
{
  "name": "string (required)",
  "input_stream_id": "uuid",
  "output_stream_id": "uuid",
  "filter_expression": "severity >= 'high'",
  "transform_expression": "{ message: input.content }",
  "is_enabled": true
}
```

**Snapshots:**

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/governors/{id}/snapshots | List snapshots |
| POST | /api/v1/governors/{id}/snapshots | Create snapshot |
| GET | /api/v1/governors/{id}/snapshots/{snapshotId} | Get snapshot |
| DELETE | /api/v1/governors/{id}/snapshots/{snapshotId} | Delete snapshot |

## Workflows

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/workflows | List. Filter: `?is_active=true` |
| POST | /api/v1/workflows | Create workflow |
| GET | /api/v1/workflows/{id} | Get workflow |
| PUT | /api/v1/workflows/{id} | Update (partial) |
| DELETE | /api/v1/workflows/{id} | Delete workflow |
| POST | /api/v1/workflows/{id}/duplicate | Deep-copy workflow |
| POST | /api/v1/workflows/{id}/execute | Execute |
| GET | /api/v1/workflows/{id}/executions | List executions |

**Create workflow:**
```json
{
  "name": "string (required)",
  "description": "string",
  "is_active": true,
  "is_default": false
}
```

**Execute workflow:**
```json
{
  "trigger_type": "manual",
  "trigger_id": "string",
  "trigger_data": {"prompt": "..."}
}
```

### Stages

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/workflows/{id}/stages | List stages |
| POST | /api/v1/workflows/{id}/stages | Create stage |
| PUT | /api/v1/workflows/{id}/stages/reorder | Reorder stages |
| GET | /api/v1/workflows/{id}/stages/{stageId} | Get stage |
| PUT | /api/v1/workflows/{id}/stages/{stageId} | Update stage |
| DELETE | /api/v1/workflows/{id}/stages/{stageId} | Delete stage |

```json
{
  "name": "string (required)",
  "description": "string",
  "sequence_order": 1,
  "run_in_parallel": false,
  "loop": false,
  "max_iterations": 1,
  "timeout": 60,
  "retries": 1,
  "require_approval": false,
  "on_fail_action": "stop",
  "input_mapping": {},
  "output_mapping": {}
}
```

### Steps

| Method | Path | Description |
|--------|------|-------------|
| GET | .../{stageId}/steps | List steps |
| POST | .../{stageId}/steps | Create step |
| GET | .../{stageId}/steps/{stepId} | Get step |
| PUT | .../{stageId}/steps/{stepId} | Update step |
| DELETE | .../{stageId}/steps/{stepId} | Delete step |

```json
{
  "name": "string (required)",
  "type": "agent_call|tool_call|governor_check|human_approval",
  "agent_id": "uuid (for agent_call)",
  "tool_id": "uuid (for tool_call)",
  "governor_id": "uuid (for governor_check)",
  "step_order": 1,
  "input_schema": {...},
  "output_schema": {...},
  "condition": "previous.confidence > 0.8",
  "true_next_step": "uuid",
  "false_next_step": "uuid"
}
```

## Executions

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/executions | List. Filters: `?status=running` |
| GET | /api/v1/executions/{id} | Get execution |
| POST | /api/v1/executions/{id}/cancel | Cancel running |
| POST | /api/v1/executions/{id}/retry | Retry failed |
| GET | /api/v1/executions/{id}/trace | Execution traces |
| GET | /api/v1/executions/{id}/stages | Stage executions |
| GET | /api/v1/executions/{id}/steps | Step executions |
| POST | /api/v1/executions/{id}/retry-stage | Retry specific stage |
| GET | /api/v1/executions/{id}/monitor | WebSocket monitoring |

## Routing Rules

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/routing-rules | List (paginated) |
| POST | /api/v1/routing-rules | Create rule |
| POST | /api/v1/routing-rules/evaluate | Evaluate against data |
| GET | /api/v1/routing-rules/{id} | Get rule |
| PUT | /api/v1/routing-rules/{id} | Update rule |
| DELETE | /api/v1/routing-rules/{id} | Delete rule |
| POST | /api/v1/routing-rules/{id}/toggle | Toggle enabled |

```json
{
  "name": "string (required)",
  "attribute": "string (required)",
  "operator": "equals|contains|startsWith|endsWith|regex|greaterThan|lessThan",
  "value": "string (required)",
  "condition": "string (optional)",
  "workflow_id": "uuid (optional)",
  "auto_start": true,
  "priority": 1,
  "max_concurrent": 5,
  "notify_channels": ["slack", "email"],
  "is_enabled": true
}
```

## Alerts

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/alerts | List. Filters: `?status=pending&type=approval` |
| GET | /api/v1/alerts/{id} | Get alert |
| POST | /api/v1/alerts/{id}/acknowledge | Acknowledge |
| POST | /api/v1/alerts/{id}/approve | Approve (resumes workflow) |
| POST | /api/v1/alerts/{id}/reject | Reject. Body: `{"note":"reason"}` |
| POST | /api/v1/alerts/{id}/dismiss | Dismiss |
| PUT | /api/v1/alerts/{id}/assign | Reassign: `{"assign_to":"uuid"}` |

## Documents

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/documents | List. Filters: `?type=X&has_embeddings=true` |
| POST | /api/v1/documents | Create document |
| POST | /api/v1/documents/upload | Upload file (multipart, 50MB max) |
| POST | /api/v1/documents/search | Search: vector, keyword, or hybrid |
| GET | /api/v1/documents/{id} | Get document |
| PUT | /api/v1/documents/{id} | Update metadata |
| DELETE | /api/v1/documents/{id} | Delete (cascade) |
| GET | /api/v1/documents/{id}/chunks | List chunks |
| POST | /api/v1/documents/{id}/reingest | Re-chunk with new params |

**Create document:**
```json
{
  "title": "string (required)",
  "content": "string (required)",
  "type": "string (optional)"
}
```

**Search:**
```json
{
  "query": "string (required)",
  "mode": "vector|keyword|hybrid",
  "top_k": 10,
  "min_score": 0.5,
  "document_types": ["string"],
  "agent_id": "uuid"
}
```

## Knowledge Graph

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/knowledge-graph/search | Search: keyword, semantic, graph-traversal |
| GET | /api/v1/knowledge-graph/nodes | List nodes. Filter: `?node_type=X&search=Y` |
| POST | /api/v1/knowledge-graph/nodes | Create node |
| GET | /api/v1/knowledge-graph/nodes/{id} | Get node |
| PUT | /api/v1/knowledge-graph/nodes/{id} | Update node |
| DELETE | /api/v1/knowledge-graph/nodes/{id} | Delete node |
| GET | /api/v1/knowledge-graph/nodes/{id}/neighbors | Get neighbors (depth param) |
| GET | /api/v1/knowledge-graph/edges | List edges |
| POST | /api/v1/knowledge-graph/edges | Create edge |
| GET | /api/v1/knowledge-graph/edges/{id} | Get edge |
| PUT | /api/v1/knowledge-graph/edges/{id} | Update edge |
| DELETE | /api/v1/knowledge-graph/edges/{id} | Delete edge |

**Create node:**
```json
{
  "label": "string (required)",
  "type": "string (required)",
  "properties": {},
  "x_position": 0.0,
  "y_position": 0.0
}
```

**Create edge:**
```json
{
  "from_node_id": "uuid (required)",
  "to_node_id": "uuid (required)",
  "label": "string (required)",
  "properties": {},
  "weight": 1.0
}
```

### Entities & Extraction

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/knowledge-graph/entities/extract | Extract from document |
| GET | /api/v1/knowledge-graph/entities/entities | List for document |
| GET | /api/v1/knowledge-graph/entities/entities/{id} | Get entity |
| POST | /api/v1/knowledge-graph/entities/entities/{id}/resolve | Resolve to KG node |
| GET | /api/v1/knowledge-graph/entities/aliases | List aliases for node |
| POST | /api/v1/knowledge-graph/entities/aliases | Create alias |

### Summaries

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/knowledge-graph/summaries/generate | Generate summary |
| GET | /api/v1/knowledge-graph/summaries | List summaries |
| GET | /api/v1/knowledge-graph/summaries/{id} | Get summary |

### Communities

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/knowledge-graph/communities/detect | Run detection |
| GET | /api/v1/knowledge-graph/communities | List (requires run_id) |
| GET | /api/v1/knowledge-graph/communities/{id} | Get community |
| POST | /api/v1/knowledge-graph/communities/{id}/summarize | Summarize community |

## Memories

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/memories | List. Filters: `?type=X&agent_id=Y&min_importance=0.5` |
| POST | /api/v1/memories | Create memory |
| POST | /api/v1/memories/search | Semantic search |
| POST | /api/v1/memories/decay | Run decay |
| POST | /api/v1/memories/consolidate | Consolidate similar |
| GET | /api/v1/memories/stats | Memory stats |
| GET | /api/v1/memories/{id} | Get memory |
| PUT | /api/v1/memories/{id} | Update memory |
| DELETE | /api/v1/memories/{id} | Delete memory |
| GET | /api/v1/memories/{id}/access-log | Access history |

**Create memory:**
```json
{
  "content": "string (required)",
  "type": "string (required)",
  "agent_id": "uuid (optional)",
  "tags": ["string"],
  "importance": 0.5
}
```

**Search memories:**
```json
{
  "query": "string (required)",
  "top_k": 10,
  "types": ["string"],
  "min_importance": 0.3,
  "agent_id": "uuid"
}
```

## Retrieval

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/retrieval/queries | List queries |
| GET | /api/v1/retrieval/queries/{id} | Get query + results |
| GET | /api/v1/retrieval/queries/{id}/results | List results |
| POST | /api/v1/retrieval/results/{id}/feedback | Submit feedback |
| GET | /api/v1/retrieval/results/{id}/feedback | List feedback |
| GET | /api/v1/retrieval/analytics | Retrieval analytics |

## Embeddings

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/embeddings/models | List models |
| POST | /api/v1/embeddings/models | Create model |
| GET | /api/v1/embeddings/models/{id} | Get model |
| PUT | /api/v1/embeddings/models/{id} | Update model |
| DELETE | /api/v1/embeddings/models/{id} | Delete model |
| POST | /api/v1/embeddings/models/{id}/set-default | Set default |

## Chat Sessions

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/chat/sessions | List sessions |
| POST | /api/v1/chat/sessions | Create session |
| GET | /api/v1/chat/sessions/{id} | Get session |
| PATCH | /api/v1/chat/sessions/{id} | Update (title) |
| DELETE | /api/v1/chat/sessions/{id} | Archive session |
| GET | /api/v1/chat/sessions/{id}/messages | List messages. Query: `after_sequence`, `limit` |

**Create session:**
```json
{
  "agent_id": "uuid (optional — connect to agent)"
}
```

**Update session:**
```json
{
  "title": "string"
}
```

**Chat message (in response):**
```json
{
  "id": "uuid",
  "session_id": "uuid",
  "role": "user|assistant|system|narration|tool",
  "content": "string",
  "metadata": {},
  "sequence": 1,
  "created_at": "timestamp"
}
```

### WebSocket

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/ws/chat/{sessionId}?token=JWT | Real-time chat WebSocket |

**WebSocket event:**
```json
{
  "type": "message|stream_token|narration|approval_request|approval_response|error",
  "session_id": "uuid",
  "message_id": "uuid",
  "role": "string",
  "content": "string",
  "metadata": {},
  "sequence": 1,
  "done": false,
  "timestamp": "timestamp"
}
```

## Knowledge Bases

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/knowledge-bases | List (paginated) |
| POST | /api/v1/knowledge-bases | Create knowledge base |
| GET | /api/v1/knowledge-bases/{id} | Get knowledge base |
| PUT | /api/v1/knowledge-bases/{id} | Update knowledge base |
| DELETE | /api/v1/knowledge-bases/{id} | Delete knowledge base |
| GET | /api/v1/knowledge-bases/{id}/acls | List ACLs |
| POST | /api/v1/knowledge-bases/{id}/acls | Create ACL |
| DELETE | /api/v1/knowledge-bases/{id}/acls/{aclId} | Delete ACL |
| POST | /api/v1/knowledge-bases/{id}/tags | Assign tag: `{"tag_id":"uuid"}` |
| DELETE | /api/v1/knowledge-bases/{id}/tags/{tagId} | Unassign tag |

**Create knowledge base:**
```json
{
  "name": "string (required)",
  "description": "string (optional)",
  "parent_kb_id": "uuid (optional — for hierarchical KBs)",
  "visibility": "private|shared (optional, default: private)"
}
```

**Update knowledge base:**
```json
{
  "name": "string (required)",
  "description": "string (optional)",
  "parent_kb_id": "uuid (optional)",
  "visibility": "string (optional)",
  "metadata": {}
}
```

**Create ACL:**
```json
{
  "grantee_user_id": "uuid (optional)",
  "grantee_group_id": "uuid (optional)",
  "permission": "string (required)"
}
```

### KB Tags

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/kb-tags | List all tags |
| POST | /api/v1/kb-tags | Create tag |
| DELETE | /api/v1/kb-tags/{id} | Delete tag |

**Create tag:**
```json
{
  "name": "string (required)",
  "description": "string (optional)",
  "color": "#hex (optional)"
}
```

## Integrations

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/integrations | List all integrations |
| GET | /api/v1/integrations/{type} | Get integration by adapter type |
| PUT | /api/v1/integrations/{type} | Update settings/enable |
| POST | /api/v1/integrations/{type}/test | Test connection |
| GET | /api/v1/integrations/{type}/actions | List available actions |
| POST | /api/v1/integrations/{type}/actions/{action} | Execute action |

**Update integration:**
```json
{
  "settings": {},
  "credential_id": "uuid (optional)",
  "enabled": true
}
```

**Test connection:**
```json
{
  "settings": {},
  "credential_id": "uuid (optional)"
}
```

**Execute action:**
```json
{
  "integration_id": "uuid (required)",
  "input": {}
}
```

**Integration (response):**
```json
{
  "id": "uuid",
  "name": "string",
  "adapter_type": "string",
  "status": "connected|disconnected|error",
  "settings": {},
  "settings_schema": {},
  "ui_schema": {},
  "credential_id": "uuid",
  "has_credential": true,
  "enabled": true,
  "error_message": "string"
}
```

## Inbound Sources

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/inbound-sources | List (paginated) |
| POST | /api/v1/inbound-sources | Create source |
| GET | /api/v1/inbound-sources/{id} | Get source |
| PUT | /api/v1/inbound-sources/{id} | Update source |
| DELETE | /api/v1/inbound-sources/{id} | Delete source |
| POST | /api/v1/inbound-sources/{id}/activate | Activate source |
| POST | /api/v1/inbound-sources/{id}/pause | Pause source |
| POST | /api/v1/inbound-sources/{id}/test | Test connection |

**Create inbound source:**
```json
{
  "name": "string (required)",
  "description": "string (optional)",
  "source_type": "manual|http_poll|email|webhook (required)",
  "status": "active|paused|error|disabled (optional, default: disabled)",
  "poll_url": "string (for http_poll)",
  "poll_interval_seconds": 300,
  "poll_method": "GET|POST (optional)",
  "poll_headers": {},
  "webhook_path": "string (for webhook)",
  "webhook_secret": "string (optional)",
  "email_address": "string (for email)",
  "email_protocol": "IMAP|POP3 (optional)",
  "email_server": "string (optional)",
  "email_port": 993,
  "field_mapping": {},
  "request_type_id": "uuid (optional)",
  "default_priority": "low|medium|high|critical (default: medium)",
  "default_title_template": "string (optional)",
  "credential_id": "uuid (optional)"
}
```

## LLM Models

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/llm-models | List (paginated) |
| POST | /api/v1/llm-models | Create model |
| GET | /api/v1/llm-models/{id} | Get model |
| PUT | /api/v1/llm-models/{id} | Update model |
| DELETE | /api/v1/llm-models/{id} | Delete model |
| POST | /api/v1/llm-models/{id}/set-default | Set as platform default |

**Create LLM model:**
```json
{
  "name": "string (required)",
  "provider": "string (required — e.g. openai, anthropic, ollama)",
  "model_id": "string (required — provider model ID)",
  "base_url": "string (optional — custom endpoint)",
  "max_tokens": 4096,
  "default_temperature": 0.7,
  "supports_tools": true,
  "supports_vision": false,
  "credential_id": "uuid (optional)",
  "is_default": false,
  "is_active": true,
  "config": {}
}
```

## Export/Import

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/v1/export | Export entity bundle |
| POST | /api/v1/import | Import bundle (multipart). Query: `?dry_run=true` |

**Export request:**
```json
{
  "entity_type": "agent|tool|governor|workflow (required)",
  "entity_id": "uuid (required)",
  "scope": "entity|dependencies|environment (required)"
}
```

**Export response (bundle):**
```json
{
  "version": 1,
  "exported_at": "timestamp",
  "platform": "string",
  "scope": "string",
  "root_entity": {"type": "string", "id": "uuid", "name": "string"},
  "entities": {
    "credentials": [],
    "tools": [],
    "agents": [],
    "governors": [],
    "workflows": []
  }
}
```

**Import:** Multipart form with `bundle` file field. Returns:
```json
{
  "created": {
    "credentials": 0,
    "tools": 0,
    "agents": 0,
    "governors": 0,
    "workflows": 0
  },
  "credential_placeholders": ["name1", "name2"]
}
```

## Traces

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/traces | List traces. Required: `?entity_type=X&entity_id=Y` |
| GET | /api/v1/traces/{traceId}/tree | Get span tree |
| GET | /api/v1/traces/{traceId}/spans/{spanId} | Get span detail |

### WebSocket

| Method | Path | Description |
|--------|------|-------------|
| GET | /api/v1/ws/traces/monitor | Real-time trace monitoring |
