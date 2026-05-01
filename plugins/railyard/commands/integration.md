---
description: Configure, enable, test, and manage external service integrations (ServiceNow, etc.)
argument-hint: [list|configure|test|execute] [--type servicenow|echo]
allowed-tools: [Bash, Read, AskUserQuestion, Task]
---

# Railyard Integration Management

Configure and manage external service integrations.

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-railyard/SKILL.md` for API conventions and auth flow.

## Verify Auth

Ensure valid JWT token. If not: "Run /railyard:auth first."

## Parse Arguments

From `$ARGUMENTS`:
- **Action**: `list` (default), `configure`, `test`, `execute`
- **--type**: Pre-select integration adapter type

## Route by Action

### List (default)

```bash
curl -s "${RAILYARD_URL}/api/v1/integrations" \
  -H "Authorization: Bearer ${TOKEN}" | jq '.data[] | {name, adapter_type, status, enabled, has_credential}'
```

### Configure

Interview:

1. List available integrations: `GET /api/v1/integrations`
2. **"Which integration to configure?"** (adapter_type)
3. Fetch integration details + settings schema: `GET /api/v1/integrations/{type}`
4. Walk through settings schema fields — ask user for each required setting
5. **"Link a credential?"**
   - List credentials: `GET /api/v1/credentials?limit=50`
   - User picks or skips
6. **"Enable this integration?"** (yes/no)

Delegate to `integration-builder` agent via Task tool with interview answers + TOKEN + RAILYARD_URL.

### Test

Interview:

1. List integrations: `GET /api/v1/integrations`
2. **"Which integration to test?"** (adapter_type)

Execute:
```bash
curl -s -X POST "${RAILYARD_URL}/api/v1/integrations/${TYPE}/test" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"settings": CURRENT_SETTINGS, "credential_id": "uuid or null"}'
```

### Execute

Interview:

1. List integrations: `GET /api/v1/integrations`
2. **"Which integration?"** (adapter_type)
3. List available actions: `GET /api/v1/integrations/{type}/actions`
4. **"Which action?"**
5. **"Input data?"** (JSON or guided entry)

Execute:
```bash
curl -s -X POST "${RAILYARD_URL}/api/v1/integrations/${TYPE}/actions/${ACTION}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"integration_id":"uuid","input":{...}}'
```

## Report

Show the output to the user.
