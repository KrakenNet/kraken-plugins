---
description: Show effective cost caps per source; edit per-source in nautilus.yaml (P0 issue)
argument-hint: [show|edit] [<source-id>]
allowed-tools: [Bash, Read, Write, AskUserQuestion]
---

# Nautilus Cost Caps

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-nautilus/SKILL.md`.

## show

```bash
uv run nautilus cost-caps show --config "${NAUTILUS_CONFIG:-./nautilus.yaml}"
```

## edit

Read `nautilus.yaml`, locate the source's `cost_caps:` block (or insert a new one), interview for: max_tokens, max_duration_seconds, max_tool_calls, enforcement (hard|soft). Write back.

Confirm with AskUserQuestion before save.

## Report

Caps before/after; suggest broker reload (or restart depending on Nautilus version).
