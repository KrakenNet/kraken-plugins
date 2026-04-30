---
description: Manage Railyard webhooks — generic, ServiceNow, CargoNet — via /api/v1/webhooks*
argument-hint: [generic|servicenow|cargonet] [list|register|test|delete] [id?]
allowed-tools: [Bash, Read, AskUserQuestion]
---

# Railyard Webhooks

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-railyard/SKILL.md`.

## Verify Auth

Standard.

## Endpoints

- `/api/v1/webhooks` — generic.
- `/api/v1/webhooks/servicenow` — SN-specific.
- `/api/v1/webhooks/cargonet` — CargoNet-specific.

## Routes

### register (generic)

Interview: url, events (list), secret (HMAC), inbound_source_id?.

### test

```bash
curl -s -X POST "${RAILYARD_URL}/api/v1/webhooks/<id>/test" -H "Authorization: Bearer ${TOKEN}"
```

### list/delete — standard.

### servicenow / cargonet

These are inbound webhooks Railyard listens on. Show their URLs + auth model; verify they're enabled.

## Report

URL + enabled status + last delivery.
