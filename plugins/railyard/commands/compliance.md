---
description: Run RMF compliance checks and download compliance reports via /api/v1/compliance/rmf and /api/v1/compliance/reports
argument-hint: [rmf|reports] [list|get|run|download] [id?]
allowed-tools: [Bash, Read, AskUserQuestion]
---

# Railyard Compliance

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-railyard/SKILL.md`.

## Verify Auth

Standard.

## Resources

- `/api/v1/compliance/rmf` — Risk Management Framework checks.
- `/api/v1/compliance/reports` — compliance report artifacts.

## Routes

### rmf list/get — standard.

### rmf run

```bash
curl -s -X POST "${RAILYARD_URL}/api/v1/compliance/rmf/run" -H "Authorization: Bearer ${TOKEN}"
```

Then poll `/api/v1/compliance/rmf/<run_id>` until status=`completed`.

### reports list

```bash
curl -s "${RAILYARD_URL}/api/v1/compliance/reports?limit=20" -H "Authorization: Bearer ${TOKEN}" | jq '.data'
```

### reports download <id>

```bash
curl -s -o "report-<id>.pdf" "${RAILYARD_URL}/api/v1/compliance/reports/<id>/download" -H "Authorization: Bearer ${TOKEN}"
```

## Report

Status of last RMF run + table of recent reports.
