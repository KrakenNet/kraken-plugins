# Human-in-the-Loop Patterns

How a Harbor run pauses for human input or approval, and how to resume it.

## When a run pauses

A run enters `PAUSED_HITL` when one of these happens:

1. **`human_input` node** — a node whose `type: harbor.nodes.human_input`
   produces no value on its own; it just declares an `expected_input_schema`
   and a `prompt`. The runtime checkpoints, marks the run paused, and emits
   a `(hitl.required ...)` fact.
2. **Governance halt** — a Bosun rule emits `halt: true, reason: hitl.<…>`.
   Common causes: budget cap, safety violation, policy gate.
3. **Approval gate** — a transition rule fires `pause_for_approval: <node>`
   instead of `goto`. The next node won't execute until a `respond` arrives.

In all three cases the run stays resumable from its last checkpoint until the
operator either responds or cancels.

## Authoring a pause point

### `human_input` node (preferred)

```yaml
nodes:
  - name: confirm_action
    type: harbor.nodes.human_input
    prompt: "About to delete {{state.target}}. Confirm?"
    expected_input_schema:
      type: object
      required: [confirmed]
      properties:
        confirmed: {type: boolean}
        reason:    {type: string}
    timeout_seconds: 3600
    on_timeout: halt        # or: continue (with default), goto:<node>
```

The `prompt` is interpolated against state at pause time. The schema is
served to the responder UI / CLI so payloads can be validated before submit.

### Governance pause

```yaml
# in a Bosun pack
- name: require-approval-on-prod-write
  when:
    - { template: tool.target.env, op: eq, value: prod }
    - { template: tool.permissions, op: contains, value: write }
  then:
    pause_for_approval: ${last_node}
    reason: prod-write-needs-approval
    audience: ops
```

`audience` is a free-form tag the responder UI can filter on (`ops`, `legal`,
`compliance`, …). It's also written into the `(hitl.required …)` fact so
downstream queries can find what's pending and for whom.

## Responding

Three decision shapes:

| Decision | When to use | Resume behavior |
|---|---|---|
| `approve` | Approval-gate / `human_input` boolean confirms. | Run continues from the next transition. |
| `deny` | Reject the action. | Halt with reason; emits `(hitl.denied …)`. |
| `input` | `human_input` node expects structured data. | Payload becomes the node's output state slice. |

Submit via `/harbor:respond` or directly:

```bash
curl -fsS -X POST "${HARBOR_URL}/v1/runs/${RID}/respond" \
  -H "Authorization: Bearer ${HARBOR_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"decision":"input","payload":{"confirmed":true,"reason":"verified ticket #123"}}'
```

`payload` is validated against `expected_input_schema` server-side; bad
payloads return `422` with the failing JSON-pointer.

## Audit fact

Every response emits a `(human_response …)` fact carrying:

```
(human_response
  decision   approve|deny|input
  payload    <jsonb>          ; null for approve/deny without data
  reason     <string>         ; required for deny
  by         <responder_id>   ; from auth token's `sub` claim
  ts         <iso8601>
  origin     user             ; provenance
  source     hitl-driver      ; or whichever responder client
  run_id     <run_id>
  step       <step>)
```

Bosun `audit` pack signs these facts so the resume action is non-repudiable.

## Cleared / air-gapped deployments

- `expected_input_schema` MUST be present — payloads without a schema are
  rejected outright in the `cleared` profile.
- Every responder authenticates via JWT; `sub` claim becomes the `by` slot.
- `respond` calls write to the JSONL audit log even before the run resumes,
  so the operator action is recorded even if the resume fails downstream.

## Common patterns

- **Two-key approval**: emit two `pause_for_approval` rules requiring
  distinct `audience` tags. The second `respond` call resumes; the first
  flips a `(hitl.first_key …)` fact.
- **Deferred input**: `human_input` with `timeout_seconds: 86400` for slow
  human review (overnight ops). Pair with `bosun:budgets` so wall-time
  doesn't blow the run budget.
- **Inline rationale**: require `reason` in the schema for any `deny` —
  audit captures *why*, not just *that*.
