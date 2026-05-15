---
description: Phase 2 entry. Runs after Stage 5 human gate. Dispatches skeleton-scaffolder, contract-generator, task-sequencer in order. Emits prd.json and locks tests. Sets up Ralph Loop preconditions.
allowed-tools: [Bash, Read, Write, Agent]
---

# /forge:scaffold

Phase 1 → Phase 2 bridge. Materializes the design into failing tests, contracts, and a task array.

## Preflight

```bash
[ -f .forge/shared.md ] || { echo "no .forge/shared.md — run /forge:new first"; exit 1; }
[ -f .forge/prd.md ]    || { echo "no .forge/prd.md — Phase 1 incomplete"; exit 1; }
```

## Stage 6: Skeleton

Agent `skeleton-scaffolder`. Reads `shared.md`, creates files + interfaces + failing tests. Writes `.forge/tests-locked.json` and updates `.forge/anti-cheat.yaml` with scaffold-stage stub allowlist.

After return: confirm all generated tests fail with expected reasons. Bash:

```bash
# Run task tests once, expect non-zero exit
# Use project test cmd — infer from package.json, Makefile, pyproject.toml
```

## Stage 7: Test Simplifier Sweep

Inline (no separate agent). Scan locked tests for:
- mocks of internal modules → remove
- `@skip` / `it.skip` / `xit` → remove or surface as blocker
- assertions on implementation detail → flag for human

After this stage, tests are immutable. Write `.forge/tests-locked.json` checksums.

## Stage 8: Adversarial Contracts

Agent `contract-generator`. Writes `.forge/contracts/` Playwright + Postman + Docker bash. Index at `.forge/contracts/README.md`.

## Stage 9: Task Sequencer

Agent `task-sequencer`. Reads `shared.md` build sequence + locked tests. Writes `.forge/prd.json`.

Validate output:

```bash
python3 - <<'PY'
import json, sys
p = json.load(open('.forge/prd.json'))
tasks = p.get('tasks', [])
assert tasks, "no tasks generated"
ids = {t['id'] for t in tasks}
for t in tasks:
    for d in t['depends_on']:
        assert d in ids, f"task {t['id']} depends on missing {d}"
print(f"OK: {len(tasks)} tasks, schema valid")
PY
```

## Stage 9b: Rebuild graph

```bash
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/forge_graph.py" rebuild
```

Ensures the spec graph reflects new prd.json + any spec edits made during scaffolding. Ralph Loop will query this graph.

## Hand-off

On success, print:

```
Phase 2 ready. N tasks queued, M tests locked, K contracts generated.
Graph: <node count> nodes indexed.
Start Ralph Loop with: /forge:resume
```
