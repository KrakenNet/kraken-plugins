---
description: Scaffold a new Fathom rule pack with pack.yaml, templates/, rules/, modules/, functions/, tests/, README
argument-hint: <pack-name>
allowed-tools: [Bash, Read, Write, AskUserQuestion, Task]
---

# New Rule Pack

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-kraken/SKILL.md` and `${CLAUDE_PLUGIN_ROOT}/skills/smart-fathom/SKILL.md`.

## Parse Arguments

`$ARGUMENTS` → `<pack-name>` (required, kebab-case).

If missing, prompt with AskUserQuestion.

## Detect Project

If `pyproject.toml` has `name = "fathom-rules"`, target dir is `rule-packs/<pack-name>/`. Otherwise, target dir is `<cwd>/<pack-name>/` and the pack is standalone.

## Interview

1. **Description?** (one line)
2. **License?** (default MIT)
3. **What domain?** (e.g., access-control, compliance, routing, custom)
4. **Decision space?** (e.g., allow/deny/escalate)
5. **Initial rule sketch?** (skip to add later)

## Delegate

Task tool → `rule-pack-builder` with `pack_name`, `target_dir`, interview answers.

## Report

File tree + `next steps` block (write first template, write first rule, run `/fathom:validate`).
