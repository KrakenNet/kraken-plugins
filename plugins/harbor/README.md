# Harbor Plugin

Slash commands, agents, and skills for authoring **and operating**
[Harbor](https://github.com/KrakenNet/harbor) — the stateful agent-graph
framework with deterministic governance via Fathom.

Covers the full Harbor CLI surface (`run`, `serve`, `inspect`, `replay`,
`counterfactual`, `respond`, `simulate`) plus authoring (graphs, nodes, tools,
skills, triggers, Bosun rule packs) and store wiring.

## Commands

### Authoring

| Command | Purpose |
|---|---|
| `/harbor:new-graph <name>` | Scaffold a graph (state.py, nodes/, rules/, harbor.yaml, tests). |
| `/harbor:new-node <graph> <name>` | Add a typed node (DSPy / ML / tool / retrieval / sub-graph). |
| `/harbor:new-tool <name>` | Tool definition with JSON Schema + namespace + permissions + side-effects. |
| `/harbor:new-skill <name>` | Skill bundle — tools, optional sub-graph, prompt fragment (pip-package format). |
| `/harbor:new-md-skill <name>` | Lightweight `SKILL.md` (YAML + markdown) compiled by `harbor-md-skills` to a typed `Skill`. |
| `/harbor:new-dir-plugin <name>` | Drop-in directory plugin under `~/.harbor/plugins/` discovered by `harbor-dir-plugins`. |
| `/harbor:new-pack <name> [--flavor routing\|governance]` | New Bosun-compatible rule pack. |
| `/harbor:new-trigger <graph> --type manual\|cron\|webhook` | Wire a trigger and verify scheduler pickup. |
| `/harbor:store add <type> <provider>` | Wire a Store provider (vector/graph/doc/memory/fact). |
| `/harbor:verify-graph <graph>` | Validate hash + schema + referenced rule packs + store providers. |

### Operations

| Command | Purpose |
|---|---|
| `/harbor:serve [--profile dev\|prod\|cleared]` | Start `harbor serve` (FastAPI HTTP+WS). |
| `/harbor:run <graph> [--input-file <json>]` | Execute a graph; stream events; return run_id. |
| `/harbor:simulate <graph> [--seed <n>]` | Dry-run with deterministic stubs for side-effecting tools. |
| `/harbor:inspect <run_id> [--events] [--facts]` | Run header, checkpoints, events, facts, provenance breakdown. |
| `/harbor:checkpoints <run_id>` | List checkpoints with state-diff summaries. |
| `/harbor:replay <run_id> [--from <cp>]` | Deterministic replay from a checkpoint. |
| `/harbor:counterfactual <run_id> --from <step> --mutate <json>` | Fork a run with mutated facts/state; diff vs original. |
| `/harbor:respond <run_id> --decision approve\|deny\|input` | Resume a paused (HITL) run. |

## Agents

| Agent | Purpose |
|---|---|
| `graph-builder` | Scaffolds + verifies graphs (state.py, nodes/, rules/, harbor.yaml, tests). |
| `node-builder` | Adds typed nodes; manages state-fact boundary; updates graph hash. |
| `pack-builder` | Scaffolds Bosun rule packs (routing or governance flavor); validates as Fathom-compatible. |
| `skill-builder` | Builds skill bundles with tools, sub-graphs, prompt fragments (pip-package format). |
| `md-skill-builder` | Authors a `SKILL.md` and validates via `harbor skills compile`. |
| `dir-plugin-builder` | Scaffolds a `~/.harbor/plugins/<name>/` dir-plugin; verifies via `harbor plugins verify` + live reload. |
| `runner` | Drives run / replay / checkpoints; polls run state and parses events. |
| `hitl-driver` | Lists paused runs, validates payloads against schema, drives `/respond`. |

## Skills

- `smart-harbor` — vocabulary, state-fact boundary, provenance, Stores, Bosun
  mounting, project detection. Loaded by every command.
- `smart-kraken` — shared cross-project conventions for the Kraken stack
  (monorepo detection, verify-before-call patterns).

## References

Loaded on demand by the commands and agents above:

- `harbor-concepts.md` — full glossary + disambiguations.
- `graph-yaml-schema.md` — `harbor.yaml` shape.
- `state-schema.md` — Pydantic + annotated-state mirroring rules.
- `provenance-facts.md` — `(origin, source, run_id, step, confidence, ts)`.
- `store-protocols.md` — Vector / Graph / Doc / Memory / Fact contracts.
- `triggers.md` — manual / cron / webhook config patterns + scheduler semantics.
- `bosun-packs.md` — routing vs governance flavor; in-tree pack catalog.
- `hitl-patterns.md` — pause shapes, schema validation, audit facts, cleared-profile rules.

## Install

```bash
claude plugins marketplace add KrakenNet/kraken-plugins
claude plugins install harbor
```

Or from a local checkout of this repo:

```bash
claude plugins marketplace add ./kraken-plugins
claude plugins install harbor
```

## Configuration

| Setting | Default | Override |
|---|---|---|
| Serve URL | `http://localhost:9000` | `HARBOR_URL` |
| Auth token | none | `HARBOR_TOKEN` |
| Graphs dir | `./graphs` | `HARBOR_GRAPHS_DIR` |
| Profile | `dev` | `HARBOR_PROFILE` (`dev`/`prod`/`cleared`) |

## Version

0.3.0 — adds lightweight authoring formats: `SKILL.md` (compiled by
`harbor-md-skills` to a typed `Skill`) and directory-based plugins under
`~/.harbor/plugins/` (discovered by `harbor-dir-plugins`). New commands
(`/harbor:new-md-skill`, `/harbor:new-dir-plugin`) and agents
(`md-skill-builder`, `dir-plugin-builder`).

0.2.0 — full ops surface (`serve`, `inspect`, `simulate`, `counterfactual`,
`respond`), trigger authoring (`new-trigger`), HITL driver agent, and three
references (`triggers.md`, `bosun-packs.md`, `hitl-patterns.md`).

See the project [CHANGELOG](https://github.com/KrakenNet/harbor/blob/main/CHANGELOG.md)
for engine-side changes.
