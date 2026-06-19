---
description: Add a NodeSpec to a Stargraph graph (builtin kind or custom module:Class)
argument-hint: <graph> <node-name>
allowed-tools: [Bash, Read, Write, AskUserQuestion, Task]
---

# New Node

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-stargraph/SKILL.md`.

## Interview

1. **Kind?** A builtin factory key (`echo`, `halt`, `dspy`, `ml`, `interrupt`,
   `passthrough`, `write_artifact`, `retrieval`, `subgraph`, `human_input`) or a
   custom `module.path:ClassName`.
2. **Config?** Builtins read a `config:` block (e.g. an `ml` node takes
   `model_id`, `version`, `runtime`, `file_uri`, `expected_sha256`,
   `input_field`, `output_field`; an `interrupt` node takes `prompt`,
   `requested_capability`, `timeout`, `on_timeout`).
3. **State fields read/written?** Custom nodes return a dict of state-field
   updates; annotated (mirrored) fields are projected to CLIPS facts at the node
   boundary so rules can route on them.
4. **Routing in?** A `RuleSpec` `goto`/`parallel`/`interrupt` action, or static
   fall-through (declaration order). There are no explicit edges.

## NodeSpec shape

A node is `{id, kind}` plus an optional `config:` block:

```yaml
nodes:
  - id: <node-name>
    kind: passthrough
  - id: risk_score
    kind: ml
    config:
      model_id: severity
      version: "1.0.0"
      runtime: onnx
      input_field: features
      output_field: risk
```

`id` must match `^[a-z0-9][a-z0-9_\-.]{0,127}$`.

## Delegate

Task tool → `node-builder`.

## Report

Updated `graph_hash` (canonical IR hash from `dumps_canonical`). If it changed,
warn that existing checkpoints will be rejected on resume unless a `migrate:`
block maps `from_hash`→`to_hash`. Re-validate with `stargraph run <graph.yaml>
--inspect` or `stargraph simulate <graph.yaml> --fixtures <f>`.
