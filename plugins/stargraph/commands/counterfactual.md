---
description: Compute a counterfactual-derived graph_hash for a graph + mutation, without forking a run
argument-hint: <graph> --step <n> --mutate <file.yaml>
allowed-tools: [Bash, Read, AskUserQuestion]
---

# Stargraph Counterfactual

Compute the counterfactual-derived `graph_hash` for a parent IR plus a mutation
YAML, **without** forking a run. Use this to verify a mutation file round-trips
and to pin the `graph_hash` you should see in the resulting cf-checkpoint —
e.g. answering *"would the routing have changed if `intent` had been
`research`?"* before you actually fork with `/stargraph:replay`.

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-stargraph/SKILL.md` and
`${CLAUDE_PLUGIN_ROOT}/references/provenance-facts.md`.

## Parse Arguments

- `<graph>` — required. Path to the parent run's IR YAML graph definition.
- `--step <n>` — required. Checkpoint step index at which to fork (recorded in output).
- `--mutate <file.yaml>` — required. A YAML file describing a
  `CounterfactualMutation` (state overrides, fact asserts/retracts, etc.).

If any required arg is missing, prompt with AskUserQuestion before continuing.

## Run

The mutation YAML is validated through `CounterfactualMutation` (`extra='forbid'`,
so typos surface here):

```bash
uv run stargraph counterfactual "${GRAPH}" \
  --step "${STEP}" \
  --mutate cf/swap-tool.yaml
```

Output:

```text
original_graph_hash=...
cf_step=4
derived_graph_hash=...
```

To actually fork a run from a checkpoint and diff the alternate against the
original, use `/stargraph:replay` (CLI) or
`POST /v1/runs/{run_id}/counterfactual` on a running `stargraph serve`.

## Report

- `original_graph_hash`, `cf_step`, and `derived_graph_hash`
- Whether the mutation file validated (a `CounterfactualMutation` parse error
  means a bad slot/field — fix the YAML)
- Next step: fork with `/stargraph:replay --from-step <step> --mutation <json>`
  to see the alternate run and its `RunDiff`
