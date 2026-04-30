---
description: Show overview of all Railyard platform entities — agents, tools, governors, workflows, credentials, documents, memories, chat sessions, knowledge bases, integrations, inbound sources, LLM models
allowed-tools: [Bash, Read]
---

# Railyard Status

Show a comprehensive overview of all deployed Railyard entities.

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-railyard/SKILL.md` for API configuration.

## Verify Auth

Ensure valid JWT token. If not: "Run /railyard:auth first."

## Gather Data

Run all queries in parallel:

```bash
RAILYARD_URL="${RAILYARD_URL:-http://localhost:38080}"

# Dashboard stats
STATS=$(curl -s "${RAILYARD_URL}/api/v1/dashboard/stats" \
  -H "Authorization: Bearer ${TOKEN}")

# Agents
AGENTS=$(curl -s "${RAILYARD_URL}/api/v1/agents?limit=50" \
  -H "Authorization: Bearer ${TOKEN}")

# Tools
TOOLS=$(curl -s "${RAILYARD_URL}/api/v1/tools?limit=50" \
  -H "Authorization: Bearer ${TOKEN}")

# Governors
GOVS=$(curl -s "${RAILYARD_URL}/api/v1/governors?limit=50" \
  -H "Authorization: Bearer ${TOKEN}")

# Workflows
WORKFLOWS=$(curl -s "${RAILYARD_URL}/api/v1/workflows?limit=50" \
  -H "Authorization: Bearer ${TOKEN}")

# Credentials
CREDS=$(curl -s "${RAILYARD_URL}/api/v1/credentials?limit=50" \
  -H "Authorization: Bearer ${TOKEN}")

# Documents
DOCS=$(curl -s "${RAILYARD_URL}/api/v1/documents?limit=50" \
  -H "Authorization: Bearer ${TOKEN}")

# Memories
MEMORIES=$(curl -s "${RAILYARD_URL}/api/v1/memories/stats" \
  -H "Authorization: Bearer ${TOKEN}")

# Chat Sessions
CHATS=$(curl -s "${RAILYARD_URL}/api/v1/chat/sessions" \
  -H "Authorization: Bearer ${TOKEN}")

# Knowledge Bases
KBS=$(curl -s "${RAILYARD_URL}/api/v1/knowledge-bases?limit=50" \
  -H "Authorization: Bearer ${TOKEN}")

# Integrations
INTEGRATIONS=$(curl -s "${RAILYARD_URL}/api/v1/integrations" \
  -H "Authorization: Bearer ${TOKEN}")

# Inbound Sources
INBOUND=$(curl -s "${RAILYARD_URL}/api/v1/inbound-sources?limit=50" \
  -H "Authorization: Bearer ${TOKEN}")

# LLM Models
MODELS=$(curl -s "${RAILYARD_URL}/api/v1/llm-models?limit=50" \
  -H "Authorization: Bearer ${TOKEN}")
```

## Output Format

```
# Railyard Platform Status

## Overview
| Metric | Count |
|--------|-------|
| Agents | N (M active) |
| Tools | N |
| Governors | N (M running) |
| Workflows | N (M active) |
| Credentials | N |
| Documents | N |
| Memories | N |
| Chat Sessions | N |
| Knowledge Bases | N |
| Integrations | N (M connected) |
| Inbound Sources | N (M active) |
| LLM Models | N |

## Agents
| Name | Module | Status | Tools | Success Rate |
|------|--------|--------|-------|-------------|
| agent-a | chain_of_thought | active | 3 | 95% |
| agent-b | react | paused | 1 | — |

## Tools
| Name | Method | Category | Active |
|------|--------|----------|--------|
| json-validator | python | validation | yes |

## Governors
| Name | Status | Stateful | Rules | Streams |
|------|--------|----------|-------|---------|
| rate-limiter | running | yes | 3 | 2 |

## Workflows
| Name | Active | Steps | Last Execution |
|------|--------|-------|----------------|
| cve-pipeline | yes | 5 | success (2m ago) |

## Credentials
| Name | Type | Provider | Active |
|------|------|----------|--------|
| openai-key | api_key | openai | yes |

## Documents
| Title | Type | Chunks | Embeddings |
|-------|------|--------|------------|
| policy-doc | text | 24 | yes |

## Memories
| Type | Count | Avg Importance |
|------|-------|----------------|
| fact | 15 | 0.7 |
| experience | 8 | 0.5 |

## Chat Sessions
| Title | Agent | Status | Last Message |
|-------|-------|--------|-------------|
| CVE Discussion | cve-analyst | active | 5m ago |

## Knowledge Bases
| Name | Visibility | Tags | Documents |
|------|-----------|------|-----------|
| sop-kb | private | [ops] | 12 |

## Integrations
| Name | Type | Status | Enabled |
|------|------|--------|---------|
| ServiceNow | servicenow | connected | yes |

## Inbound Sources
| Name | Type | Status | Requests |
|------|------|--------|----------|
| snow-poller | http_poll | active | 47 |

## LLM Models
| Name | Provider | Model ID | Default | Active |
|------|----------|----------|---------|--------|
| GPT-4o | openai | gpt-4o | yes | yes |
```
