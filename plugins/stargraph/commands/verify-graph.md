---
description: Validate a Stargraph graph (hash, schema, referenced rule packs, store providers)
argument-hint: <graph-path-or-name>
allowed-tools: [Bash, Read]
---

# Stargraph Verify Graph

## Run

```bash
uv run stargraph graph verify <graph-path-or-name>
```

## Report

✓ valid, hash=<hex>, summary of nodes/rules/stores. Or ✗ with error block.
