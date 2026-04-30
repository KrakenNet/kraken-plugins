---
description: Fetch Railyard dashboard summary metrics from /api/v1/dashboard
argument-hint: [overview|workflows|agents|costs]
allowed-tools: [Bash, Read]
---

# Railyard Dashboard

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-railyard/SKILL.md`.

## Verify Auth

Standard.

## Endpoint

`/api/v1/dashboard`

## Routes

```bash
curl -s "${RAILYARD_URL}/api/v1/dashboard/<section>" -H "Authorization: Bearer ${TOKEN}" | jq '.data'
```

Sections: overview (default), workflows, agents, costs.

## Report

Render as a tight table; flag any red counters (errors, breached budgets).
