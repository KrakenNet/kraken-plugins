---
description: Add a defrule YAML file to an existing Fathom rule pack with conditions and actions
argument-hint: <pack> <rule-name>
allowed-tools: [Bash, Read, Write, AskUserQuestion, Task]
---

# New Rule

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-fathom/SKILL.md`.

## Parse Arguments

`<pack>` + `<rule-name>`. Both required.

## Interview

1. **Natural-language description** of what should match and what should happen.
2. **Templates referenced?** (list existing templates in pack)
3. **Output decision?** (allow|deny|escalate|custom)
4. **Test cases?** (input → expected decision)

## Delegate

Task tool → `rule-author` agent with description + templates + decision + test cases. Agent drafts a `defrule` and matching pytest cases.

## Report

Rule YAML + tests + `fathom validate` + `fathom test` results.
