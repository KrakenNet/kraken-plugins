---
description: Execute a Stargraph graph against `stargraph serve`; stream events; return run_id
argument-hint: <graph> [--input-file <json>]
allowed-tools: [Bash, Read, AskUserQuestion, Task]
---

# Stargraph Run

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-stargraph/SKILL.md`.

## Verify Server

`GET ${STARGRAPH_URL}/health`. `GET /v1/graphs` — confirm graph is registered.

## Run

```bash
RUN=$(curl -s -X POST "${STARGRAPH_URL}/v1/runs" \
  -H "Authorization: Bearer ${STARGRAPH_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"graph\":\"<graph>\", \"input\": $(cat <input-file>)}" | jq -r '.data.run_id')
```

Optionally tail events via WS:

```bash
websocat -H "Authorization: Bearer ${STARGRAPH_TOKEN}" "${STARGRAPH_URL/http/ws}/v1/runs/$RUN/events"
```

## Delegate

Task tool → `runner` for deeper polling/parsing.

## Report

run_id, current state, last 5 events.
