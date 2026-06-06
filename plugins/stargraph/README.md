# Stargraph Plugin

Slash commands, agents, and skills for authoring **and operating**
[Stargraph](https://github.com/KrakenNet/stargraph) — the stateful agent-graph
framework with deterministic governance via Fathom.

Covers the full Stargraph CLI surface (`run`, `serve`, `inspect`, `replay`,
`counterfactual`, `respond`, `simulate`) plus authoring (graphs, nodes, tools,
skills, triggers, Bosun rule packs) and store wiring.

## Commands

### Authoring

| Command | Purpose |
|---|---|
| `/stargraph:new-graph <name>` | Scaffold a graph (state.py, nodes/, rules/, stargraph.yaml, tests). |
| `/stargraph:new-node <graph> <name>` | Add a typed node (DSPy / ML / tool / retrieval / sub-graph). |
| `/stargraph:new-tool <name>` | Tool definition with JSON Schema + namespace + permissions + side-effects. |
| `/stargraph:new-skill <name>` | Skill bundle — tools, optional sub-graph, prompt fragment (pip-package format). |
| `/stargraph:new-md-skill <name>` | Lightweight `SKILL.md` (YAML + markdown) compiled by `stargraph-md-skills` to a typed `Skill`. |
| `/stargraph:new-dir-plugin <name>` | Drop-in directory plugin under `~/.stargraph/plugins/` discovered by `stargraph-dir-plugins`. |
| `/stargraph:new-pack <name> [--flavor routing\|governance]` | New Bosun-compatible rule pack. |
| `/stargraph:new-trigger <graph> --type manual\|cron\|webhook` | Wire a trigger and verify scheduler pickup. |
| `/stargraph:store add <type> <provider>` | Wire a Store provider (vector/graph/doc/memory/fact). |
| `/stargraph:verify-graph <graph>` | Validate hash + schema + referenced rule packs + store providers. |

### Operations

| Command | Purpose |
|---|---|
| `/stargraph:serve [--profile dev\|prod\|cleared]` | Start `stargraph serve` (FastAPI HTTP+WS). |
| `/stargraph:run <graph> [--input-file <json>]` | Execute a graph; stream events; return run_id. |
| `/stargraph:simulate <graph> [--seed <n>]` | Dry-run with deterministic stubs for side-effecting tools. |
| `/stargraph:inspect <run_id> [--events] [--facts]` | Run header, checkpoints, events, facts, provenance breakdown. |
| `/stargraph:checkpoints <run_id>` | List checkpoints with state-diff summaries. |
| `/stargraph:replay <run_id> [--from <cp>]` | Deterministic replay from a checkpoint. |
| `/stargraph:counterfactual <run_id> --from <step> --mutate <json>` | Fork a run with mutated facts/state; diff vs original. |
| `/stargraph:respond <run_id> --decision approve\|deny\|input` | Resume a paused (HITL) run. |

## Agents

| Agent | Purpose |
|---|---|
| `graph-builder` | Scaffolds + verifies graphs (state.py, nodes/, rules/, stargraph.yaml, tests). |
| `node-builder` | Adds typed nodes; manages state-fact boundary; updates graph hash. |
| `pack-builder` | Scaffolds Bosun rule packs (routing or governance flavor); validates as Fathom-compatible. |
| `skill-builder` | Builds skill bundles with tools, sub-graphs, prompt fragments (pip-package format). |
| `md-skill-builder` | Authors a `SKILL.md` and validates via `stargraph skills compile`. |
| `dir-plugin-builder` | Scaffolds a `~/.stargraph/plugins/<name>/` dir-plugin; verifies via `stargraph plugins verify` + live reload. |
| `runner` | Drives run / replay / checkpoints; polls run state and parses events. |
| `hitl-driver` | Lists paused runs, validates payloads against schema, drives `/respond`. |

## Skills

- `smart-stargraph` — vocabulary, state-fact boundary, provenance, Stores, Bosun
  mounting, project detection. Loaded by every command.
- `smart-kraken` — shared cross-project conventions for the Kraken stack
  (monorepo detection, verify-before-call patterns).

## References

Loaded on demand by the commands and agents above:

- `stargraph-concepts.md` — full glossary + disambiguations.
- `graph-yaml-schema.md` — `stargraph.yaml` shape.
- `state-schema.md` — Pydantic + annotated-state mirroring rules.
- `provenance-facts.md` — `(origin, source, run_id, step, confidence, ts)`.
- `store-protocols.md` — Vector / Graph / Doc / Memory / Fact contracts.
- `triggers.md` — manual / cron / webhook config patterns + scheduler semantics.
- `bosun-packs.md` — routing vs governance flavor; in-tree pack catalog.
- `hitl-patterns.md` — pause shapes, schema validation, audit facts, cleared-profile rules.

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
| Serve URL | `http://localhost:9000` | `STARGRAPH_URL` |
| Auth token | none | `STARGRAPH_TOKEN` |
| Graphs dir | `./graphs` | `STARGRAPH_GRAPHS_DIR` |
| Profile | `dev` | `STARGRAPH_PROFILE` (`dev`/`prod`/`cleared`) |

## Version

0.3.0 — adds lightweight authoring formats: `SKILL.md` (compiled by
`stargraph-md-skills` to a typed `Skill`) and directory-based plugins under
`~/.stargraph/plugins/` (discovered by `stargraph-dir-plugins`). New commands
(`/stargraph:new-md-skill`, `/stargraph:new-dir-plugin`) and agents
(`md-skill-builder`, `dir-plugin-builder`).

0.2.0 — full ops surface (`serve`, `inspect`, `simulate`, `counterfactual`,
`respond`), trigger authoring (`new-trigger`), HITL driver agent, and three
references (`triggers.md`, `bosun-packs.md`, `hitl-patterns.md`).

See the project [CHANGELOG](https://github.com/KrakenNet/stargraph/blob/main/CHANGELOG.md)
for engine-side changes.
