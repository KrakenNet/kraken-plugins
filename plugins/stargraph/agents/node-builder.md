---
description: Add a NodeSpec to a Stargraph IRDocument graph (builtin kind or module:Class); update state at the node boundary; verify via simulate / run --inspect.
tools: [Bash, Read, Write, Edit]
---

# Node Builder

Adds a **NodeSpec** (`{id, kind}`, plus an optional `config:` block for
builtins) to a graph's `stargraph.yaml` and wires the state it reads/writes.

## Inputs

- `graph_name`, `node_id` (slug `^[a-z0-9][a-z0-9_\-.]{0,127}$`).
- `kind` — either a builtin factory key (`echo`, `halt`, `dspy`, `ml`,
  `interrupt`, `passthrough`, `write_artifact`, `retrieval`, `subgraph`,
  `human_input`) or `module.path:ClassName` for a custom node.
- `reads` / `writes` — State fields the node consumes and produces.

## Steps

1. Add the node to `graphs/<graph>/stargraph.yaml` under `nodes:`:

   ```yaml
   nodes:
     - id: <node_id>
       kind: <builtin-kind | module.path:ClassName>
       # builtins accept a config: block, e.g. ml/interrupt:
       config:
         input_field: features
         output_field: risk
   ```

2. For a custom node, write/extend the class referenced by `module.path:ClassName`
   in `nodes/__init__.py` (or the module the `kind` names).
3. Wire routing: nodes have no explicit edges. Add a `goto` rule (or rely on
   static fall-through in declaration order) so the new node is reachable, e.g.

   ```yaml
   rules:
     - id: r-<prev>-to-<node_id>
       when: "?n <- (node-id (id <prev>))"
       then: [{ kind: goto, target: <node_id> }]
   ```

4. Manage the state boundary: add any new `writes` fields to the graph's
   `state_schema` (flat map) or to the `state_class` Pydantic model. Fields the
   downstream rules must route on are mirrored to CLIPS with
   `Annotated[T, Mirror()]`. Replay-safe state forbids `set` — use `frozenset`.
5. Verify (no graph-hash CLI; the canonical `graph_hash` is recomputed
   automatically from the IR on load):
   - `uv run stargraph run graphs/<graph>/stargraph.yaml --inspect` (rule-firing trace, no execution).
   - `uv run stargraph simulate graphs/<graph>/stargraph.yaml --fixtures fixtures/<graph>.yaml` (add a synthetic output for the new node id).
6. Add a fixture entry for the new node and confirm the rule trace reaches it.

## Output

YAML diff, state diff, simulate / run --inspect trace showing the node reached.
