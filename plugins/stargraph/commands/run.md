---
description: Execute a Stargraph graph; stream events; return run_id
argument-hint: <graph> [-i K=V]... [--inspect]
allowed-tools: [Bash, Read, AskUserQuestion, Task]
---

# Stargraph Run

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-stargraph/SKILL.md`.

## Run

`<graph>` is a path to an IR YAML file (commonly `<graphdir>/stargraph.yaml`).
Seed initial state with `-i K=V` (repeatable; each key must match the IR
`state_schema`). The graph runs against a SQLite checkpointer (default
`./.stargraph/run.sqlite`).

```bash
uv run stargraph run "<graph>" \
  -i message="check pack drift" -i severity=3 \
  --checkpoint ./.stargraph/run.sqlite \
  --log-file ./.stargraph/run.jsonl \
  --summary-json
```

To preview routing without executing any node (rule-firing trace only), add
`--inspect`:

```bash
uv run stargraph run "<graph>" --inspect
```

Exit code is `0` on a terminal `done`, non-zero on `failed`. Bind a local LLM
for `dspy` nodes with `--lm-url URL --lm-model NAME` (supplied together) plus
optional `--lm-key`/`--lm-timeout`. Use `--quiet`/`--verbose` for output
volume and `--non-interactive` to fail rather than prompt on a HITL pause.

## Driving a running server

If a `stargraph serve` process is up, start the run over HTTP instead — the
graph's `id` (e.g. `graph:triage`) is the key:

```bash
RUN=$(curl -fsS -X POST "http://localhost:8000/v1/runs" \
  -H "Authorization: Bypass operator" \
  -H "Content-Type: application/json" \
  -d '{"graph_id":"graph:triage","params":{}}' | jq -r '.run_id')

# Tail events over the WebSocket stream
websocat "ws://localhost:8000/v1/runs/$RUN/stream"
```

`POST /v1/runs` returns `202` with `{run_id, status:"pending"}`; poll
`GET /v1/runs/$RUN` for terminal state.

## Delegate

Task tool → `runner` for deeper polling/parsing.

## Report

run_id, current state, last 5 events.
