---
description: Author a SKILL.md (YAML frontmatter + markdown body) for the harbor-md-skills compiler; validate via `harbor skills compile`.
tools: [Bash, Read, Write, Edit]
---

# MD Skill Builder

Builds a single `SKILL.md` that compiles into a typed `harbor.skills.Skill`.
No Python package; the file lives inside a directory plugin
(`~/.harbor/plugins/<plugin>/skills/<skill-name>/SKILL.md`) or a project's
local `skills/` tree.

## Inputs

- `skill_name` (slug) — directory and frontmatter `name`.
- `purpose` — one-sentence description.
- `kind` — `agent` | `workflow` | `utility`.
- `tools` — list of `<namespace>.<name>@<semver-range>` ids (must already
  be registered, or contributed by tools elsewhere in the same dir-plugin).
- `state_schema_fields` — `[(field_name, json_schema_type)]`; becomes the
  declared output write-whitelist enforced by `SubGraphNode`.
- `requires` — list of capability strings.
- `subgraph_path` (optional) — if provided, embedded as `subgraph:` in
  frontmatter; absent = single-step React subgraph default.
- `examples` (optional) — list of `(inputs, expected_output)` pairs.
- `host_path` — directory to create the skill under. Default
  `~/.harbor/plugins/<dir-plugin>/skills/<skill_name>/` if invoked from a
  dir-plugin context, else `./skills/<skill_name>/`.

## Steps

1. Create `<host_path>/SKILL.md`.
2. Emit frontmatter:
   ```yaml
   ---
   name: <skill_name>
   version: 0.1.0
   kind: <kind>
   description: |
     <purpose>
   requires: [<requires>]
   tools: [<tools>]
   state_schema:
     <field>: { type: <type>, ... }
   examples:
     - inputs: { ... }
       expected_output: { ... }
   ---
   ```
3. Emit body skeleton with sections:
   - `# <Title>` — derived from `purpose`.
   - `## When to <verb>` — preconditions for activation.
   - `## Procedure` — numbered steps using `{{ tool_descriptions }}` template
     references.
   - `## Failure modes` — when to refuse / escalate.
4. If `subgraph_path` provided, write a stub IR sub-graph at that path via
   `/harbor:new-graph` (or scaffold inline JSON for trivial cases).
5. If `examples` provided, drop one fixture per example into
   `<host_path>/examples/NN_<slug>.json`.
6. Validate: `harbor skills compile <host_path>/SKILL.md`. On error, parse
   the JSON envelope and surface the failure section to fix.

## Build-Test-Fix

5 iterations. On each failure, edit only the offending field; never
overwrite the whole file blindly.

## Output

- Path to `SKILL.md`.
- Validation result (success or specific compile error).
- If hosted inside a dir-plugin, the plugin's `plugin.toml` did NOT need to
  change — confirm by re-running `harbor plugins inspect <plugin>` and
  checking the skill appears in the registered set.

## Constraints

- Markdown body MUST NOT contain `<script>` tags or raw HTML — the prompt is
  data, not code (`harbor-md-skills` rejects these).
- Tool refs MUST be `<namespace>.<name>@<semver-range>` format; bare names
  fail compile with an unambiguous error.
- `state_schema` fields are the **only** allowed boundary writes; document
  which sub-graph step writes which field.
