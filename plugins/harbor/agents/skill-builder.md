---
description: Scaffold a pip-installable Harbor skill package with entry-point registration.
tools: [Bash, Read, Write, Edit]
---

# Skill Builder

## Inputs

- `skill_name`, `purpose`, `tools`, `subgraph`, `prompt_fragment`.

## Steps

1. Create `harbor-skill-<skill_name>/` package.
2. `pyproject.toml` with `[project.entry-points."harbor.skills"]`.
3. `src/harbor_skill_<skill_name>/__init__.py` exporting `Skill` instance.
4. For each declared tool, scaffold under `tools/`.
5. If subgraph, create under `graphs/<skill_name>/`.
6. If prompt_fragment, write `prompts/<skill_name>.md`.
7. Run `uv pip install -e .`; verify `harbor skills list` shows it.

## Output

Tree + skills list.
