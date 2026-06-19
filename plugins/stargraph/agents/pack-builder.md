---
description: Scaffold a Bosun rule pack (routing or governance flavor) carrying Fathom/CLIPS rules; distribute it as a plugin under the stargraph.packs entry-point group and mount it via IR governance.
tools: [Bash, Read, Write, Edit]
---

# Pack Builder

Builds a **Bosun** governance pack (Fathom/CLIPS rules) that a graph mounts via
its IR `governance:` list. A pack is identified by a slug `id` plus a separate
`version` field (e.g. `stargraph.bosun.budgets` / `soc-policy`) — a slug id with
its own separate `version`, never a combined `name@version`-style string.

## Inputs

- `pack_id` (slug `^[a-z0-9][a-z0-9_\-.]{0,127}$`), `version`,
  `flavor` (routing | governance), `description`, `initial_rules`.

## Steps

1. Create `bosun-packs/<pack_id>/` with the pack layout: `rules.clp` (the CLIPS
   rules), a `manifest_path`-referenced manifest, `templates/`, and `tests/`.
2. For the governance flavor, seed CLIPS rules for budget tripping, audit emit,
   and retry-with-backoff; for routing, seed disposition/route rules. The
   `_pack.py`-style loader splits `rules.clp` into top-level constructs and
   feeds each to `fathom.Engine._env.build` for precise compile-error attribution.
3. Distribute the pack as a plugin: a pip package whose `pyproject.toml`
   declares the manifest factory under group `stargraph` and the pack under
   group `stargraph.packs`. The `register_packs()` hookimpl returns
   `list[PackSpec]`, where `PackSpec = (id, version, manifest_path)`.
4. Mount it from a graph's IR `governance:` (a `PackMount`):

   ```yaml
   governance:
     - id: <pack_id>
       version: "<version>"
       requires: { stargraph_facts_version: "1.0", api_version: "1" }
   ```

   `check_pack_compat` enforces `requires` at pack-load time and raises
   `PackCompatError` on mismatch (force-loud; comparison is pinned-string
   equality in the POC).
5. **Signing:** production requires Ed25519/JWS-signed packs (releases are
   signed with Ed25519, detached `.sig`). Generate/manage the signing key per
   `references/bosun-packs.md`; never silently rotate a key.
6. Validate by mounting the pack on a graph and running the offline rule trace:
   `uv run stargraph simulate <graph.yaml> --fixtures <fixtures.yaml>` (or
   `run --inspect`). Confirm discovery/registration with
   `STARGRAPH_TRACE_PLUGINS=1 stargraph run <graph.yaml> --inspect`, and at
   runtime via `GET /v1/registry/{kind}` when `stargraph serve` is up.

## Build-Test-Fix

5 iters. On a `PackCompatError`, reconcile `requires` against the graph's
declared versions. On a CLIPS compile error, the per-construct loader names the
offending construct — fix only that.

## Output

Tree, simulate/inspect output, pack registration status, signing status.
