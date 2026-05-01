---
description: Create a Harbor tool definition with JSON Schema + namespace + permissions + side-effect flags
argument-hint: <tool-name>
allowed-tools: [Bash, Read, Write, AskUserQuestion]
---

# New Tool

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-harbor/SKILL.md`.

## Interview

1. **Namespace?** (e.g. `browser`, `db`, `internal`)
2. **Args schema?** (JSON Schema)
3. **Returns schema?**
4. **Permissions?** (read | write | network | filesystem | executes-code)
5. **Side effects?** (none | external-api | local-fs | sends-email | ...)

## Write

```python
# tools/<namespace>/<name>.py
from harbor.tools import tool

@tool(namespace="<ns>", side_effects=[...], permissions=[...])
def <name>(arg1: ..., arg2: ...) -> ...:
    """..."""
    ...
```

JSON Schema is auto-derived from type hints; allow override via decorator args.

## Report

Tool path + adapter notes for DSPy + MCP if applicable.
