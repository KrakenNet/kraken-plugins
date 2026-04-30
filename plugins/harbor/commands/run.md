---
description: Execute a Harbor graph against `harbor serve`; stream events; return run_id
argument-hint: <graph> [--input-file <json>]
allowed-tools: [Bash, Read, AskUserQuestion, Task]
---

# Harbor Run

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-harbor/SKILL.md`.

## Verify Server

`GET ${HARBOR_URL}/health`. `GET /v1/graphs` — confirm graph is registered.

## Run

```bash
RUN=$(curl -s -X POST "${HARBOR_URL}/v1/runs" \
  -H "Authorization: Bearer ${HARBOR_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"graph\":\"<graph>\", \"input\": $(cat <input-file>)}" | jq -r '.data.run_id')
```

Optionally tail events via WS:

```bash
websocat -H "Authorization: Bearer ${HARBOR_TOKEN}" "${HARBOR_URL/http/ws}/v1/runs/$RUN/events"
```

## Delegate

Task tool → `runner` for deeper polling/parsing.

## Report

run_id, current state, last 5 events.
