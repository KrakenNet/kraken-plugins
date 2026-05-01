---
description: Respond to a paused (HITL) Harbor run — supply human input, approve/deny, resume
argument-hint: <run_id> --decision <approve|deny|input> [--payload <json>] [--reason <str>]
allowed-tools: [Bash, Read, AskUserQuestion]
---

# Harbor Respond

Resume a run that's paused at a `human_input` node or a Bosun governance hold.

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-harbor/SKILL.md` and
`${CLAUDE_PLUGIN_ROOT}/references/hitl-patterns.md`.

## Verify Pause

Refuse unless the run is in `PAUSED_HITL` status:

```bash
STATUS=$(curl -fsS "${HARBOR_URL}/v1/runs/${RID}" \
  -H "Authorization: Bearer ${HARBOR_TOKEN}" | jq -r .status)
[[ "$STATUS" == "PAUSED_HITL" ]] || { echo "not paused (status=$STATUS)"; exit 2; }
```

Show the user the pending question/context (`prompt`, `policy_reason`, expected
schema for `payload`) before asking for their response.

## Parse Arguments

- `--decision`: `approve` | `deny` | `input`
- `--payload`: JSON matching the run's `expected_input_schema` (required for `input`, optional for `approve`)
- `--reason`: free-form audit string (required for `deny`, recommended for `approve`)

If args are missing, prompt with AskUserQuestion. Validate `--payload` against
the schema with `jsonschema` before submitting.

## Run

```bash
curl -fsS -X POST "${HARBOR_URL}/v1/runs/${RID}/respond" \
  -H "Authorization: Bearer ${HARBOR_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"decision\": \"${DECISION}\", \"payload\": ${PAYLOAD:-null}, \"reason\": ${REASON_JSON:-null}}"
```

## Report

- New status (`RUNNING` / `COMPLETED` / `HALTED`)
- Audit fact emitted: `(human_response decision=… reason=… by=… ts=…)`
- Next node about to run, if any
- Stream URL to follow: `${HARBOR_URL}/v1/runs/${RID}/stream`
