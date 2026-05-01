---
description: Scaffold a Harbor SKILL.md (lightweight markdown skill format that compiles to a typed harbor.skills.Skill)
argument-hint: <skill-name>
allowed-tools: [Bash, Read, Write, AskUserQuestion, Task]
---

# New Markdown Skill

Lightweight authoring path: a single `SKILL.md` (YAML frontmatter + markdown
body) compiles into a typed `harbor.skills.Skill` instance. Same runtime
guarantees (state-schema enforcement, capability gates, deterministic
replay) — no Python boilerplate.

Use this command when you want a Claude-Code-style authoring experience
instead of a full pip-installable package. Use `/harbor:new-skill` for the
heavier Python-package path.

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-harbor/SKILL.md`.

## Interview

1. **Purpose?** (one sentence — becomes the description)
2. **Kind?** (`agent` | `workflow` | `utility`)
3. **Tools to reference?** (list of `<namespace>.<name>@<semver-range>` ids; must already be registered)
4. **State schema fields?** (name + type per declared output channel)
5. **Required capabilities?** (e.g. `billing.read`, `net.fetch`)
6. **Has a typed sub-graph?** (y/n; if yes, will call `/harbor:new-graph`)
7. **Examples?** (optional — at least one input/expected_output pair recommended)

## Delegate

Task tool → `md-skill-builder`.

## Report

- Path to the new `SKILL.md`.
- Result of `harbor skills compile <path>` validation.
- If hosted inside an existing dir-plugin, the plugin name it was added to.
