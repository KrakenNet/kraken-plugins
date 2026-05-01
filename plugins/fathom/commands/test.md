---
description: Run rule-pack tests via pytest; surface failures with branch coverage hints
argument-hint: [path]
allowed-tools: [Bash, Read]
---

# Fathom Test

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-fathom/SKILL.md`.

## Run

```bash
uv run pytest "$PATH/tests" -v --tb=short
```

If a `pack.yaml` declares a `decision_space`, also run a coverage check:

```bash
uv run fathom test "$PATH" --branch-coverage
```

## Report

Pass/fail counts, slowest tests, decision branches not covered.
