---
description: Start `stargraph serve` (FastAPI HTTP+WebSocket daemon) with a chosen profile
argument-hint: [--profile dev|prod|cleared] [--port <n>] [--host <addr>]
allowed-tools: [Bash, Read, AskUserQuestion]
---

# Stargraph Serve

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-stargraph/SKILL.md`.

## Parse Arguments

- `--profile` ∈ {`dev`, `prod`, `cleared`} — default `dev`. Cleared profile assumes air-gapped, signed-only artifacts, no telemetry.
- `--port` — default `9000`.
- `--host` — default `127.0.0.1`. Use `0.0.0.0` only when the user explicitly asks for it.

If a `stargraph` process already listens on `${STARGRAPH_URL}/health`, abort and report.

## Run

```bash
STARGRAPH_PROFILE="${PROFILE:-dev}" \
  uv run stargraph serve \
    --host "${HOST:-127.0.0.1}" \
    --port "${PORT:-9000}"
```

Run in background only if the user asked for it (`run_in_background: true`). Otherwise stream the boot output for ~3 seconds, then check:

```bash
curl -fsS "${STARGRAPH_URL}/health" | jq .
curl -fsS "${STARGRAPH_URL}/v1/graphs" | jq '.data | length'
```

## Report

- Profile, host:port, PID
- Number of registered graphs
- WebSocket endpoint: `${STARGRAPH_URL}/v1/runs/<id>/stream`
- Stop hint: `kill <PID>` or Ctrl-C in the foreground shell
