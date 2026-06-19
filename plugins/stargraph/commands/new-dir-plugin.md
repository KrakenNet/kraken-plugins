---
description: Scaffold an entry-point Stargraph plugin — pip package + pyproject entry-points + stargraph_plugin manifest factory + capability hooks
argument-hint: <plugin-name>
allowed-tools: [Bash, Read, Write, AskUserQuestion, Task]
---

# New Plugin (entry-point)

Stargraph plugins are normal pip packages discovered via `importlib.metadata`
entry points, then wired through `pluggy` hooks. There are no directory plugins:
a distribution declares a `stargraph_plugin` manifest factory plus one or more
capability groups in `pyproject.toml`. The reference archetype is
`stargraph.plugins.pii_guard` (a `@tool`-decorated redaction coroutine plus
governance hooks).

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-stargraph/SKILL.md`.

## Interview

1. **Distribution + package name?** (`name` field on the manifest; the import package, e.g. `my_pkg`)
2. **Namespaces it claims?** (`namespaces: list[str]`; conflicts abort load)
3. **What does it provide?** (`provides: list["tool"|"skill"|"store"|"pack"]`) — combine any of:
   - **Tools** (`stargraph.tools` group, `register_tools`) — scaffold each via `/stargraph:new-tool`
   - **Skills** (`stargraph.skills` group, `register_skills`) — `/stargraph:new-skill`
   - **Bosun packs** (`stargraph.packs` group, `register_packs`) — `/stargraph:new-pack`
   - **Stores** (`stargraph.stores` group, `register_stores`) — `/stargraph:store`
4. **Cross-cutting hooks?** (optional `authorize_action` first-deny gate;
   `before_tool_call` / `after_tool_call` audit; `stargraph_startup` /
   `stargraph_shutdown`)

## Layout (pii_guard archetype)

```
my_pkg/
  __init__.py        # docstring
  _plugin.py         # @hookimpl register_tools() -> [my_tool.spec]; manifest factory
  hooks.py           # authorize_action default-deny + before/after_tool_call audit
  redact.py          # the @tool-decorated coroutine (or your capability module)
pyproject.toml
```

`_plugin.py` exposes a `manifest` factory returning a `PluginManifest`
(`name`, `version`, `api_version="1"`, `namespaces`, `provides`, `order` 0..10000
default 5000), and the `register_*` hookimpls. Import hookimpls from
`stargraph.plugin import hookimpl` (or `stargraph.plugin._markers`).

```toml
# pyproject.toml
[project.entry-points."stargraph"]
stargraph_plugin = "my_pkg._plugin:manifest"

[project.entry-points."stargraph.tools"]
my_tool = "my_pkg.redact:redact_pii"
```

## Delegate

Task tool → `dir-plugin-builder`. The agent:

1. Creates the package + `pyproject.toml` with the `stargraph` manifest factory
   entry-point and the relevant capability-group entries.
2. Calls sibling agents per requested artifact (tool-builder, skill-builder, pack-builder).
3. Installs the package (`uv add .` / `pip install -e .`).

## Verify

Plugins are discovered at process start. Run any subcommand with
`STARGRAPH_TRACE_PLUGINS=1` to trace discovery → manifest validation →
registration:

```bash
STARGRAPH_TRACE_PLUGINS=1 uv run stargraph run <graph.yaml> --inspect
```

List the registered kinds against a running server: `GET /v1/registry/{kind}`
(`tool` / `skill` / `store` / `pack`).

## Report

- Tree of the package + the `pyproject.toml` entry-point tables.
- Plugin-trace output confirming discovery + registration.
- Any namespace conflicts or unsigned-pack warnings, with remediation hints.
