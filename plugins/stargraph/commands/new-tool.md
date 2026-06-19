---
description: Create a Stargraph @tool — ToolSpec with namespace/version, side-effects, replay policy, capability gate
argument-hint: <tool-name>
allowed-tools: [Bash, Read, Write, AskUserQuestion]
---

# New Tool

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-stargraph/SKILL.md`.

## Interview

1. **Namespace + version?** (e.g. `namespace="nautilus"`, `version="1"`). The
   registry key is `f"{namespace}.{name}@{version}"` (e.g. `nautilus.broker_request@1`).
2. **Signature?** Type hints drive auto-derived `input_schema` / `output_schema`
   (via `pydantic.create_model` + `TypeAdapter`). Pass `input_schema=` /
   `output_schema=` explicitly only for `Annotated`/positional-only/`BaseModel`
   cases.
3. **Side effects?** `SideEffects`: `none` | `read` | `write` | `external`. The
   `cleared` serve profile refuses `write`/`external`.
4. **Replay policy?** `ReplayPolicy` (kebab): `must-stub` | `fail-loud` |
   `recorded-result`. Default is derived from `side_effects` (none/read →
   `recorded-result`; write/external → `must-stub`) — override only when needed.
5. **Required capability?** `requires_capability="..."` → stored on
   `ToolSpec.permissions`; the gate raises `CapabilityError` before the call.

## Write

```python
# tools/<name>.py
from stargraph.tools import SideEffects, tool

@tool(
    name="<name>",
    namespace="<ns>",
    version="1",
    side_effects=SideEffects.read,
    requires_capability="tools:<ns>:read",
)
async def <name>(*, arg1: str) -> dict:
    """First line becomes the description if none is passed."""
    ...
```

The decorator wraps the callable (sync or async) and exposes `wrapper.spec`
(a `ToolSpec`). Schemas are auto-derived from type hints when omitted.

## Wire into a graph

Tools enter the registry via the plugin entry-point group `stargraph.tools`
(`register_tools() -> list[ToolSpec]`, returning `[<name>.spec]`). A graph node
references the tool by its registry key:

```yaml
nodes:
  - id: ask
    kind: tool
    tool: <ns>.<name>@1
```

## Report

Tool module path, the registry key `<ns>.<name>@<version>`, `side_effects` /
`replay_policy`, required capability, and the `register_tools` entry-point line
needed in the owning plugin's `pyproject.toml`.
