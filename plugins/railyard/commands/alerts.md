---
description: Manage Railyard alerts, alert escalations, and notifications via /api/v1/alerts, /api/v1/alert-escalation, /api/v1/notifications
argument-hint: [alerts|escalation|notifications] [list|get|create|ack|resolve|delete] [id?]
allowed-tools: [Bash, Read, AskUserQuestion]
---

# Railyard Alerts and Notifications

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-railyard/SKILL.md`.

## Verify Auth

Standard.

## Resources

- `/api/v1/alerts` — alert rules + active alerts.
- `/api/v1/alert-escalation` — escalation chains.
- `/api/v1/notifications` — notification routing.

## Routes

### alerts create

Interview: name, severity (info|warn|error|critical), condition (CLIPS-style facts), notify_channels.

### alerts ack <id>

```bash
curl -s -X POST "${RAILYARD_URL}/api/v1/alerts/<id>/ack" -H "Authorization: Bearer ${TOKEN}"
```

### alerts resolve <id>

POST `/resolve` similar pattern.

### escalation create

Interview: alert_id, levels (list of {after_seconds, channel}).

### notifications list/get/delete — standard CRUD.

## WS

Pointer to `/api/v1/ws/notifications` — see `smart-railyard` for WS streaming helper.

## Report

Table of alerts with severity, status, last triggered.
