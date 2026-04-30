---
description: Run `fathom bench` against a rule pack; report µs/eval and regressions vs published targets
argument-hint: [path]
allowed-tools: [Bash, Read]
---

# Fathom Bench

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-fathom/SKILL.md`.

## Run

```bash
uv run fathom bench "$PATH"
```

## Targets

| Operation | Target |
|---|---|
| Single rule eval | <100µs |
| 100-rule eval | <500µs |
| Fact assertion | <10µs |
| YAML compilation | <50ms |

## Report

Each metric vs target with ✓/⚠/✗. Suggest profiling if any ⚠/✗.
