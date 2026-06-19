---
description: Author a Stargraph skill bundle — the Shipwright multi-file layout (manifest.yaml + stargraph.yaml + state.py + nodes/) that packages a Python `stargraph.skills.Skill`; verify via simulate / run --inspect.
tools: [Bash, Read, Write, Edit]
---

# Skill Bundle Builder

Builds a **skill bundle**: the canonical multi-file shape for a Python
`stargraph.skills.Skill`, modeled on the in-tree Shipwright bundle
(`src/stargraph/skills/shipwright/`). There is no markdown `SKILL.md` format —
a skill is always a Python `Skill` (single file or this bundle layout).

## Inputs

- `skill_name` (slug), `purpose`, `kind` (`agent` | `workflow` | `utility`).
- `state_fields` — `(name, type, mirrored?)`; the state model's FIELD NAMES are
  the declared output channels / write whitelist. `set`/`set[X]` is rejected —
  use `frozenset`.
- `nodes` — the subgraph nodes (builtin kind or `module.path:ClassName`).
- `rule_packs` / `governance` — Bosun packs the subgraph mounts.
- `host_path` — directory to create the bundle under.

## Steps

1. Create the bundle at `<host_path>/<skill_name>/` (Shipwright layout):
   ```
   <skill_name>/
     manifest.yaml      skill identity + state_schema reference
     stargraph.yaml     graph: state ref, nodes, rules, stores, checkpoints
     state.py           the State Pydantic model
     nodes/             per-node modules
     templates/         prompt fragments (optional)
     _pack.py           Bosun sub-pack loader (optional)
   ```

2. `manifest.yaml`:
   ```yaml
   id: <skill_name>
   version: "0.1.0"
   kind: <kind>
   description: |
     <purpose>
   state_schema: <module>.state:State
   ```

3. `stargraph.yaml` — the bundle graph (authoring shape, richer than the
   validated IRDocument):
   ```yaml
   name: <skill_name>
   state: ./state.py:State
   nodes:
     - name: <node>
       type: <module.path:ClassName | stargraph.nodes.human_input>
   rules:
     - pack: <bosun.pack.id>
   stores:
     doc: sqlite:./.<skill_name>/docs.db
     fact: sqlite:./.<skill_name>/facts.db
   checkpoints:
     every: node-exit
     store: sqlite:./.<skill_name>/checkpoints.db
   ```

4. `state.py` — the `State` model referenced from `manifest.yaml#state_schema`
   and `stargraph.yaml#state`. Mirror fields the rule packs route on with
   `Annotated[T, Mirror()]`; no `set` (use `frozenset`).
5. Write `nodes/` modules for each custom node `type`.
6. Register the bundle as a Skill plugin so the loader picks it up: a
   `register_skills()` hookimpl under entry-point group `stargraph.skills`
   returning the `Skill` whose `subgraph` points at the bundle graph (delegate
   to `skill-builder` for the pyproject + `_plugin.py` wiring).
7. **Verify** (there is no skill compiler or skill-compile CLI subcommand). Validate the
   subgraph's IRDocument form and discovery:
   - `uv run stargraph simulate <graph.yaml> --fixtures <fixtures.yaml>` or `run --inspect`.
   - `STARGRAPH_TRACE_PLUGINS=1 stargraph run <any-graph.yaml> --inspect` to
     confirm discovery + registration; or `GET /v1/registry/skills` with serve up.

## Build-Test-Fix

5 iterations. On each failure edit only the offending field/file; surface the
validation `path`/`hint` rather than overwriting blindly.

## Output

- Tree of the created bundle.
- simulate / run --inspect output and the discovery trace / `GET /v1/registry/skills`.

## Constraints

- The state model's field names are the **only** allowed boundary writes;
  document which subgraph node writes which field.
- Tool refs are registry-key ids `<namespace>.<name>@<version>` — never bare names.
