---
description: Counterfactual replay — fork a run from a checkpoint with mutated facts/state, diff against original
argument-hint: <run_id> --from <step> --mutate <json> [--compare]
allowed-tools: [Bash, Read, AskUserQuestion]
---

# Stargraph Counterfactual

Like `/stargraph:replay` but you mutate something on the way through and Stargraph
diffs the alternate run against the original. Use when answering questions
like *"would the routing have changed if `intent` had been `research`?"*

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-stargraph/SKILL.md` and
`${CLAUDE_PLUGIN_ROOT}/references/provenance-facts.md`.

## Parse Arguments

- `<run_id>` — required. Source run to fork.
- `--from <step>` — required. Checkpoint step to branch from.
- `--mutate <json>` — required. JSON Patch (RFC 6902) or shorthand
  `{"facts.<template>.<slot>": <value>}` / `{"state.<field>": <value>}`.
- `--compare` — also fetch a diff vs the original (default true; pass `--no-compare` to skip).

If any required arg is missing, prompt with AskUserQuestion before continuing.

## Verify Graph Hash

A counterfactual is meaningless across graph versions. Refuse if the original
run's `graph_hash` doesn't match the currently-registered graph.

```bash
ORIG=$(curl -fsS "${STARGRAPH_URL}/v1/runs/${RID}" -H "Authorization: Bearer ${STARGRAPH_TOKEN}" | jq -r .graph_hash)
CUR=$(curl -fsS "${STARGRAPH_URL}/v1/graphs/${GRAPH}" -H "Authorization: Bearer ${STARGRAPH_TOKEN}" | jq -r .hash)
[[ "$ORIG" == "$CUR" ]] || { echo "graph_hash mismatch — refuse"; exit 2; }
```

## Run

```bash
NEW_RUN=$(curl -fsS -X POST "${STARGRAPH_URL}/v1/runs/${RID}/counterfactual" \
  -H "Authorization: Bearer ${STARGRAPH_TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"from_step\": ${STEP}, \"mutate\": ${MUTATE}}" | jq -r .run_id)

curl -fsS "${STARGRAPH_URL}/v1/runs/${NEW_RUN}/compare?against=${RID}" \
  -H "Authorization: Bearer ${STARGRAPH_TOKEN}" | jq .
```

## Report

- New `run_id`
- Divergence point: first step where node, transition, or facts differ from original
- Side-by-side: nodes visited, terminal facts, final state
- Cost delta (LLM tokens, tool calls) if budgets pack mounted
- Whether the terminal `result` changed
