---
description: Scaffold + verify Stargraph IRDocument graphs. Writes state, nodes, rules, stargraph.yaml, fixtures; validates via `stargraph simulate` / `run --inspect` and `stargraph.ir.validate`; iterates.
tools: [Bash, Read, Write, Edit]
---

# Graph Builder

Builds a validated **IRDocument** graph (the runnable shape: `ir_version`,
`id`, `nodes`, `rules`, plus optional `tools`/`skills`/`stores`/`governance`).
All IR models pin `extra='forbid'`, so unknown keys are rejected at load.

## Inputs

- `graph_name`, `purpose`, `nodes` (list of `(id, kind)`), `state_fields`
  (name → type), `rule_packs` (governance PackMounts), `stores`.

## Steps

1. Create dir `graphs/<graph_name>/`.
2. Define state — pick ONE:
   - Flat `state_schema: {field: "type", ...}` inline in the IR, OR
   - `state_class: "module.path:ClassName"` pointing at a Pydantic model in
     `state.py`. The two are mutually exclusive. Mirrored fields (projected to
     CLIPS at node boundaries) use `Annotated[T, Mirror()]`; replay-safe state
     forbids `set` — use `frozenset`.
3. Write `nodes/__init__.py` for any custom node classes (referenced as
   `module.path:ClassName`); builtin kinds (`echo`, `halt`, `dspy`, `ml`,
   `interrupt`, `passthrough`, `write_artifact`, `retrieval`, `subgraph`,
   `human_input`) need no code.
4. Write `stargraph.yaml` per `references/graph-yaml-schema.md` (IRDocument
   shape; node/rule/pack ids must match `^[a-z0-9][a-z0-9_\-.]{0,127}$`):

   ```yaml
   ir_version: "1.0.0"
   id: "graph:<graph_name>"
   state_schema: { message: "str", severity: "int" }
   nodes:
     - { id: "classify", kind: "dspy" }
     - { id: "halt", kind: "halt" }
   rules:
     - id: "r-escalate"
       when: "(severity ?s&:(>= ?s 4))"
       then: [{ kind: "goto", target: "classify" }]
   governance:
     - id: "stargraph.bosun.routing"
       version: "1.0.0"
       requires: { stargraph_facts_version: "1.0", api_version: "1" }
   ```

   Routing has no explicit edges: static fall-through (declaration order) plus
   rule `goto`/`halt`/`parallel`/`interrupt` actions.
5. Write a fixtures file (`fixtures/<graph_name>.yaml`): a `node_id → synthetic
   output` map for offline rule-trace verification.
6. **Validate** (there is no graph-verify CLI subcommand):
   - Offline rule trace: `uv run stargraph simulate graphs/<graph_name>/stargraph.yaml --fixtures fixtures/<graph_name>.yaml` (no tools/LLM/checkpoint).
   - Rule-firing trace without node execution: `uv run stargraph run graphs/<graph_name>/stargraph.yaml --inspect`.
   - Structural validation in Python: `stargraph.ir.validate(ir)` returns
     `list[ValidationError]` (empty = valid; never raises). IRDocument
     validation is also automatic on load via `extra='forbid'`.
7. On error, parse the validation/simulate output (JSON-pointer `path` + `hint`),
   fix the offending field, retry.

## Output

Tree, `simulate` / `run --inspect` output, any `stargraph.ir.validate` errors.
