---
description: Manage Railyard cost budgets and inspect cost reports via /api/v1/budgets and /api/v1/costs
argument-hint: [budgets|costs] [list|get|create|update|delete|report] [id?]
allowed-tools: [Bash, Read, AskUserQuestion]
---

# Railyard Budgets and Costs

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-railyard/SKILL.md`.

## Verify Auth

Standard.

## Resources

- `/api/v1/budgets` — budget definitions.
- `/api/v1/costs` — cost reports.

## Routes

### budgets create

Interview: name, scope (global|agent|workflow|tool), limit_usd, period (daily|weekly|monthly), action (warn|block).

### budgets list/get/update/delete — standard CRUD.

### costs list — query params: scope, period, agent_id?, workflow_id?, from_ts?, to_ts?.

```bash
curl -s "${RAILYARD_URL}/api/v1/costs?scope=agent&agent_id=<id>&from_ts=<ts>" -H "Authorization: Bearer ${TOKEN}" | jq '.data'
```

### costs report

Renders a per-period table.

## Report

Table of budget vs. spend.
