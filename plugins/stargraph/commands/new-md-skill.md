---
description: Author a Stargraph skill bundle (manifest.yaml + stargraph.yaml + state.py + nodes/) per the Shipwright archetype
argument-hint: <skill-name>
allowed-tools: [Bash, Read, Write, AskUserQuestion, Task]
---

# New Skill Bundle

There is exactly one skill format: the Python `stargraph.skills.Skill`. A skill
bundle is its richer multi-file packaging — a directory with a `manifest.yaml`,
a `stargraph.yaml` graph, a typed `state.py`, and per-node modules. The
reference archetype is `src/stargraph/skills/shipwright/`.

For a single-file `Skill` instance, use `/stargraph:new-skill`. Use this command
when the skill is graph-shaped (multiple nodes + rules + stores).

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-stargraph/SKILL.md`.

## Interview

1. **Purpose?** (one sentence — becomes the `description`)
2. **Kind?** `agent` | `workflow` | `utility`.
3. **State model?** A Pydantic `State` in `state.py`; its field names are the
   declared output channels / write-whitelist. Annotated (`Mirror`) fields are
   projected to CLIPS facts at node boundaries. `set` / `set[X]` rejected — use
   `frozenset`.
4. **Nodes?** Each maps `name` → a builtin (`stargraph.nodes.human_input`, ...)
   or a custom `module.path:Class`.
5. **Bosun rule packs / governance?** (`rules: - pack: ...`, `governance: ...`)
6. **Stores + checkpoints?** (`stores: {doc:, fact:}`, `checkpoints:`)
7. **Tools to reference?** A `list[str]` of registry-key ids (`<ns>.<name>@<ver>`).

## Layout (Shipwright archetype)

```
<skill-name>/
  manifest.yaml   # id, version, kind, description, state_schema: module:Class
  stargraph.yaml  # graph: name, state: ./state.py:State, nodes, rules, governance, stores, checkpoints
  state.py        # the State Pydantic model
  nodes/          # per-node modules
  templates/      # prompt fragments (optional)
  _pack.py        # CLIPS pack loader (optional)
```

`manifest.yaml`:

```yaml
id: my.skills.<skill-name>
version: "0.1.0"
kind: workflow
description: |
  ...
state_schema: my.skills.<skill-name>.state:State
```

`stargraph.yaml`:

```yaml
name: <skill-name>
state: ./state.py:State
nodes:
  - name: human_input
    type: stargraph.nodes.human_input
    expected_input_schema_from: open_questions
rules:
  - pack: my.bosun.<skill-name>.gaps
stores:
  doc: sqlite:./.<skill-name>/docs.db
  fact: sqlite:./.<skill-name>/facts.db
checkpoints:
  every: node-exit
  store: sqlite:./.<skill-name>/checkpoints.db
```

## Delegate

Task tool → `md-skill-builder`.

## Report

- Tree of the bundle dir.
- The `register_skills` entry-point registration (group `stargraph.skills`) if
  the bundle is shipped as a plugin.
- Validation: run the bundle graph via `stargraph run <stargraph.yaml> --inspect`
  or `stargraph simulate <stargraph.yaml> --fixtures <f>`.
