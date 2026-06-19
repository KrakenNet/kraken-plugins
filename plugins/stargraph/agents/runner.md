---
description: Driver for Stargraph run/inspect/replay/respond. Polls run state, parses events, summarizes; reads fact deltas via `stargraph inspect --diff`.
tools: [Bash, Read]
---

# Runner

## Inputs

- Action: run | inspect | replay | respond
- `graph` + `--inputs` (for run); `run_id` + `--db` (for inspect/replay);
  `run_id` + response file + actor (for respond).

## Steps

1. **run** — execute a graph end-to-end against the checkpointer:
   ```bash
   stargraph run <graph.yaml> -i k=v [-i k2=v2] \
     --checkpoint ./.stargraph/run.sqlite --log-file run.jsonl
   ```
   Each `-i K=V` key must match the IR `state_schema`. Use `--inspect` for a
   rule-firing trace with no node execution. The run drives to terminal
   `done` / `failed` (exit 0 on done, non-zero on failed).

2. **inspect** — read-only views over the checkpointer DB:
   - Timeline: `stargraph inspect <run_id> --db ./.stargraph/run.sqlite --log-file run.jsonl`
   - State at step N: `stargraph inspect <run_id> --db ./.stargraph/run.sqlite --step N`
   - CLIPS fact delta (facts asserted/retracted between steps): `stargraph inspect <run_id> --db ./.stargraph/run.sqlite --diff N M`
   - Mode selector is `--diff` > `--step` > timeline; both `--diff`/`--step` require `--db`.

3. **replay** — fork a counterfactual run from a checkpoint:
   ```bash
   stargraph replay <run_id> --db ./.stargraph/run.sqlite \
     [--mutation cf/override.json] [--from-step N] --diff
   ```
   Mints a `cf-<uuid>` child; the parent's checkpoint rows stay byte-identical.

4. **respond** — deliver HITL input to an `awaiting-input` run (thin wrapper
   over `POST /v1/runs/{run_id}/respond`):
   ```bash
   stargraph respond <run_id> --response decision.json --actor alice \
     --server http://localhost:8000
   ```

### Driving runs via the serve API (when `stargraph serve` is up)

Default base URL `http://localhost:8000`. Verify-before-call:
`GET /v1/graphs` (confirm the `graph_id` is registered) → `POST /v1/runs`
(`{graph_id, inputs?, trigger_source?}`, returns `202` `{run_id, status:"pending"}`)
→ poll `GET /v1/runs/<run_id>` until status leaves pending/running, or attach
`WS /v1/runs/<run_id>/stream` for the live event stream.

## Output

Status, last node, last decision, total duration. For inspect, the timeline /
state-at-step / fact-diff view requested.
