---
description: Start `stargraph serve` (FastAPI HTTP+WebSocket daemon) with a chosen profile
argument-hint: [--profile oss-default|cleared] [--port <n>] [--host <addr>]
allowed-tools: [Bash, Read, AskUserQuestion]
---

# Stargraph Serve

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-stargraph/SKILL.md`.

## Parse Arguments

- `--profile` ∈ {`oss-default`, `cleared`} — default `oss-default`. Under
  `cleared`, the startup gate refuses `--allow-pack-mutation` and
  `--allow-side-effects` and exits non-zero with a `ProfileViolationError`.
- `--port` — default `8000`.
- `--host` — default `127.0.0.1`. Use `0.0.0.0` only when the user explicitly asks for it.

If a `stargraph` process already listens on the chosen `--host:--port`, abort and report.

## Run

```bash
uv run stargraph serve \
  --profile "${PROFILE:-oss-default}" \
  --host "${HOST:-127.0.0.1}" \
  --port "${PORT:-8000}" \
  --db ./stargraph.sqlite \
  --audit-log ./audit.jsonl \
  --graph "<graphdir>/stargraph.yaml"
```

`--graph` is repeatable and loads + registers an IR YAML at boot; the graph's
`id` is the key `POST /v1/runs` uses. Bind a local LLM with
`--lm-url URL --lm-model NAME` (plus optional `--lm-key`/`--lm-timeout`).

Run in background only if the user asked for it (`run_in_background: true`).
Otherwise stream the boot output for ~3 seconds, then confirm the API is up by
listing graphs:

```bash
curl -fsS "http://localhost:8000/v1/graphs" \
  -H "Authorization: Bypass operator" | jq 'length'
```

## Report

- Profile, host:port, PID
- Number of registered graphs
- WebSocket endpoint: `http://localhost:8000/v1/runs/<id>/stream`
- Stop hint: `kill <PID>` or Ctrl-C in the foreground shell
