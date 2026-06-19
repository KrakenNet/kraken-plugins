---
description: Scaffold a Python stargraph.skills.Skill registered via register_skills (optionally a skill bundle)
argument-hint: <skill-name>
allowed-tools: [Bash, Read, Write, AskUserQuestion, Task]
---

# New Skill

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-stargraph/SKILL.md`.

## Interview

1. **Purpose?** (becomes `description`)
2. **Kind?** `SkillKind`: `agent` | `workflow` | `utility`.
3. **Tools to call?** A `list[str]` of registry-key ids (`<ns>.<name>@<ver>`);
   scaffold each via `/stargraph:new-tool`.
4. **State schema?** A Pydantic `BaseModel` whose **field names** are the
   declared output channels / write-whitelist. `set` / `set[X]` fields are
   rejected at construction — use `frozenset` (replay-safe).
5. **Has a sub-graph?** (optional `subgraph: str | None` — path/ref to an IR doc;
   if yes, scaffold via `/stargraph:new-graph`)
6. **System prompt fragment?** (optional `system_prompt: str | None`)
7. **Required capabilities?** (optional `requires: list[str]`)

## Write

A skill is a `stargraph.skills.Skill` instance, registered through the pluggy
`register_skills` hookimpl in a plugin under entry-point group `stargraph.skills`:

```python
from pydantic import BaseModel
from stargraph.plugin import hookimpl
from stargraph.skills import Skill, SkillKind

class MyState(BaseModel):
    answer: str = ""

MY_SKILL = Skill(
    name="<skill-name>",
    version="0.1.0",
    kind=SkillKind.utility,
    description="...",
    tools=["<ns>.<name>@1"],
    state_schema=MyState,
)

@hookimpl
def register_skills() -> list[Skill]:
    return [MY_SKILL]
```

`declared_output_keys` and `site_id = f"{name}@{version}"` are computed from the
above. The loader pre-validates each instance and pre-checks namespace conflicts
before any hookimpl body runs.

## Skill bundle (multi-file layout)

For a richer multi-file skill (the Shipwright archetype at
`src/stargraph/skills/shipwright/`), scaffold a bundle dir: `manifest.yaml`
(`id`, `version`, `kind`, `description`, `state_schema: module:Class`),
`stargraph.yaml` (graph: `name`, `state: ./state.py:State`, `nodes`, `rules:
- pack: ...`, `stores`, `checkpoints`), `state.py`, `nodes/`, and optional
`templates/` + `_pack.py`. This authoring shape is richer than the validated
IRDocument shape (see `/stargraph:new-graph`).

## Delegate

Task tool → `skill-builder`.

## Report

Tree, the `register_skills` entry-point registration in `pyproject.toml` under
group `stargraph.skills`, and the `site_id`.
