---
description: Scaffold a Nautilus routing rule pack (extends data-routing-nist / data-routing-hipaa pattern)
argument-hint: <pack-name>
allowed-tools: [Bash, Read, Write, AskUserQuestion, Task]
---

# New Routing Rule Pack

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-nautilus/SKILL.md` and `${CLAUDE_PLUGIN_ROOT}/skills/smart-fathom/SKILL.md` if present (Nautilus packs are Fathom packs).

## Delegate

If a Fathom plugin command `/fathom:new-rule-pack` is available, delegate. Otherwise, scaffold directly:

```
rule-packs/<pack-name>/
  pack.yaml
  templates/source.yaml          # source template
  templates/request.yaml         # request template
  rules/route-default.yaml
  modules/routing.yaml
  tests/test_routing.py
  README.md
```

## Report

File tree + test status.
