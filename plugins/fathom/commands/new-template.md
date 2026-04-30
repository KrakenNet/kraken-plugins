---
description: Add a deftemplate YAML file to an existing Fathom rule pack with typed slots
argument-hint: <pack> <template-name>
allowed-tools: [Bash, Read, Write, AskUserQuestion]
---

# New Template

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-fathom/SKILL.md`.

## Parse Arguments

`<pack>` (path or name) + `<template-name>`. Both required.

## Resolve Pack Dir

If `<pack>` is a path, use it. Else search `rule-packs/<pack>/`.

## Interview

For each slot:
1. Name?
2. Type? (string|int|float|bool|enum|datetime)
3. Required? (default no)
4. If enum, list values.

Loop until user says "done".

## Write

Write `<pack-dir>/templates/<template-name>.yaml`:

```yaml
templates:
  - name: <template-name>
    slots:
      <slot1>: { type: ..., required: ... }
      <slot2>: { type: ..., required: ... }
```

## Report

File path + `fathom validate` result.
