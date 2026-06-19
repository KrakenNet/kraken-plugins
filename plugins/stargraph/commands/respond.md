---
description: Respond to a paused (HITL) Stargraph run — supply human input, resume
argument-hint: <run_id> --response <json> --actor <name> [--server <url>]
allowed-tools: [Bash, Read, AskUserQuestion]
---

# Stargraph Respond

Deliver a HITL response to a run that is `awaiting-input` (paused at an
`interrupt` / `human_input` node). `stargraph respond` is a thin wrapper over
`POST /v1/runs/{run_id}/respond` on a running `stargraph serve`.

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-stargraph/SKILL.md` and
`${CLAUDE_PLUGIN_ROOT}/references/hitl-patterns.md`.

## Verify Pause

The run must be awaiting input. `GET /v1/runs/{id}` folds that lifecycle state
onto `paused`; refuse unless the run is paused:

```bash
SERVER="${SERVER:-http://localhost:8000}"
STATUS=$(curl -fsS "${SERVER}/v1/runs/${RID}" \
  -H "Authorization: Bypass ${ACTOR}" | jq -r .status)
[[ "$STATUS" == "paused" ]] || { echo "not awaiting input (status=$STATUS)"; exit 2; }
```

Show the user the pending prompt and the requested capability before asking for
their response.

## Parse Arguments

- `--response <json>`: path to a JSON file with the analyst response payload (required).
- `--actor <name>`: principal id; sent as `Authorization: Bypass <actor>` (required).
- `--server <url>`: base URL of the running `stargraph serve` (default `http://localhost:8000`).

If args are missing, prompt with AskUserQuestion. Build the response JSON file,
then submit:

## Run

```bash
uv run stargraph respond "${RID}" \
  --response analyst-decision.json \
  --actor "${ACTOR}" \
  --server "${SERVER:-http://localhost:8000}"
```

The CLI maps HTTP status to operator-friendly messages: `200` prints the
`RunSummary` JSON; `401` = auth failed; `404` = run not found or not awaiting
input; `409` = not awaiting input (already responded / conflicting state).

## Report

- New status from the returned `RunSummary` (`running` / `done` / `paused`)
- The response payload delivered, the actor, and the run id
- Stream URL to follow: `http://localhost:8000/v1/runs/${RID}/stream`
