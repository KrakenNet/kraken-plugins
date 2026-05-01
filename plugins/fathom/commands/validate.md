---
description: Run `fathom validate` against a rule-pack directory; explain errors
argument-hint: [path]
allowed-tools: [Bash, Read]
---

# Fathom Validate

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-fathom/SKILL.md`.

## Parse Arguments

`[path]` defaults to `./rules/` if present, else `./rule-packs/`, else PWD.

## Run

```bash
uv run fathom validate "$PATH"
```

## Report

If pass: "✓ valid: <N> templates, <M> rules". If fail: parse first error, suggest fix, link to `references/rule-yaml-schema.md` section that applies.
