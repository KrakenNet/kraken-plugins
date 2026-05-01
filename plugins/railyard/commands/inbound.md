---
description: Configure inbound sources for multi-channel request ingestion (HTTP polling, webhooks, email)
argument-hint: [create|list|test|activate|pause] [--type manual|http_poll|email|webhook]
allowed-tools: [Bash, Read, AskUserQuestion, Task]
---

# Railyard Inbound Source Management

Configure multi-channel inbound sources to feed requests into workflows.

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-railyard/SKILL.md` for API conventions and auth flow.

## Verify Auth

Ensure valid JWT token. If not: "Run /railyard:auth first."

## Parse Arguments

From `$ARGUMENTS`:
- **Action**: `create` (default), `list`, `test`, `activate`, `pause`
- **--type**: Pre-select source type

## Route by Action

### List

```bash
curl -s "${RAILYARD_URL}/api/v1/inbound-sources?limit=50" \
  -H "Authorization: Bearer ${TOKEN}" | jq '.data[] | {id, name, source_type, status, requests_created, last_poll_at}'
```

### Create (default)

Interview:

1. **"What should this inbound source be called?"** (name)

2. **"Description?"** (optional)

3. **"Source type?"**
   - manual — Requests created manually or via API
   - http_poll — Poll an external URL on a schedule
   - webhook — Receive incoming webhooks
   - email — Monitor an email inbox

4. Type-specific questions:

   **http_poll:**
   - **"URL to poll?"** (poll_url)
   - **"HTTP method?"** (GET/POST, default GET)
   - **"Poll interval in seconds?"** (default 300)
   - **"Custom headers?"** (JSON, optional)
   - **"Credential for authentication?"** — list credentials if needed

   **webhook:**
   - **"Webhook path?"** (e.g., /webhooks/my-source)
   - **"Webhook secret for verification?"** (optional)

   **email:**
   - **"Email address to monitor?"**
   - **"Protocol?"** (IMAP/POP3)
   - **"Server and port?"**
   - **"Credential for email auth?"** — list credentials

5. **"Map incoming fields to request fields?"** (field_mapping JSON, optional)

6. **"Route to a specific request type?"**
   - List request types if available
   - Or skip for default routing

7. **"Default priority?"** (low/medium/high/critical, default medium)

Delegate to `inbound-source-builder` agent via Task tool with interview answers + TOKEN + RAILYARD_URL.

### Test

1. List sources: `GET /api/v1/inbound-sources?limit=50`
2. **"Which source to test?"**

```bash
curl -s -X POST "${RAILYARD_URL}/api/v1/inbound-sources/${ID}/test" \
  -H "Authorization: Bearer ${TOKEN}"
```

### Activate

1. List paused/disabled sources
2. **"Which source to activate?"**

```bash
curl -s -X POST "${RAILYARD_URL}/api/v1/inbound-sources/${ID}/activate" \
  -H "Authorization: Bearer ${TOKEN}"
```

### Pause

1. List active sources
2. **"Which source to pause?"**

```bash
curl -s -X POST "${RAILYARD_URL}/api/v1/inbound-sources/${ID}/pause" \
  -H "Authorization: Bearer ${TOKEN}"
```

## Report

Show the output to the user.
