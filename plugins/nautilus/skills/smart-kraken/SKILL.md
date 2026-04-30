---
name: smart-kraken
description: Shared cross-project skill for Kraken Networks plugins — detect monorepo, project paths, conventions; surface verify-before-call discipline. Duplicated across fathom, nautilus, harbor.
version: 1.0.0
user-invocable: false
---

# Smart Kraken

## Monorepo Detection

```bash
case "$PWD" in
  /home/sean/leagues|/home/sean/leagues/*) MONOREPO=1 ;;
  *) MONOREPO=0 ;;
esac
```

If `MONOREPO=1`, the following paths are canonical:
- `fathom/` — Fathom Python project (rule packs at `rule-packs/`)
- `nautilus/` — Nautilus Python project (config at `nautilus.yaml`)
- `harbor/` — Harbor Python project (graphs at `graphs/` once shipped)
- `bosun/` — Bosun (governance rule packs)
- `railyard/railyard/` — Railyard Go service
- `kraken-plugins/` — this repo
- `kraken-mythos/` — Mythos
- `gcve/` — GCVE pipeline

## Project Identity

- `pyproject.toml` `name = "fathom-rules"` → fathom
- `pyproject.toml` `name = "nautilus-rkm"` → nautilus
- `pyproject.toml` `name = "harbor"` → harbor
- `go.mod` with `module github.com/KrakenNet/railyard` → railyard

## Cross-project Conventions

- **YAML over JSON** for human-edited config (rule packs, graphs, source defs).
- **Pydantic typing** for any Python state objects.
- **Ed25519** for attestations, JWS envelope.
- **JSONL audit logs** for append-only audit sinks.
- **Bearer token auth** for all REST APIs.
- **`/api/v1/health`** standard probe shape (Railyard) or `/health` (Fathom/Nautilus).

## Verify-Before-Call

1. Health check first.
2. List before create.
3. Re-GET after create.
4. Parse error envelopes (don't retry blindly).

## Lint Anchor

This file is byte-identical across all plugins that include it. Run `scripts/lint-smart-kraken.sh` (in `kraken-plugins/`) to enforce.
