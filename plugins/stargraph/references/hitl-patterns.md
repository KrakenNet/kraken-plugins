# Human-in-the-Loop Patterns

How a Stargraph run pauses for human input or approval, and how to resume it.

## When a run pauses

A run enters `awaiting-input` when an **interrupt** fires. Dispatch happens on
`Action.kind == "interrupt"` (or an `interrupt` node) **before** routing is
translated — it is a control-flow primitive, not a routing decision. The runtime
checkpoints, marks the run awaiting input, and emits a `WaitingForInputEvent`
carrying the prompt, the `interrupt_payload`, and the `requested_capability`.

The run stays resumable from its last checkpoint until the operator either
responds or the wait times out.

## Authoring a pause point

### `interrupt` node

```yaml
nodes:
  - id: analyst_gate
    kind: interrupt
    config:
      prompt: "Approve disposition {disposition} for alert {alert_id}?"
      requested_capability: "runs:respond"
      interrupt_payload:
        requested_capability: "runs:respond"
      timeout: "PT900S"        # ISO-8601 duration; null = no timeout
      on_timeout: "halt"       # "halt" (terminal) or "goto:<node_id>"
```

The `prompt` is interpolated against state at pause time and surfaced on the
`WaitingForInputEvent`.

### `interrupt` rule action

The same primitive is available as a `RuleSpec.then` action, so a routing rule
can pause the run when a condition matches:

```yaml
rules:
  - id: r-analyst-gate
    when: "?n <- (node-id (id analyst_gate))"
    then:
      - kind: interrupt
        prompt: "Approve disposition {disposition} for alert {alert_id}?"
        interrupt_payload:
          requested_capability: "runs:respond"
        requested_capability: "runs:respond"
        timeout: null
        on_timeout: "halt"
```

| Field | Type | Default | Purpose |
|---|---|---|---|
| `prompt` | `str` | required | Operator-facing prompt on the wait event. |
| `interrupt_payload` | `dict` | `{}` | Free-form payload echoed on the wait event. |
| `requested_capability` | `str \| None` | `None` | Capability gate for `POST /v1/runs/{id}/respond`. |
| `timeout` | `timedelta \| None` | `None` | Wait bound; `None` means no timeout. |
| `on_timeout` | `"halt" \| "goto:<node_id>"` | `"halt"` | Terminal halt, or resume at a node. |

## Responding

Resume a paused run by delivering a response to its `respond` endpoint. The
caller must hold the interrupt's `requested_capability` (e.g. `runs:respond`).

### `stargraph respond` (CLI)

A thin wrapper over `POST /v1/runs/{run_id}/respond` on a running
`stargraph serve` process:

```bash
stargraph respond <RUN_ID> --response analyst-decision.json --actor alice
```

| Flag | Required | Description |
|---|---|---|
| `RUN_ID` | yes | Run id that is `awaiting-input`. |
| `--response FILE` | yes | JSON file with the analyst response payload. |
| `--actor NAME` | yes | Principal id; sent as `Authorization: Bypass <actor>`. |
| `--server URL` | no | Base URL of the serve process (default `http://localhost:8000`). |

The CLI maps HTTP errors to operator-friendly messages: `200` prints the
`RunSummary` JSON; `401` = auth failed for actor; `404` = run not found or not
awaiting input; `409` = run not awaiting input (already responded or in a
conflicting state).

### Direct HTTP

```bash
curl -fsS -X POST "http://localhost:8000/v1/runs/${RID}/respond" \
  -H "Authorization: Bypass alice" \
  -H "Content-Type: application/json" \
  -d @analyst-decision.json
```

## Audit trail

The response is sealed into the run's provenance trail. Provenance carries the
documented origin values (`tool`, `llm`, `rule`, `system`); the responding
actor is recorded from the `Authorization: Bypass <actor>` principal. The
`stargraph.bosun.audit` pack signs transition facts so the resume action is
non-repudiable. See `references/provenance-facts.md`.

## Cleared / air-gapped deployments

- Every responder is identified by the `--actor` principal, which becomes the
  recorded actor on the response.
- The serve process writes to the JSONL audit log (see `stargraph serve
  --audit-log`), so the operator action is recorded.
- Inspect what a paused run was waiting on, and the state at the pause, with
  `stargraph inspect RUN_ID --db DB --step N`.

## Common patterns

- **Finite wait for hot-resume**: set a finite `timeout` (e.g. `PT900S`) so the
  serve loop takes its hot-resume path — `POST /v1/runs/{id}/respond` wakes the
  same live loop, which advances past the gate. `on_timeout: "halt"` keeps an
  unanswered gate terminal, not hung.
- **Resume-to-node**: `on_timeout: "goto:<node_id>"` resumes at a fallback node
  instead of halting when the operator never responds.
- **Capability-scoped approvals**: set `requested_capability` so only principals
  holding that capability can respond — the gate runs on the `respond` endpoint
  before the run resumes.
