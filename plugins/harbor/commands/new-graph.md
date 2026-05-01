---
description: Scaffold a Harbor graph (state.py, nodes/, rules/, harbor.yaml, tests)
argument-hint: <graph-name>
allowed-tools: [Bash, Read, Write, AskUserQuestion, Task]
---

# New Graph

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-kraken/SKILL.md` and `${CLAUDE_PLUGIN_ROOT}/skills/smart-harbor/SKILL.md`.

## Parse Arguments

`<graph-name>` (kebab-case). If missing, prompt.

## Interview

1. **Purpose?** (one line)
2. **Initial nodes?** (think/act/observe pattern? custom?)
3. **State fields?** (list of (name, type, annotated?))
4. **Rule packs to mount?** (bosun:budgets, bosun:audit, custom)
5. **Stores?** (vector / graph / doc / memory / fact — pick providers)

## Delegate

Task tool → `graph-builder`.

## Report

File tree, `harbor graph verify` result.
