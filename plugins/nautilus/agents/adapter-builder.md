---
description: Scaffold a Nautilus adapter package conforming to the Adapter SDK; runs SDK conformance tests; iterates.
tools: [Bash, Read, Write, Edit]
---

# Adapter Builder

## Inputs

- `adapter_name`
- `backing_api`, `auth_model`, `data_types`, `scope_mode`, `test_fixture`

## Steps

1. Create package dir `nautilus-adapter-<adapter_name>/`:
   - `pyproject.toml` with `[project.entry-points."nautilus.adapters"]` registering the adapter.
   - `src/nautilus_adapter_<adapter_name>/__init__.py` exporting `Adapter` class.
   - `src/nautilus_adapter_<adapter_name>/adapter.py` implementing the Adapter Protocol (`query`, `health`, `close`, optional `attest`).
   - `tests/test_conformance.py` using `nautilus.testing.AdapterConformance`.
   - `README.md` with config example.
2. Run conformance:

```bash
uv run pytest tests/test_conformance.py -v
```

3. If `auth_model == OAuth2`, add helper for token refresh.
4. If `scope_mode == native`, document the API permissions mapping.

## Build-Test-Fix

Max 5 iters.

## Output

Tree, conformance result, install command (`uv pip install -e .` from adapter dir).
