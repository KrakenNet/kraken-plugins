---
description: POST /v1/request to a running Nautilus broker; show data, sources_queried, sources_denied, attestation
argument-hint: [--agent-id <id>] [--intent <text>] [--clearance <c>] [--purpose <p>] [--session-id <s>]
allowed-tools: [Bash, Read, AskUserQuestion, Task]
---

# Nautilus Request

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-nautilus/SKILL.md`.

## Verify Broker

`GET ${NAUTILUS_URL}/health`.

## Interview (if args missing)

agent_id, intent, clearance, purpose, session_id, optional fact_set_hash.

## Delegate

Task tool → `broker-driver`.

## Report

data summary + sources_queried + sources_denied + attestation snippet + audit_id + duration_ms.
