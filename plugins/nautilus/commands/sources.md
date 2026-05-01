---
description: List Nautilus sources, enable/disable a source at runtime (P0 issue)
argument-hint: [list|enable|disable] [<id>] [--reason "..."]
allowed-tools: [Bash, Read, AskUserQuestion]
---

# Nautilus Sources

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-nautilus/SKILL.md`.

## Verify Broker

Standard.

## Routes

### list (default)

```bash
curl -s "${NAUTILUS_URL}/v1/sources" -H "Authorization: Bearer ${NAUTILUS_TOKEN}" | jq '.data[] | {id, enabled, reason, actor, changed_at}'
```

### enable <id>

```bash
curl -s -X POST "${NAUTILUS_URL}/v1/sources/<id>/enable" -H "Authorization: Bearer ${NAUTILUS_TOKEN}"
```

### disable <id>

Confirm with AskUserQuestion. Require `--reason`. Then:

```bash
curl -s -X POST "${NAUTILUS_URL}/v1/sources/<id>/disable" -H "Authorization: Bearer ${NAUTILUS_TOKEN}" -H "Content-Type: application/json" -d '{"reason":"..."}'
```

## Verify

Re-GET `/v1/sources`; confirm new state.

## Report

Markdown table; bold the changed row.
