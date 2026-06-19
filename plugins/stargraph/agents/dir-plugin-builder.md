---
description: Scaffold an entry-point Stargraph plugin — a pip package whose pyproject declares a `stargraph_plugin` manifest factory plus capability groups (tools/skills/stores/packs); verify discovery via STARGRAPH_TRACE_PLUGINS=1.
tools: [Bash, Read, Write, Edit]
---

# Plugin Builder

Stargraph plugins are **entry-point** plugins: a normal pip package discovered
via `importlib.metadata` entry points + `pluggy` hooks (two-stage loader). There
are no directory/drop-in plugins. The `pii_guard` plugin
(`stargraph.plugins.pii_guard`) is the reference archetype — a `@tool`-decorated
coroutine plus governance hooks.

## Inputs

- `plugin_name` — distribution + package name.
- `namespaces` — dotted namespace prefixes the plugin claims (conflicts abort load).
- `provides` — subset of `{tool, skill, store, pack}`.
- `order` — load priority `0..10000` (default `5000`; collisions raise `PluginLoadError`).

## Steps

1. **Scaffold a pip package** (pii_guard layout):
   ```
   <plugin_name>/
     pyproject.toml
     src/<pkg>/
       __init__.py          (docstring)
       _plugin.py           (manifest factory + register_* hookimpl)
       hooks.py             (authorize_action / before|after_tool_call — optional)
       redact.py            (the @tool-decorated coroutine — example tool)
   ```

2. **Declare entry points in `pyproject.toml`** — the manifest factory under
   group `stargraph`, plus one or more capability groups:
   ```toml
   [project.entry-points."stargraph"]
   stargraph_plugin = "<pkg>._plugin:manifest"     # returns a PluginManifest

   [project.entry-points."stargraph.tools"]
   <pkg> = "<pkg>._plugin:register_tools"
   # also available: stargraph.skills, stargraph.stores, stargraph.packs,
   # stargraph.triggers, stargraph.mcp_adapters
   ```

3. **Write `_plugin.py`** — the manifest factory + a `register_*` collect-all
   hookimpl per capability:
   ```python
   from stargraph.plugin import hookimpl
   from stargraph.ir import PluginManifest, ToolSpec
   from <pkg>.redact import redact_pii

   def manifest() -> PluginManifest:
       return PluginManifest(
           name="<plugin_name>",
           version="0.1.0",
           api_version="1",
           namespaces=[<namespaces>],
           provides=["tool"],
           order=5000,
       )

   @hookimpl
   def register_tools() -> list[ToolSpec]:
       return [redact_pii.spec]   # .spec off the @tool wrapper
   ```

4. **Per artifact, delegate:**
   - tools → the tool-builder (`@tool`, `ToolSpec`, registry key `ns.name@ver`).
   - skills → `skill-builder` (Python `Skill` + `register_skills`).
   - packs → `pack-builder` (group `stargraph.packs`, `register_packs`, signing).
   - stores → wire a `StoreSpec` + `register_stores`.

5. **Optional governance hooks** (`hooks.py`, pii_guard pattern):
   `authorize_action(action) -> bool|None` (first-deny; first non-`None` wins),
   `before_tool_call(call)` / `after_tool_call(call, result)` for audit. Register
   these on the same plugin object.

6. **Install + verify discovery** (there are no plugin verify/inspect/reload CLI subcommands):
   ```bash
   uv pip install -e .
   STARGRAPH_TRACE_PLUGINS=1 stargraph run <any-graph.yaml> --inspect
   ```
   The trace logs every discovery, manifest validation, and registration step
   (with the `order` it registered at). Failure cases:
   - `api_version` not `"1"` → manifest validation fails; pin it.
   - Namespace conflict with another plugin → load aborts; rename the namespace.
   - `order` collision → `PluginLoadError`; pick a distinct order.
   - Import failure in a capability module → trace shows the discovery/registration gap.

   At runtime with `stargraph serve` up, confirm registered kinds via
   `GET /v1/registry/{kind}` (`kind` ∈ `tools`, `skills`, `stores`).

## Build-Test-Fix

5 iterations across the trace + `GET /v1/registry/{kind}`. On signing failures
for packs, regenerate keys only with explicit user confirmation.

## Output

- Tree of the created package.
- `STARGRAPH_TRACE_PLUGINS=1` discovery/validation/registration trace.
- `GET /v1/registry/{kind}` result (or "skipped — serve not running").

## Constraints

- The manifest **must** declare at least one namespace; conflicts abort load.
- Stage-1 manifest validation is import-cold — do not import capability modules
  during scaffolding; rely on the stage-2 trace to exercise imports.
