# Railyard API Quick Reference

## Conventions

- **Base URL:** `${RAILYARD_URL:-http://localhost:38080}` — all REST endpoints below are mounted under `/api/v1`.
- **Auth:** `Authorization: Bearer ${TOKEN}` (Supabase-issued JWT). Public endpoints: `/api/v1/health`, `/api/v1/ready`, `/metrics`, `/api/v1/docs`.
- **Response envelope:** `{ "success": bool, "data": ..., "meta": { ... }, "error": { "code", "message", "details" } }`. Successful responses set `success=true`; errors set `success=false` and populate `error`.
- **Pagination:**
  - Offset-based (most list endpoints): `?limit=<n>&offset=<n>` — `meta.total`, `meta.limit`, `meta.offset`.
  - Cursor-based (executions/steps/trace, traces, large logs): `?cursor=<opaque>&limit=<n≤200>` — `meta.next_cursor` (null at end).
- **Error catalog:** `401` unauthenticated, `403` forbidden, `404` not found, `409` conflict, `422` validation, `429` rate-limited (Retry-After header), `500` server.
- **WebSocket pattern:** `ws(s)://${RAILYARD_URL}/api/v1/ws/<topic>` with bearer auth via `Authorization` subprotocol or `?token=` query. Events are JSON `{type, seq, ts, payload}`; reconnect with `?since=<seq>`.

## Auth

- `POST /auth/v1/token?grant_type=password` — Supabase GoTrue. Body `{email, password}`. Response `{access_token, refresh_token, expires_in, user}`.
- `POST /auth/v1/token?grant_type=refresh_token` — Body `{refresh_token}`. Response same shape.
- All `/api/v1/*` calls require `Authorization: Bearer <access_token>`.

## Health & Probes

- `GET /api/v1/health` — liveness. Response `{status:"ok", version, uptime_s}`.
- `GET /api/v1/ready` — readiness (db, supabase, queue). Response `{status, checks:[{name,ok,detail}]}`.
- `GET /metrics` — Prometheus exposition format (text/plain).

## Agents

| Verb | Path | Description |
|------|------|-------------|
| GET | `/api/v1/agents` | List agents (offset paged) |
| POST | `/api/v1/agents` | Create agent |
| GET | `/api/v1/agents/{id}` | Get agent |
| PUT | `/api/v1/agents/{id}` | Update agent |
| DELETE | `/api/v1/agents/{id}` | Delete agent |
| POST | `/api/v1/agents/{id}/execute` | Execute agent inline |
| POST | `/api/v1/agents/{id}/execute/batch` | Batch execute |
| GET | `/api/v1/agents/{id}/tools` | List bound tools |
| GET | `/api/v1/agents/{id}/governors` | List bound governors |
| GET | `/api/v1/agents/{id}/demonstrations` | List demonstrations |
| GET | `/api/v1/agents/{id}/sessions` | List sessions |
| GET | `/api/v1/agents/{id}/trace` | Get latest trace |
| GET | `/api/v1/agents/{id}/monitor` | Live monitor data |
| GET | `/api/v1/agents/{id}/memory-sources` | List memory bindings |
| GET | `/api/v1/agents/{id}/credentials` | List credential bindings |
| GET | `/api/v1/agents/{id}/knowledge-bases` | List KB bindings |
| GET | `/api/v1/agents/{id}/mcp` | MCP server bindings |

- **POST body:** `{name:string, dspy_module:enum, system_prompt:string, model_id:uuid, tools:[uuid], governors:[uuid], knowledge_bases:[uuid], metadata:object}`.
- **Response data:** `{id:uuid, name, dspy_module, system_prompt, model_id, tools, governors, knowledge_bases, created_at, updated_at}`.
- `/execute` body: `{input:string|object, context?:object, stream?:bool}` → `{execution_id, output, trace_id}`.

## Tools

| Verb | Path | Description |
|------|------|-------------|
| GET | `/api/v1/tools` | List tools |
| POST | `/api/v1/tools` | Create tool |
| GET | `/api/v1/tools/{id}` | Get tool |
| PUT | `/api/v1/tools/{id}` | Update tool |
| DELETE | `/api/v1/tools/{id}` | Delete tool |
| POST | `/api/v1/tools/{id}/test` | Dry-run a tool |

- **POST body:** `{name, type:python|shell|api|dspy, implementation:object, input_schema:json-schema, output_schema:json-schema, credential_id?:uuid}`.
- **Response data:** `{id, name, type, implementation, input_schema, output_schema, created_at}`.

## Governors

| Verb | Path | Description |
|------|------|-------------|
| GET | `/api/v1/governors` | List governors |
| POST | `/api/v1/governors` | Create governor |
| GET | `/api/v1/governors/{id}` | Get governor |
| PUT | `/api/v1/governors/{id}` | Update governor |
| DELETE | `/api/v1/governors/{id}` | Delete governor |
| GET/POST | `/api/v1/governors/{id}/rules` | CLIPS rule list/add |
| GET/POST | `/api/v1/governors/{id}/facts` | Static facts |
| GET | `/api/v1/governors/{id}/facts/runtime` | Runtime fact snapshot |
| GET/POST | `/api/v1/governors/{id}/streams` | Input streams |
| GET/POST | `/api/v1/governors/{id}/routes` | Output routes |
| GET | `/api/v1/governors/{id}/snapshots` | Saved working memory snapshots |
| POST | `/api/v1/governors/{id}/start` | Start engine |
| POST | `/api/v1/governors/{id}/stop` | Stop engine |
| GET | `/api/v1/governors/{id}/status` | Engine status |
| GET | `/api/v1/governors/{id}/trace` | Last execution trace |
| POST | `/api/v1/governors/{id}/test` | Test rules with sample facts |
| POST | `/api/v1/governors/{id}/validate` | Validate CLIPS source |
| GET | `/api/v1/governors/{id}/monitor` | Live metrics |
| GET (WS) | `/api/v1/governors/{id}/ws` | Live event stream |

- **POST body:** `{name, description?, rules:[{name,clips}], facts:[{name,value}], streams:[...], routes:[...]}`.
- **Response data:** `{id, name, status, rules, facts, streams, routes, created_at}`.

## Workflows + Executions

### Workflows

| Verb | Path | Description |
|------|------|-------------|
| GET | `/api/v1/workflows` | List workflows |
| POST | `/api/v1/workflows` | Create workflow |
| GET | `/api/v1/workflows/{id}` | Get workflow |
| PUT | `/api/v1/workflows/{id}` | Update workflow |
| DELETE | `/api/v1/workflows/{id}` | Delete workflow |
| GET/POST | `/api/v1/workflows/{id}/stages` | Stage CRUD |
| GET/POST | `/api/v1/workflows/{id}/stages/{stageId}/steps` | Step CRUD (`step_type`: agent_call, tool_call, governor_check, human_approval) |
| GET | `/api/v1/workflows/{id}/executions` | Execution history |
| POST | `/api/v1/workflows/{id}/execute` | Trigger run; body `{input?:object, nickname?:string}` → `{execution_id}` |
| POST | `/api/v1/workflows/{id}/duplicate` | Clone workflow |

### Executions

| Verb | Path | Description |
|------|------|-------------|
| GET | `/api/v1/executions` | List (cursor paged, `limit≤200`) |
| GET | `/api/v1/executions/{id}` | Get execution detail |
| POST | `/api/v1/executions/{id}/cancel` | Cancel running execution |
| GET | `/api/v1/executions/{id}/steps` | Step events (cursor paged) |
| GET | `/api/v1/executions/{id}/trace` | Full trace tree (cursor paged) |

- **WS:** `GET /api/v1/ws/v1/executions/{execId}/events?since=<seq>` — live tail of step/log/decision events.
- **Response data (execution):** `{id, workflow_id, status:queued|running|succeeded|failed|canceled, started_at, finished_at, nickname?, input, output?, error?}`.

## Routing Rules + Requests

- `GET/POST /api/v1/routing-rules` — list/create rule.
- `GET/PUT/DELETE /api/v1/routing-rules/{id}`.
- `POST /api/v1/routing-rules/{id}/test` — body `{request:object}` → `{matched:bool, decision, trace}`.
- `GET /api/v1/requests` — request log (offset paged).
- `GET /api/v1/requests/{id}` — single request with routing decision.
- `GET/POST /api/v1/request-types` — schema registry (JSON Schema).
- `GET/PUT/DELETE /api/v1/request-types/{id}`.

- **Rule body:** `{name, priority:int, conditions:[{field,operator:enum,value}], action:{kind, target}}`. Operators: `equals|contains|startsWith|endsWith|regex|greaterThan|lessThan`.

## Knowledge

### Documents
- `GET/POST /api/v1/documents` — list/upload (multipart or JSON).
- `GET/PUT/DELETE /api/v1/documents/{id}`.
- `GET /api/v1/documents/{id}/chunks` — list chunks for a document.
- `POST /api/v1/documents/search` — body `{query, limit?, knowledge_base_id?}`.

### Embeddings
- `GET/POST /api/v1/embeddings` — list/create.
- `GET/PUT/DELETE /api/v1/embeddings/{id}`.
- `POST /api/v1/embeddings/search` — body `{vector?:[float]|query?:string, top_k:int, filter?:object}` → `{matches:[{id,score,metadata}]}`.

### Knowledge Graph
- `GET /api/v1/knowledge-graph` — root summary.
- `GET /api/v1/knowledge-graph/nodes` / `GET /api/v1/knowledge-graph/edges`.
- `GET /api/v1/knowledge-graph/nodes/{id}/neighbors`.
- `POST /api/v1/knowledge-graph/search`.
- `GET/POST /api/v1/knowledge-graph/summaries` (+ `/generate`).
- `GET/POST /api/v1/knowledge-graph/entities` (+ `/extract`, `/aliases`).
- `GET/POST /api/v1/knowledge-graph/communities` (+ `/detect`).

### Memories
- `GET/POST /api/v1/memories` — list/create.
- `GET/PUT/DELETE /api/v1/memories/{id}`.
- `POST /api/v1/memories/search` — semantic search.
- `POST /api/v1/memories/decay` — apply decay function.
- `POST /api/v1/memories/consolidate` — merge similar memories.
- `GET /api/v1/memories/stats` — counts and salience histogram.

### Retrieval
- `POST /api/v1/retrieval` — unified RAG query. Body `{query, knowledge_base_ids?:[uuid], top_k?, filters?:object, include?:[documents,memories,graph]}` → `{results:[{type, id, score, content, metadata}], trace_id}`.

### Knowledge Bases
- `GET/POST /api/v1/knowledge-bases` — list/create.
- `GET/PUT/DELETE /api/v1/knowledge-bases/{id}`.
- `GET/POST/DELETE /api/v1/knowledge-bases/{id}/acls` — visibility ACLs.
- `GET/POST /api/v1/knowledge-bases/{id}/tags` — tag membership.

### KB Tags
- `GET/POST /api/v1/kb-tags` — list/create kb tag.
- `GET/PUT/DELETE /api/v1/kb-tags/{id}`.

### Node Tags
- `GET /api/v1/node-tags` — list node-level tags (filter by `entity_type`, `entity_id`).
- `POST /api/v1/node-tags` — attach tag to node.
- `DELETE /api/v1/node-tags/{id}` — detach.

## ML Stack

| Verb | Path | Description |
|------|------|-------------|
| GET/POST | `/api/v1/model-definitions` | List/create model architectures |
| GET/PUT/DELETE | `/api/v1/model-definitions/{id}` | CRUD |
| GET/POST | `/api/v1/trained-models` | List/register trained model artifact |
| GET/PUT/DELETE | `/api/v1/trained-models/{id}` | CRUD |
| GET/POST | `/api/v1/training-runs` | List/start a training run |
| GET | `/api/v1/training-runs/{id}` | Run detail (status, metrics) |
| POST | `/api/v1/training-runs/{id}/cancel` | Cancel run |
| GET/POST | `/api/v1/ml-datasets` | Dataset CRUD |
| GET/PUT/DELETE | `/api/v1/ml-datasets/{id}` | CRUD |
| GET | `/api/v1/ml/layer-schemas` | Available NN layer schemas |
| POST | `/api/v1/onnx/import` | Import ONNX model file |
| GET | `/api/v1/onnx/{id}/metadata` | ONNX inspection |
| GET/POST | `/api/v1/images` | User image-staging (upload/list) |
| GET/DELETE | `/api/v1/images/{id}` | Get/delete staged image |

- **WS:** `GET /api/v1/ws/training/{runId}` — live training metrics (loss, lr, step, epoch).

## Pipelines

- `GET/POST /api/v1/pipelines` — list/create.
- `GET/PUT/DELETE /api/v1/pipelines/{id}`.
- `POST /api/v1/pipelines/{id}/run` — trigger; body `{input?:object}` → `{run_id, status}`.
- `GET /api/v1/pipelines/{id}/runs` — run history.

## Skills

- `GET/POST /api/v1/skills` — list/create skill.
- `GET/PUT/DELETE /api/v1/skills/{id}`.
- **Body:** `{name, description, definition:object, tags?:[string]}`. Skills compose tools/governors into reusable behaviors.

## Chatbots

- `GET/POST /api/v1/chatbots` — list/create chatbot flow.
- `GET/PUT/DELETE /api/v1/chatbots/{id}`.
- `POST /api/v1/chatbots/quick-create` — body `{prompt:string, knowledge_base_id?:uuid}` → fully-provisioned chatbot id.

## Budgets + Costs

- `GET/POST /api/v1/budgets` — list/create.
- `GET/PUT/DELETE /api/v1/budgets/{id}`.
- `GET /api/v1/costs` — aggregated cost rows; query `?from&to&group_by=agent|model|workflow`.
- `GET /api/v1/costs/{id}` — single cost record.

## Alerts + Notifications

- `GET/POST /api/v1/alerts` — list/create alert rule.
- `GET/PUT/DELETE /api/v1/alerts/{id}`.
- `POST /api/v1/alerts/{id}/test` — fire a synthetic alert.
- `GET/POST /api/v1/alert-escalation` — escalation policies.
- `GET/PUT/DELETE /api/v1/alert-escalation/{id}`.
- `GET /api/v1/notifications` — list user notifications.
- `POST /api/v1/notifications/{id}/ack` — acknowledge.
- **WS:** `GET /api/v1/ws/notifications` — live user notification fan-out.

## Compliance

- `GET /api/v1/compliance/rmf` — RMF (NIST Risk Management Framework) status.
- `GET/POST /api/v1/compliance/rmf/controls` — control catalog/state.
- `GET/POST /api/v1/compliance/reports` — compliance report generation/list.
- `GET /api/v1/compliance/reports/{id}` — fetch report (PDF/JSON).

## Webhooks

- `GET/POST /api/v1/webhooks` — list/create generic webhook subscriptions.
- `GET/PUT/DELETE /api/v1/webhooks/{id}`.
- `POST /api/v1/webhooks/servicenow` — ServiceNow inbound (signature-verified).
- `POST /api/v1/webhooks/cargonet` — CargoNet inbound (signature-verified).

## Dashboard

- `GET /api/v1/dashboard` — top-level summary.
- `GET /api/v1/dashboard/overview` — counts, health, recent runs.
- `GET /api/v1/dashboard/workflows` — workflow KPIs.
- `GET /api/v1/dashboard/agents` — agent KPIs.
- `GET /api/v1/dashboard/costs` — cost rollups.

## Integrations

- `GET /api/v1/integrations` — list installed integrations.
- `GET /api/v1/integrations/{type}` — get config (type = servicenow, slack, etc.).
- `PUT /api/v1/integrations/{type}` — set/update config.
- `POST /api/v1/integrations/{type}/test` — connectivity test.
- `GET/POST /api/v1/integrations/{type}/actions` — available actions / invoke action.
- `POST /api/v1/integrations/{type}/actions/{action}` — invoke specific action.

## Inbound Sources

- `GET/POST /api/v1/inbound-sources` — list/create.
- `GET/PUT/DELETE /api/v1/inbound-sources/{id}`.
- `POST /api/v1/inbound-sources/{id}/activate` — start polling/listening.
- `POST /api/v1/inbound-sources/{id}/pause` — pause.
- `POST /api/v1/inbound-sources/{id}/test` — synthetic ingest.
- `GET /api/v1/inbound-sources/{id}/status` — last poll state.
- **Body:** `{name, source_type:manual|http_poll|email|webhook, config:object, status:active|paused|error|disabled}`.

## LLM Models

- `GET/POST /api/v1/llm-models` — list/create.
- `GET/PUT/DELETE /api/v1/llm-models/{id}`.
- `POST /api/v1/llm-models/{id}/set-default` — mark as default for the workspace.
- **Body:** `{name, provider:string, model:string, max_tokens:int, capabilities:[string], credential_id:uuid, default?:bool}`.

## Chat

- `GET/POST /api/v1/chat/sessions` — list/create session.
- `GET/PATCH/DELETE /api/v1/chat/sessions/{id}`.
- `GET/POST /api/v1/chat/sessions/{id}/messages` — message history / send message.
- **WS:** `GET /api/v1/ws/chat/{sessionId}` — bidirectional chat with `chat_event_type`: `message|stream_token|narration|approval_request|approval_response|error`.

## Credentials

- `GET/POST /api/v1/credentials` — list/create.
- `GET/PUT/DELETE /api/v1/credentials/{id}`.
- `POST /api/v1/credentials/{id}/test` — verify the credential against its provider.
- **Body:** `{name, type:api_key|oauth2|basic_auth|bearer_token|custom, secret:object, metadata?:object}`. Secrets are write-only — `GET` returns redacted values.

## Traces

- `GET /api/v1/traces` — list traces (query `?entity_type=&entity_id=&from=&to=`, cursor paged).
- `GET /api/v1/traces/{traceId}` — trace summary.
- `GET /api/v1/traces/{traceId}/tree` — span tree.
- `GET /api/v1/traces/{traceId}/spans/{spanId}` — span detail.
- **WS:** `GET /api/v1/ws/traces/monitor` — live trace event firehose (filterable by `?entity_type=&entity_id=`).

## Export / Import

- `POST /api/v1/export` — body `{scope:entity|dependencies|environment, ids?:[uuid], filters?:object}` → `{bundle_url, expires_at}` or inline JSON.
- `POST /api/v1/import` — multipart bundle or JSON body `{bundle:object, conflict_strategy:skip|overwrite|rename}` → `{imported:[...], skipped:[...], errors:[...]}`.

## Swagger

- `GET /api/v1/docs` — Swagger UI.
- `GET /api/v1/docs/doc.json` — OpenAPI 3.0 spec (machine-readable).

_Regenerated from `railyard/internal/api/router.go` on 2026-04-30._
