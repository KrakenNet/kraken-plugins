---
description: Dry-run a Harbor graph in a sandboxed engine — no side-effecting tools, deterministic stubs
argument-hint: <graph> [--input-file <json>] [--seed <int>] [--max-steps <n>]
allowed-tools: [Bash, Read, AskUserQuestion]
---

# Harbor Simulate

Execute a graph end-to-end with all `side-effects ≠ none` tool calls swapped
for deterministic stubs. Use to smoke-test routing rules and Bosun packs
without touching real systems.

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-harbor/SKILL.md` and
`${CLAUDE_PLUGIN_ROOT}/references/graph-yaml-schema.md`.

## Parse Arguments

- `<graph>` — graph name registered with `harbor serve`, or a path to `harbor.yaml`.
- `--input-file <json>` — initial state. Defaults to the graph's `examples/smoke.json` if present.
- `--seed <int>` — RNG seed for any DSPy nodes flagged `must_stub`. Default `0`.
- `--max-steps <n>` — abort if the graph exceeds this. Default `50`.

## Run

```bash
uv run harbor simulate "${GRAPH}" \
  ${INPUT_FILE:+--input-file "$INPUT_FILE"} \
  --seed "${SEED:-0}" \
  --max-steps "${MAX_STEPS:-50}"
```

## Report

- Whether simulation completed, halted, or hit max-steps
- Node trace: `step → node → outcome → next-rule-fired`
- Tools that would have side-effected (with the args they were called with)
- Any rule pack assertions that fired
- Suggested next step: real `/harbor:run` if clean, otherwise inspect the
  failing rule or stub
