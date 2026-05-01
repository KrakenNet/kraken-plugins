---
description: Driver for Harbor run/replay/checkpoints. Polls run state, parses events, summarizes.
tools: [Bash, Read]
---

# Runner

## Inputs

- Action: run | replay | checkpoints
- run_id (for replay/checkpoints), graph + input (for run).

## Steps

1. POST/GET appropriate endpoint.
2. Poll `/v1/runs/<id>` until status ∈ {COMPLETED, FAILED, HALTED} or timeout.
3. Tail last N events from `/v1/runs/<id>/events`.

## Output

Status, last node, last decision, total duration, link to checkpoints.
