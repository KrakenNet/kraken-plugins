---
description: Scaffold a Stargraph IRDocument graph (stargraph.yaml + optional state class, nodes, rules, governance)
argument-hint: <graph-name>
allowed-tools: [Bash, Read, Write, AskUserQuestion, Task]
---

# New Graph

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-kraken/SKILL.md` and `${CLAUDE_PLUGIN_ROOT}/skills/smart-stargraph/SKILL.md`.

## Parse Arguments

`<graph-name>` (kebab-case). If missing, prompt.

## Interview

1. **Purpose?** (one line)
2. **Initial nodes?** For each: a builtin `kind` (`echo`, `halt`, `dspy`, `ml`,
   `interrupt`, `passthrough`, `write_artifact`, `retrieval`, `subgraph`,
   `human_input`) or a custom `module.path:ClassName`.
3. **State?** Either a flat `state_schema` (name→type-string map) OR a
   `state_class: "module.path:ClassName"` Pydantic model (mutually exclusive).
4. **Rule packs to mount?** (governance PackMounts — `stargraph.bosun.budgets`,
   `stargraph.bosun.audit`, custom slug + version)
5. **Stores?** (vector / graph / doc / memory / fact — pick providers; see `/stargraph:store`)

## IRDocument shape

The runnable IR is an `IRDocument` (all IR models pin `extra='forbid'`, so
unknown keys are rejected at load). Top-level keys: `ir_version`, `id`, `nodes`
(required); `rules`, `tools`, `skills`, `stores`, `governance`, `migrate`,
`parallel`, and `state_schema` / `state_class` (optional). Routing is implicit:
static fall-through in declaration order plus rule `goto` actions — there are no
explicit edges.

```yaml
ir_version: "1.0.0"
id: "graph:<graph-name>"
state_class: "graph.state:RunState"   # OR a flat state_schema map
nodes:
  - id: classify
    kind: dspy
  - id: decide
    kind: passthrough
  - id: halt
    kind: echo
governance:
  - id: stargraph.bosun.audit
    version: "1.0"
    requires: { stargraph_facts_version: "1.0", api_version: "1" }
rules:
  - id: r-classify-to-decide
    when: "?n <- (node-id (id classify))"
    then: [{ kind: goto, target: decide }]
  - id: r-halt
    when: "?n <- (node-id (id halt))"
    then: [{ kind: halt, reason: "done" }]
```

Node/rule/pack ids must match `^[a-z0-9][a-z0-9_\-.]{0,127}$`.

## Delegate

Task tool → `graph-builder`.

## Report

File tree, plus validation result from `stargraph simulate <graph.yaml> --fixtures <f>`
or `stargraph run <graph.yaml> --inspect` (rule trace, no execution). IRDocument
validation runs automatically on load; `stargraph.ir.validate(ir)` gives the
structured error list in Python.
