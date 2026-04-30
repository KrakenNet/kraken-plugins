---
description: Manage LLM model configurations — providers, token limits, capabilities, and defaults
argument-hint: [create|list|set-default]
allowed-tools: [Bash, Read, AskUserQuestion]
---

# Railyard LLM Model Management

Configure LLM models available to agents on the platform.

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-railyard/SKILL.md` for API conventions and auth flow.

## Verify Auth

Ensure valid JWT token. If not: "Run /railyard:auth first."

## Parse Arguments

From `$ARGUMENTS`:
- **Action**: `list` (default), `create`, `set-default`

## Route by Action

### List (default)

```bash
curl -s "${RAILYARD_URL}/api/v1/llm-models?limit=50" \
  -H "Authorization: Bearer ${TOKEN}" | jq '.data[] | {id, name, provider, model_id, is_default, is_active, supports_tools, supports_vision}'
```

### Create

Interview:

1. **"Model name?"** (display name, e.g., "GPT-4o" or "Claude Sonnet")

2. **"Provider?"** (e.g., openai, anthropic, ollama, azure, bedrock)

3. **"Model ID?"** (provider-specific ID, e.g., "gpt-4o", "claude-sonnet-4-20250514")

4. **"Base URL?"** (optional — for custom endpoints, Ollama, Azure, etc.)

5. **"Max tokens?"** (optional — token limit for this model)

6. **"Default temperature?"** (optional — 0.0-2.0)

7. **"Does this model support tool calling?"** (yes/no)

8. **"Does this model support vision/images?"** (yes/no)

9. **"Link a credential for API access?"**
   - List credentials: `GET /api/v1/credentials?limit=50`
   - User picks or skips

10. **"Set as platform default?"** (yes/no)

11. **"Any additional config?"** (optional JSON for provider-specific settings)

Execute:
```bash
curl -s -X POST "${RAILYARD_URL}/api/v1/llm-models" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "...",
    "provider": "...",
    "model_id": "...",
    "base_url": "...",
    "max_tokens": N,
    "default_temperature": 0.7,
    "supports_tools": true,
    "supports_vision": false,
    "credential_id": "uuid",
    "is_default": false,
    "is_active": true,
    "config": {}
  }'
```

### Set Default

1. List models: `GET /api/v1/llm-models?limit=50`
2. **"Which model should be the default?"**

```bash
curl -s -X POST "${RAILYARD_URL}/api/v1/llm-models/${ID}/set-default" \
  -H "Authorization: Bearer ${TOKEN}"
```

## Report

Show the output to the user.
