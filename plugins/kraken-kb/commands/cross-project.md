---
description: Bootstrap a Railyard-style KB inside a Kraken sibling project (fathom, nautilus, or harbor) using the same conventions
argument-hint: [fathom|nautilus|harbor|--auto-detect]
allowed-tools: [Bash, Read, Write, AskUserQuestion, Task]
---

# Cross-Project KB Bootstrap

Initialize a fresh KB in a Kraken sibling project using the same article shape, gap-file pattern, and `_index.md` routing as railyard.

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/kb-conventions/SKILL.md`.

## Resolve Target

From `$ARGUMENTS`:
- If a project name is given (`fathom`, `nautilus`, `harbor`), use it.
- If `--auto-detect`, read `pyproject.toml` in PWD: name `fathom-rules` → fathom; `nautilus-rkm` → nautilus; `harbor` → harbor.
- Otherwise, prompt with AskUserQuestion: which project?

Resolve the absolute path to the project's repo (under `/home/sean/leagues/<project>/` if monorepo-aware, else PWD).

## Delegate

Delegate to the existing `kb-bootstrapper` agent via Task tool with:
- `project_name`
- `project_root`
- `kb_dir` (default `docs/`)
- `index_template` (Railyard `_index.md` shape)

## Report

Show the created file tree and the `_index.md` skeleton.
