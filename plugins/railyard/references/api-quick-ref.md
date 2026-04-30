# Railyard API Quick Reference

Base: `${RAILYARD_URL:-http://localhost:38080}/api/v1`
Auth: `Authorization: Bearer ${TOKEN}`

## Entities at a Glance

| Entity | Create | List | Get | Update | Delete | Test/Execute |
|--------|--------|------|-----|--------|--------|-------------|
| Credential | POST /credentials | GET /credentials | GET /credentials/{id} | PUT /credentials/{id} | DELETE /credentials/{id} | POST /credentials/{id}/test |
| Agent | POST /agents | GET /agents | GET /agents/{id} | PUT /agents/{id} | DELETE /agents/{id} | POST /agents/{id}/execute |
| Tool | POST /tools | GET /tools | GET /tools/{id} | PUT /tools/{id} | DELETE /tools/{id} | POST /tools/{id}/test |
| Governor | POST /governors | GET /governors | GET /governors/{id} | PUT /governors/{id} | DELETE /governors/{id} | POST /governors/{id}/test |
| Workflow | POST /workflows | GET /workflows | GET /workflows/{id} | PUT /workflows/{id} | DELETE /workflows/{id} | POST /workflows/{id}/execute |
| Document | POST /documents | GET /documents | GET /documents/{id} | PUT /documents/{id} | DELETE /documents/{id} | POST /documents/search |
| Memory | POST /memories | GET /memories | GET /memories/{id} | PUT /memories/{id} | DELETE /memories/{id} | POST /memories/search |
| Chat Session | POST /chat/sessions | GET /chat/sessions | GET /chat/sessions/{id} | PATCH /chat/sessions/{id} | DELETE /chat/sessions/{id} | — |
| Knowledge Base | POST /knowledge-bases | GET /knowledge-bases | GET /knowledge-bases/{id} | PUT /knowledge-bases/{id} | DELETE /knowledge-bases/{id} | — |
| Integration | — | GET /integrations | GET /integrations/{type} | PUT /integrations/{type} | — | POST /integrations/{type}/test |
| Inbound Source | POST /inbound-sources | GET /inbound-sources | GET /inbound-sources/{id} | PUT /inbound-sources/{id} | DELETE /inbound-sources/{id} | POST /inbound-sources/{id}/test |
| LLM Model | POST /llm-models | GET /llm-models | GET /llm-models/{id} | PUT /llm-models/{id} | DELETE /llm-models/{id} | POST /llm-models/{id}/set-default |

## Governor Sub-resources (under /governors/{id}/)

rules, facts, facts/runtime, streams, routes, snapshots, start, stop, status, trace

## Workflow Sub-resources (under /workflows/{id}/)

stages, stages/{stageId}/steps, executions, execute, duplicate

## Agent Sub-resources (under /agents/{id}/)

tools, governors, demonstrations, sessions, trace, execute, execute/batch, monitor, memory-sources, credentials, knowledge-bases, mcp

## Governor Sub-resources (under /governors/{id}/)  — additional

validate, monitor, ws

## Chat Sub-resources (under /chat/sessions/{id}/)

messages

## Knowledge Base Sub-resources (under /knowledge-bases/{id}/)

acls, tags

## Integration Sub-resources (under /integrations/{type}/)

test, actions, actions/{action}

## Inbound Source Actions

activate, pause, test

## Export/Import

POST /export, POST /import

## Traces (under /traces/)

?entity_type=X&entity_id=Y, {traceId}/tree, {traceId}/spans/{spanId}

## KG (under /knowledge-graph/)

nodes, edges, nodes/{id}/neighbors, search, entities/extract, entities/entities, entities/aliases, summaries/generate, summaries, communities/detect, communities

## Enums

- dspy_module: predict, chain_of_thought, react, multi_chain_comparison, refine, parallel, rlm
- step_type: agent_call, tool_call, governor_check, human_approval
- credential_type: api_key, oauth2, basic_auth, bearer_token, custom
- stream_type: http, kafka, memory, webhook
- routing_operator: equals, contains, startsWith, endsWith, regex, greaterThan, lessThan
- source_type: manual, http_poll, email, webhook
- inbound_status: active, paused, error, disabled
- integration_status: connected, disconnected, error
- chat_message_role: user, assistant, system, narration, tool
- chat_event_type: message, stream_token, narration, approval_request, approval_response, error
- kb_visibility: private, shared
- export_scope: entity, dependencies, environment
