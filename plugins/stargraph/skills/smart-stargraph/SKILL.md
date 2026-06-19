---
name: smart-stargraph
description: Core skill for all Stargraph plugin commands and agents — vocabulary, state-fact boundary, provenance, store protocols, Bosun rule-pack mounting, stargraph serve, project detection.
version: 1.0.0
user-invocable: false
---

# Smart Stargraph

## Configuration

| Setting | Default | Override |
|---|---|---|
| Local install | `uv add stargraph` (or `pip install stargraph`) | — |
| Serve URL | `http://localhost:8000` | `--server` on `stargraph respond`; `--host`/`--port` on `stargraph serve` |
| Profile | `oss-default` | `--profile` flag / `STARGRAPH_PROFILE` (`oss-default`/`cleared`) |
| Project config | `stargraph.toml` (CWD) | `STARGRAPH_TOML_FILENAME` |
| Runtime config dir | `~/.config/stargraph/` (`triggers.yaml`, `nautilus.yaml`) | `STARGRAPH_CONFIG_DIR` |
| Local run artifacts | `./.stargraph/run.sqlite`, `./.stargraph/runs/<run_id>/` | `--checkpoint` / `--db` |
| Plugin-discovery trace | off | `STARGRAPH_TRACE_PLUGINS=1` |

## Project Detection

`pyproject.toml` `name = "stargraph"` → contributor mode (scan `src/stargraph/`, `design-docs/`, `specs/`, `docs/`).

## Vocabulary

| Term | Definition |
|---|---|
| Graph | IR definition (`IRDocument`): nodes, state schema, rules, governance. Blueprint, not running thing. Authored as an `*.yaml` IR file (often `stargraph.yaml`). |
| Run | Single execution of a graph. `run_id` is a UUIDv7; counterfactual forks are `cf-<uuid>`. |
| Node | Unit of work. Builtin `kind` (`echo`, `halt`, `dspy`, `ml`, `interrupt`, `passthrough`, `write_artifact`, `retrieval`, `subgraph`, `human_input`) or `module.path:ClassName`. |
| State | Pydantic-typed bundle flowing through a run (`state_class: module:Class` or flat `state_schema`). |
| Annotated state | Subset mirrored into CLIPS facts at node boundaries. Replay-safe: use `frozenset`, never `set`. |
| Fact | CLIPS tuple — mirrored from annotated state, emitted by runtime, or asserted by rules. |
| Rule | Fathom/CLIPS production matching facts; `then` emits actions (`goto`/`parallel`/`halt`/`interrupt`/…). |
| Pack | Versioned named rule collection (Bosun). Mounted via IR `governance:` (`{id, version, requires}`). |
| Tool | `@tool`-decorated typed callable. Registry key `namespace.name@version`. SideEffects + ReplayPolicy. |
| Skill | Python `stargraph.skills.Skill` (Pydantic): tools, optional subgraph, prompt, `state_schema` write-whitelist. |
| Plugin | Pip-installable Python package registered via `pyproject.toml` entry points. Ships tools/skills/stores/packs/triggers. |
| Store | Data tier abstraction — `vector` / `graph` / `doc` / `memory` / `fact`. |
| Provider | Concrete Store impl (LanceDB, RyuGraph, SQLite, …). |
| Checkpoint | Persisted snapshot at a node transition (SQLite checkpointer). |
| Graph hash | Canonical IR hash (topology + node signatures + state schema). |
| Trigger | Run initiator — `manual` / `cron` / `webhook` (authored in `triggers.yaml`). |

## State-Fact Boundary

- Mutate State freely inside a node (Python).
- On node exit, mirror annotated fields into CLIPS, fire rules, persist checkpoint.
- Source of truth: State. Facts are projection. `set`/`set[X]` on `state_schema` is rejected — use `frozenset`.

## Provenance-typed Facts

Tool/node outputs carry a `__stargraph_provenance__` envelope: `{origin, source, external_id}`.
Documented `origin` values: `tool`, `llm`, `rule`, `system`. Facts carry provenance + run_id/step.

## Stores

Protocols: `vector`, `graph`, `doc`, `memory`, `fact`. Default providers (embedded): LanceDB
(`stargraph.stores.lancedb`), RyuGraph/cypher (`stargraph.stores.ryugraph` / `stargraph.stores.cypher`),
SQLite (`stargraph.stores.sqlite_doc` / `sqlite_memory` / `sqlite_fact`). Capabilities: `db.{name}:read|write`.

## Graph IR (sketch)

The validated runnable shape is `IRDocument` (`extra='forbid'` — unknown keys rejected on load):

```yaml
ir_version: "1.0.0"
id: "graph:research"
state_class: "graph.state:State"      # or flat state_schema: {message: "str", severity: "int"}
nodes:
  - { id: think, kind: dspy }
  - { id: act, kind: "graph.nodes:SearchNode" }
  - { id: halt, kind: halt }
rules:
  - id: r-think-to-act
    when: "?n <- (node-id (id think))"
    then: [{ kind: goto, target: act }]
governance:
  - id: stargraph.bosun.budgets
    version: "1.0"
    requires: { stargraph_facts_version: "1.0", api_version: "1" }
stores:
  - { name: kb, provider: stargraph.stores.lancedb }
```

Skill **bundles** (e.g. Shipwright) use a richer authoring `stargraph.yaml` (`state:`, `nodes: [{name,type}]`,
`rules: [{pack:}]`, `stores: {doc:,fact:}`, `checkpoints:`) alongside `manifest.yaml` + `state.py` + `nodes/`.

## Graph Hash

Canonical IR hash (`dumps_canonical`, sorted keys). Checkpoints carry the hash. Resume rejects on
mismatch unless a `migrate:` block maps `from_hash`→`to_hash`.

## REST + WS Endpoints (stargraph serve, v1)

| Verb | Path | Purpose |
|---|---|---|
| POST | /v1/runs | start a run (`graph_id` + `params`) |
| GET | /v1/runs | list runs (paged) |
| GET | /v1/runs/{id} | run status / RunSummary |
| POST | /v1/runs/{id}/cancel | cancel |
| POST | /v1/runs/{id}/pause | pause |
| WS | /v1/runs/{id}/stream | stream run events |
| POST | /v1/runs/{id}/respond | deliver HITL response |
| POST | /v1/runs/{id}/counterfactual | fork counterfactual |
| GET | /v1/runs/{id}/artifacts | list run artifacts |
| GET | /v1/artifacts/{id} | fetch an artifact |
| GET | /v1/graphs | list registered graphs |
| GET | /v1/registry/{kind} | list registered tools/skills/stores |

## CLI

Eight subcommands (typer app `stargraph.cli:main`):
`stargraph run / serve / inspect / replay / respond / simulate / counterfactual / verify-audit`.

- Validate a graph: `stargraph run GRAPH --inspect` (rule trace, no exec) or `stargraph simulate GRAPH --fixtures FILE`.
- Inspect a run: `stargraph inspect RUN_ID --db DB` (timeline), `--step N` (state), `--diff N M` (CLIPS fact delta).

## Verify-Before-Call

1. `GET /v1/graphs` — confirm graph registered before starting a run.
2. After `POST /v1/runs`, `GET /v1/runs/<id>` — confirm it left pending.
3. Parse error envelopes; map 401/404/409 (don't retry blindly).

(There is no `/health` or `/ready` probe — use `GET /v1/graphs`.)

## Build-Test-Fix

Same 5-iter pattern.

## Authoring Formats

| Artifact | How | Command |
|---|---|---|
| Tool | `@tool`-decorated callable → entry-point group `stargraph.tools` | `/stargraph:new-tool` |
| Skill | Python `Skill` (single file or bundle dir) → `register_skills`, group `stargraph.skills` | `/stargraph:new-skill`, `/stargraph:new-md-skill` (bundle) |
| Plugin | Pip package + `pyproject.toml` entry points + `stargraph_plugin` manifest factory | `/stargraph:new-dir-plugin` |
| Pack | Bosun rule pack → group `stargraph.packs`, Ed25519/JWS signed | `/stargraph:new-pack` |
| Trigger | Entry in `~/.config/stargraph/triggers.yaml`, or trigger plugin under `stargraph.triggers` | `/stargraph:new-trigger` |

All capability kinds register through pluggy hookspecs: `register_tools`, `register_skills`,
`register_stores`, `register_packs`, plus the `trigger_*` family. Discovery is via entry points only
(no directory scanning); trace it with `STARGRAPH_TRACE_PLUGINS=1`.
