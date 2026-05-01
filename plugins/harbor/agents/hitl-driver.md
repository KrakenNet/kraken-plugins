---
description: Driver for human-in-the-loop pauses — fetches paused runs, presents context, validates payload against schema, calls /respond.
tools: [Bash, Read, AskUserQuestion]
---

# HITL Driver

## Inputs

- `run_id` (optional). If omitted, list all `PAUSED_HITL` runs and pick interactively.

## Steps

1. `GET /v1/runs?status=PAUSED_HITL` — list candidates with `paused_at`,
   `pause_reason`, and the prompting node.
2. For the chosen `run_id`:
   - `GET /v1/runs/${run_id}` — pull `prompt`, `policy_reason`,
     `expected_input_schema`, plus the last 3 facts emitted before the pause.
   - Render a compact summary (no more than 30 lines) so the user can decide.
3. Ask the user:
   - decision (`approve` / `deny` / `input`)
   - payload (only for `input` — must match `expected_input_schema`)
   - reason (required for `deny`)
4. Validate payload locally with `jsonschema` before submitting.
5. `POST /v1/runs/${run_id}/respond` with the response body.
6. Stream `/v1/runs/${run_id}/stream` until status leaves `RUNNING` or 30s elapse.

## Build-Test-Fix

3 iters. On schema validation failure, surface the offending JSON-pointer path
to the user and re-prompt — do not retry blindly.

## Report

- run_id, decision, audit fact
- New status; node about to run; or terminal `result` if the run completed
