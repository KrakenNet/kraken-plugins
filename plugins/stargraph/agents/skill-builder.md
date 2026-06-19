---
description: Scaffold a pip-installable Stargraph Skill plugin — a Python `stargraph.skills.Skill` registered via `register_skills` under the stargraph.skills entry-point group; verify discovery and registration.
tools: [Bash, Read, Write, Edit]
---

# Skill Builder

Builds a pip package that contributes a Python `stargraph.skills.Skill`. A Skill
is registered through the `register_skills()` hookimpl under the entry-point
group `stargraph.skills` (there is no markdown skill format).

## Inputs

- `skill_name`, `purpose`, `kind` (`agent` | `workflow` | `utility`),
  `tools` (registry-key ids `<ns>.<name>@<ver>`), `subgraph` (optional IR ref),
  `system_prompt` (optional).

## Steps

1. Create `stargraph-skill-<skill_name>/` package.
2. `pyproject.toml` declaring BOTH entry-point groups:
   ```toml
   [project.entry-points."stargraph"]
   stargraph_plugin = "stargraph_skill_<skill_name>._plugin:manifest"

   [project.entry-points."stargraph.skills"]
   <skill_name> = "stargraph_skill_<skill_name>._plugin:register_skills"
   ```
3. `src/stargraph_skill_<skill_name>/_plugin.py` — define the `Skill` and the
   `register_skills` hookimpl:
   ```python
   from stargraph.plugin import hookimpl
   from stargraph.skills import Skill, SkillKind
   from pydantic import BaseModel

   class State(BaseModel):
       answer: str = ""   # FIELD NAMES are the declared output channels / write whitelist; no `set` — use `frozenset`

   MY_SKILL = Skill(
       name="<skill_name>",
       version="0.1.0",
       kind=SkillKind.<kind>,
       description="<purpose>",
       tools=[<"ns.name@ver">],        # registry-key ids
       subgraph=None,                   # or path/ref to an IR doc
       system_prompt=None,
       state_schema=State,
       requires=[],                     # capability strings
       bubble_events=True,
   )

   @hookimpl
   def register_skills() -> list[Skill]:
       return [MY_SKILL]
   ```
   Also expose a `manifest` factory returning a `PluginManifest`
   (`api_version="1"`, `provides=["skill"]`).
4. If `subgraph` is set, author its IRDocument (delegate to `graph-builder`).
   For richer multi-file skills, use the **bundle** layout (Shipwright archetype):
   `manifest.yaml` (`id`, `version`, `kind`, `description`, `state_schema:
   module:Class`), `stargraph.yaml`, `state.py`, `nodes/`, optional `templates/`.
5. Install: `uv pip install -e .`.
6. **Verify discovery + registration** (there is no skill-listing CLI subcommand):
   - Run any subcommand with `STARGRAPH_TRACE_PLUGINS=1` and confirm the
     distribution is discovered, its manifest validates, and the skill registers:
     `STARGRAPH_TRACE_PLUGINS=1 stargraph run <any-graph.yaml> --inspect`.
   - At runtime with `stargraph serve` up: `GET /v1/registry/skills`.

## Output

Tree, `STARGRAPH_TRACE_PLUGINS=1` discovery trace, `GET /v1/registry/skills`
result (or trace-only if serve not running).
