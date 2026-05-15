---
description: Re-enter Ralph Loop mid-task. Reads .forge/prd.json, picks next failing task, dispatches ralph-coder.
allowed-tools: [Bash, Read, Agent]
---

# /forge:resume

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/pipeline/SKILL.md`.

## Preflight

```bash
[ -f .forge/prd.json ] || { echo "no .forge/prd.json — run /forge:new first"; exit 1; }
[ -f .forge/shared.md ] || { echo "no .forge/shared.md — Phase 1 incomplete"; exit 1; }
```

## Next Task

```bash
jq -r '.tasks[] | select(.passes == false) | .id' .forge/prd.json | head -1
```

If empty → all tasks pass. Print "Ralph Loop complete. Run /forge:status." and exit.

## Dispatch Ralph Loop

Agent `ralph-coder` with task id. Agent:
1. Reads task spec from `.forge/prd.json`
2. Writes code for that task only
3. Runs static gate (lint, empty diff check)
4. Runs anti-cheat gate (`${CLAUDE_PLUGIN_ROOT}/scripts/anti-cheat-scan.sh`)
5. Runs test gate (locked unit/integration tests)
6. Runs adversarial sandbox (contracts in `.forge/contracts/`)
7. On all green: marks `"passes": true` in `prd.json`, commits atomically
8. On fail: revises, retries (cap 3 attempts), or surfaces blocker

After return, re-check next failing task. Self-invoke until done or blocked.

## Report

Per task: pass/fail, gate that fired, commit SHA, next task.
