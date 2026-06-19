---
description: Driver for human-in-the-loop pauses — finds awaiting-input runs, presents the interrupt prompt + requested capability, gathers a response, and resumes via /respond.
tools: [Bash, Read, AskUserQuestion]
---

# HITL Driver

A graph pauses when an `interrupt` node fires (or a rule emits an `interrupt`
action). The pause emits a `WaitingForInputEvent` carrying the operator
`prompt`, the free-form `interrupt_payload`, and the `requested_capability`
the responder must hold. The run sits at status `awaiting-input` until a human
POSTs to `/v1/runs/{run_id}/respond`; the response is injected as a `respond`
fact (`origin="user", source=<actor>`).

## Inputs

- `run_id` (optional). If omitted, list awaiting-input runs and pick interactively.

## Steps

1. List candidates: `GET /v1/runs?status=awaiting-input` (filterable list;
   default base URL `http://localhost:8000`). Note `run_id` + prompting node.
2. For the chosen `run_id`:
   - `GET /v1/runs/${run_id}` — pull the `RunSummary` and the pending
     `WaitingForInputEvent` (`prompt`, `interrupt_payload`,
     `requested_capability`, optional `timeout` / `on_timeout`).
   - Inspect the facts that led to the pause if a checkpoint DB is available:
     `stargraph inspect ${run_id} --db ./.stargraph/run.sqlite --diff N M`.
   - Render a compact summary (≤30 lines) so the user can decide.
3. Ask the user (AskUserQuestion) for the response payload. Confirm the actor
   id and that the actor holds `requested_capability` (the `/respond` route is
   gated on `runs:respond`; the gate denies with a `capability_denied` audit
   event + 403 if the actor lacks the capability).
4. Submit the response. Either:
   - CLI: `stargraph respond ${run_id} --response decision.json --actor alice
     --server http://localhost:8000` (writes `Authorization: Bypass <actor>`).
   - Direct: `POST /v1/runs/${run_id}/respond` with body `{response, actor}`.
5. Confirm resume: stream `WS /v1/runs/${run_id}/stream`, or poll
   `GET /v1/runs/${run_id}` until status leaves `awaiting-input`.

## Build-Test-Fix

3 iters. HTTP errors map to operator-friendly cases: `401` auth failed for
actor; `404` run not found or not awaiting input; `409` run not awaiting input
(already responded / conflicting state). On `409`/`404`, re-list awaiting-input
runs rather than retrying blindly. If `on_timeout` already fired (`halt` or
`goto:<node>`), report that the gate is no longer answerable.

## Report

- run_id, actor, response payload.
- New status; node about to run; or terminal `result` if the run completed.
