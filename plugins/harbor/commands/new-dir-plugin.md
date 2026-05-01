---
description: Scaffold a directory-based Harbor plugin (drop-in folder under ~/.harbor/plugins/) — skills, tools, packs, stores, plugin.toml
argument-hint: <plugin-name>
allowed-tools: [Bash, Read, Write, AskUserQuestion, Task]
---

# New Directory Plugin

Drop-in plugin layout that `harbor-dir-plugins` discovers from
`$HARBOR_PLUGINS_DIR` (default `~/.harbor/plugins/`). No pip install
required for prototyping; same typed contract, namespace conflict
detection, and audit chain as a pip-installed plugin once registered.

Use this command for personal config, prototyping, or sharing a plugin as
a tarball. Use `/harbor:new-skill` (or the legacy plugin-package
generator) when you want to publish to PyPI.

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-harbor/SKILL.md`.

## Interview

1. **Plugin name?** (becomes the directory name and `name` field)
2. **Namespaces it claims?** (one or more dotted prefixes, conflict-checked)
3. **What does it ship?** Combine any of:
   - **Markdown skills** (`skills/<name>/SKILL.md`) — will call `/harbor:new-md-skill` per skill
   - **Tools** (`tools/*.py`) — will call `/harbor:new-tool` per tool
   - **Bosun packs** (`packs/<name>/`) — will call `/harbor:new-pack` per pack
   - **Stores** (declarative TOML store specs)
4. **Pack signing?** (if shipping packs: provide `[trust].keys` Ed25519 pubkeys, or generate a fresh keypair for development)
5. **Capability declarations?** (any new capability strings the tools/skills require)

## Delegate

Task tool → `dir-plugin-builder`. The agent:

1. Creates `~/.harbor/plugins/<name>/` (or `$HARBOR_PLUGINS_DIR/<name>/`).
2. Writes `plugin.toml` with name, version, api_version, namespaces, trust keys.
3. Calls sibling agents per requested artifact (md-skill-builder, tool-builder, pack-builder).
4. Runs `harbor plugins verify <path>` for offline validation.
5. Runs `harbor plugins reload && harbor plugins inspect <name>` to confirm
   the live `harbor serve` registers it.

## Report

- Tree of the new dir-plugin.
- Output of `harbor plugins verify` and `harbor plugins inspect`.
- Any namespace conflicts or unsigned-pack warnings, with remediation hints.
