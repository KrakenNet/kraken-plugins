# Stargraph Plugin

Slash commands, agents, and skills for authoring **and operating**
[Stargraph](https://github.com/KrakenNet/stargraph) — the stateful agent-graph
framework with deterministic governance via Fathom.

Covers the full Stargraph CLI surface (`run`, `serve`, `inspect`, `replay`,
`counterfactual`, `respond`, `simulate`, `verify-audit`) plus authoring (graphs,
nodes, tools, skills, triggers, Bosun rule packs) and store wiring.

## Commands

### Authoring

| Command | Purpose |
|---|---|
| `/stargraph:new-graph <name>` | Scaffold an `IRDocument` graph YAML (`ir_version`, `id`, nodes, rules, governance, state). |
| `/stargraph:new-node <graph> <name>` | Add a `NodeSpec` (builtin `kind` — dspy/ml/interrupt/retrieval/subgraph/… — or `module:Class`). |
| `/stargraph:new-tool <name>` | `@tool`-decorated callable + `ToolSpec` (namespace, side-effects, replay policy, capabilities). |
| `/stargraph:new-skill <name>` | Python `stargraph.skills.Skill` plugin — tools, optional subgraph, prompt, `state_schema`. |
| `/stargraph:new-md-skill <name>` | Skill **bundle** dir (`manifest.yaml` + `stargraph.yaml` + `state.py` + `nodes/`), Shipwright-style. |
| `/stargraph:new-dir-plugin <name>` | Entry-point plugin — pip package + `pyproject` entry points + `stargraph_plugin` manifest factory. |
| `/stargraph:new-pack <name> [--flavor routing\|governance]` | Bosun rule pack (group `stargraph.packs`, Ed25519/JWS signed). |
| `/stargraph:new-trigger <graph> --type manual\|cron\|webhook` | Add a trigger to `triggers.yaml`; verify `stargraph serve` pickup. |
| `/stargraph:store add <protocol> <provider>` | Wire a Store (vector/graph/doc/memory/fact) as an IR `StoreRef`. |
| `/stargraph:verify-graph <graph>` | Validate the IR via `run --inspect` / `simulate` + `stargraph.ir.validate`. |

### Operations

| Command | Purpose |
|---|---|
| `/stargraph:serve [--profile oss-default\|cleared]` | Start `stargraph serve` (FastAPI HTTP+WS on :8000). |
| `/stargraph:run <graph> [-i K=V] [--inspect]` | Execute a graph (or print its rule trace); seed state; return run_id. |
| `/stargraph:simulate <graph> --fixtures <yaml>` | Offline rule-firing trace against synthetic node outputs (no tools/LLM/checkpoint). |
| `/stargraph:inspect <run_id> --db <path> [--step N] [--diff N M]` | Timeline / state-at-step / CLIPS fact-delta + provenance. |
| `/stargraph:checkpoints <run_id>` | Checkpoint/state/fact views over the SQLite checkpointer (via `inspect`). |
| `/stargraph:replay <run_id> --db <path> [--mutation <json>] [--from-step N]` | Fork a counterfactual run from a checkpoint; diff vs parent. |
| `/stargraph:counterfactual <graph> --step N --mutate <yaml>` | Compute the cf-derived `graph_hash` for a mutation (no fork). |
| `/stargraph:respond <run_id> --response <json> --actor <name>` | Resume an `awaiting-input` (HITL) run. |

## Agents

| Agent | Purpose |
|---|---|
| `graph-builder` | Builds + validates `IRDocument` graphs; verifies via `simulate` / `run --inspect`. |
| `node-builder` | Adds typed nodes; manages the state-fact boundary; tracks `graph_hash` + `migrate:`. |
| `pack-builder` | Scaffolds Bosun rule packs (routing or governance flavor); signs + mounts via `governance:`. |
| `skill-builder` | Builds Python `Skill` plugins (tools, subgraph, prompt) registered via `register_skills`. |
| `md-skill-builder` | Authors a skill **bundle** dir (Shipwright layout); verifies via `simulate` / `run --inspect`. |
| `dir-plugin-builder` | Scaffolds an entry-point plugin (pii_guard archetype); verifies discovery via `STARGRAPH_TRACE_PLUGINS=1`. |
| `runner` | Drives run / inspect / replay / respond; polls run state and parses events. |
| `hitl-driver` | Finds `awaiting-input` runs, builds the response payload, drives `/respond`. |

## Skills

- `smart-stargraph` — vocabulary, state-fact boundary, provenance, Stores, Bosun
  mounting, CLI/API surface, project detection. Loaded by every command.
- `smart-kraken` — shared cross-project conventions for the Kraken stack
  (monorepo detection, verify-before-call patterns).

## References

Loaded on demand by the commands and agents above:

- `stargraph-concepts.md` — full glossary + disambiguations.
- `graph-yaml-schema.md` — the `IRDocument` graph shape.
- `state-schema.md` — Pydantic state + annotated-state mirroring rules.
- `provenance-facts.md` — the `__stargraph_provenance__` envelope `(origin, source, external_id)`.
- `store-protocols.md` — vector / graph / doc / memory / fact contracts + providers.
- `triggers.md` — `triggers.yaml` schema (manual / cron / webhook) + scheduler semantics.
- `bosun-packs.md` — routing vs governance flavor; PackMount + signing.
- `hitl-patterns.md` — interrupt node/action, `/respond`, capability gate, timeout/on_timeout.

## Install

```bash
claude plugins marketplace add KrakenNet/kraken-plugins
claude plugins install stargraph
```

Or from a local checkout of this repo:

```bash
claude plugins marketplace add ./kraken-plugins
claude plugins install stargraph
```

## Configuration

| Setting | Default | Override |
|---|---|---|
| Local install | `uv add stargraph` | — |
| Serve URL | `http://localhost:8000` | `stargraph serve --host/--port`; `stargraph respond --server` |
| Profile | `oss-default` | `--profile` / `STARGRAPH_PROFILE` (`oss-default`/`cleared`) |
| Project config | `stargraph.toml` (CWD) | `STARGRAPH_TOML_FILENAME` |
| Runtime config dir | `~/.config/stargraph/` | `STARGRAPH_CONFIG_DIR` |

## Version

0.4.0 — reconciled the whole plugin against the real Stargraph CLI/HTTP/plugin
surface: the 8-subcommand CLI (`run`/`serve`/`inspect`/`replay`/`respond`/
`simulate`/`counterfactual`/`verify-audit`), the `IRDocument` graph schema, the
entry-point plugin model (no directory plugins), Python `Skill` bundles (no
markdown SKILL.md compiler), `stargraph.toml` project config, and the real
`/v1/*` API. Replaced the prior fictional `graph verify` / `plugins *` /
`skills compile` / `facts` surfaces with their real equivalents.

0.3.0 — earlier authoring-format work (superseded by 0.4.0).

0.2.0 — full ops surface (`serve`, `inspect`, `simulate`, `counterfactual`,
`respond`), trigger authoring, HITL driver agent, and three references
(`triggers.md`, `bosun-packs.md`, `hitl-patterns.md`).

See the project [CHANGELOG](https://github.com/KrakenNet/stargraph/blob/main/CHANGELOG.md)
for engine-side changes.
