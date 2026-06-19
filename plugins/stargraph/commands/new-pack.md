---
description: Scaffold a Bosun rule pack (CLIPS rules + PackSpec) and mount it via IR governance
argument-hint: <pack-name> [--flavor routing|governance]
allowed-tools: [Bash, Read, Write, AskUserQuestion, Task]
---

# New Bosun Pack

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-stargraph/SKILL.md` and the Fathom plugin's `smart-fathom` if installed.

## Interview

1. **Flavor?** (routing | governance)
2. **Pack id?** Slug form like `stargraph.bosun.budgets`, `stargraph.bosun.audit`,
   or `soc-policy`. The version is a SEPARATE field.
3. **What does it govern/route?**
4. **Initial CLIPS rule sketches?** (packs carry CLIPS rules, e.g. `rules.clp`)

## Mount into a graph

A pack is mounted in the IRDocument `governance:` list as a `PackMount`
(`{id, version, requires}`), where `requires` is a `PackRequires`
(`stargraph_facts_version`, `api_version`):

```yaml
governance:
  - id: <pack-name>
    version: "1.0"
    requires: { stargraph_facts_version: "1.0", api_version: "1" }
```

`check_pack_compat` enforces `requires` at pack-load time and raises
`PackCompatError` on mismatch (force-loud — no silent drift).

## Distribute as a plugin

Ship the pack as a plugin under entry-point group `stargraph.packs`, with
`register_packs() -> list[PackSpec]`. `PackSpec` is `(id, version, manifest_path)`.

## Signing

Production requires Ed25519/JWS-signed packs (see signing.md). For development
you may generate a fresh keypair; unsigned packs are dev-only.

## Delegate

Task tool → `pack-builder`. If flavor=governance, scaffold a budget/audit/retry
pack template.

## Report

Tree + validation: mount the pack in a graph and run `stargraph run <graph.yaml>
--inspect` (or `simulate`) so the pack loads and `check_pack_compat` passes.
