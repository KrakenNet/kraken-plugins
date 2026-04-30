---
description: Scaffold a Harbor skill bundle — tools, optional sub-graph, prompt fragment, entry-point registration
argument-hint: <skill-name>
allowed-tools: [Bash, Read, Write, AskUserQuestion, Task]
---

# New Skill

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-harbor/SKILL.md`.

## Interview

1. **Purpose?**
2. **Tools to ship?** (list of names; will scaffold each via `/harbor:new-tool` later)
3. **Has a sub-graph?** (y/n; if yes, will call `/harbor:new-graph`)
4. **Prompt fragment?** (optional)

## Delegate

Task tool → `skill-builder`.

## Report

Tree, entry-point registration in pyproject.toml.
