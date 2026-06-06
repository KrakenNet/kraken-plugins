---
description: Scaffold a Bosun rule pack (routing or governance flavor); validate as a Fathom-compatible pack.
tools: [Bash, Read, Write, Edit]
---

# Pack Builder

## Inputs

- `pack_name`, `flavor` (routing | governance), `description`, `initial_rules`.

## Steps

1. Create `bosun-packs/<pack_name>/` with the Fathom rule-pack layout (`pack.yaml`, `templates/`, `rules/`, `modules/`, `functions/`, `tests/`).
2. For governance flavor, include starter rules for budget tripping, audit emit, retry-with-backoff.
3. Validate via `fathom validate` and `pytest`.

## Build-Test-Fix

5 iters.

## Output

Tree + validate + test status.
