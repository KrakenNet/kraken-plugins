---
description: Scaffold a directory-based Harbor plugin under ~/.harbor/plugins/ or $HARBOR_PLUGINS_DIR; verify via `harbor plugins verify` + live reload.
tools: [Bash, Read, Write, Edit]
---

# Dir-Plugin Builder

Builds a drop-in Harbor plugin discovered by `harbor-dir-plugins`. No pip
install; same typed contract, namespace-conflict detection, signing, and
audit chain as a pip-installed plugin once registered.

## Inputs

- `plugin_name` — directory name and `plugin.toml` `name` field.
- `namespaces` — list of dotted namespace prefixes claimed by the plugin.
- `ships` — combination of `{md_skills, tools, packs, stores}`.
- `trust_keys` — Ed25519 pubkeys for pack signing; if empty and `ships`
  includes packs, generate a dev keypair via `fathom keygen` and persist
  the public half in `plugin.toml`.
- `capabilities` — list of new capability strings to declare (with
  description + sensitivity).
- `target_dir` — default `~/.harbor/plugins/`; honor `$HARBOR_PLUGINS_DIR`
  if set.

## Steps

1. **Scaffold layout:**
   ```
   <target_dir>/<plugin_name>/
     plugin.toml
     skills/                  (if ships includes md_skills)
     tools/                   (if ships includes tools)
       __init__.py
     packs/                   (if ships includes packs)
     stores/                  (if ships includes stores)
     capabilities.toml        (if capabilities declared)
     README.md
   ```

2. **Write `plugin.toml`:**
   ```toml
   name = "<plugin_name>"
   version = "0.1.0"
   api_version = "1.x"
   order = 100
   namespaces = [<namespaces>]

   [author]
   name = ""
   email = ""

   [trust]
   keys = [<trust_keys>]

   [runtime]
   python_path = ["tools"]
   ```

3. **Per artifact, delegate:**
   - For each requested md-skill: invoke `md-skill-builder` with
     `host_path=<target_dir>/<plugin_name>/skills/<skill>/`.
   - For each tool: invoke the tool-builder agent against
     `tools/<name>.py`.
   - For each pack: invoke `pack-builder`; sign with the dev keypair if
     no trust key was supplied.

4. **Capabilities:**
   If `capabilities.toml` was requested, emit one entry per declared cap:
   ```toml
   [capabilities."<name>"]
   description = "<description>"
   sensitivity = "low" | "medium" | "high"
   ```

5. **Offline validation:** run
   `harbor plugins verify <target_dir>/<plugin_name>`. Failure cases to
   diagnose:
   - `api_version` mismatch → bump or pin.
   - Namespace conflict with existing plugin → rename namespace.
   - Unsigned pack with `allow_unsigned=false` → sign or move to
     dev-only path.
   - Tool import failure → check `runtime.python_path`.

6. **Live reload (optional, if `harbor serve` is running):**
   `harbor plugins reload && harbor plugins inspect <plugin_name>`.
   Confirm: tool count, skill count, pack count, signing status, and that
   the audit chain emitted a registration record with the plugin's
   manifest hash.

## Build-Test-Fix

5 iterations across verify + inspect. On signing failures, regenerate
keypair only with explicit user confirmation — never silently rotate keys.

## Output

- Tree of the created dir-plugin.
- `harbor plugins verify` output.
- `harbor plugins inspect <plugin_name>` output (or "skipped — serve not
  running" if applicable).
- Any unsigned-pack warnings + remediation steps.

## Constraints

- The plugin **must** declare at least one namespace; bare-name plugins
  are rejected by the loader.
- If shipping unsigned packs in a path that production policy treats as
  untrusted, surface the warning prominently; do NOT auto-sign with a
  user-pubkey-claiming key.
- Stage-1 manifest validation is import-cold (NFR-7) — do not import
  `tools/` modules during scaffolding; rely on `harbor plugins verify`
  to exercise stage-2 import safely.
