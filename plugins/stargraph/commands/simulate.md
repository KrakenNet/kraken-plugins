---
description: Offline rule-firing trace for a Stargraph graph against synthetic fixtures — no tools/LLM/checkpoint
argument-hint: <graph> --fixtures <file>
allowed-tools: [Bash, Read, AskUserQuestion]
---

# Stargraph Simulate

Validate a graph's rule logic against caller-supplied synthetic node outputs
without invoking any tool, LLM, or checkpoint. Use to smoke-test routing rules
and Bosun packs without touching real systems.

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-stargraph/SKILL.md` and
`${CLAUDE_PLUGIN_ROOT}/references/graph-yaml-schema.md`.

## Parse Arguments

- `<graph>` — path to an IR YAML graph definition (commonly `<graphdir>/stargraph.yaml`).
- `--fixtures <file>` — required. A YAML file mapping `node_id` → synthetic
  output dict (one entry per IR node). Defaults to the graph's
  `fixtures/*.yaml` if the user points at one.

## Run

```bash
uv run stargraph simulate "${GRAPH}" --fixtures "${FIXTURES}"
```

Output mirrors `stargraph run --inspect`: a leading
`graph_hash=<hex>` and `rule_firings=<count>` line, followed by one row per
rule firing.

## Report

- The `graph_hash` and total `rule_firings`
- The rule-firing trace: which rules fired, in declaration/`goto` order
- Any `assert`/`retract`/`goto`/`halt` actions the fired rules produced
- Suggested next step: real `/stargraph:run` if the trace looks right,
  otherwise fix the failing rule `when` pattern or the fixture output it matches
