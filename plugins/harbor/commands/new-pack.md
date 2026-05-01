---
description: Scaffold a Bosun rule pack (routing or governance flavor) using Fathom rule patterns
argument-hint: <pack-name> [--flavor routing|governance]
allowed-tools: [Bash, Read, Write, AskUserQuestion, Task]
---

# New Bosun Pack

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-harbor/SKILL.md` and the Fathom plugin's `smart-fathom` if installed.

## Interview

1. **Flavor?** (routing | governance)
2. **What does it govern/route?**
3. **Initial rule sketches?**

## Delegate

Task tool → `pack-builder`. If flavor=governance, scaffold a budget/audit/retry pack template.

## Report

Tree + validate result.
