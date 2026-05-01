---
description: Build, validate, and append source blocks to nautilus.yaml. Validates against the schema; runs broker config-check.
tools: [Bash, Read, Write, Edit]
---

# Source Builder

## Inputs

- `config_path`
- All interview answers from `/nautilus:new-source`.

## Steps

1. Read `config_path`.
2. Confirm `id` is unique within `sources:`.
3. Build the source block (YAML, properly indented).
4. Append to `sources:` list.
5. Validate:

```bash
uv run nautilus health --config "$config_path"
uv run python -c "from nautilus import Broker; Broker.from_config('$config_path'); print('OK')"
```

6. If broker init fails, parse error, propose fix.

## Build-Test-Fix

Max 5 iters.

## Output

YAML diff + validation + suggestion to start broker:

```bash
uv run nautilus serve --config "$config_path"
```
