# Harbor Plugin

Slash commands and agents for authoring Harbor graphs, skills, nodes, tools, and Bosun rule packs. Light ops via `harbor serve`.

## Commands

| Command | Purpose |
|---|---|
| `/harbor:new-graph <name>` | Scaffold a graph (state.py, nodes/, rules/, harbor.yaml, tests) |
| `/harbor:new-skill <name>` | Scaffold a skill bundle |
| `/harbor:new-node <graph> <name>` | Add a node |
| `/harbor:new-tool <name>` | Tool definition with JSON Schema |
| `/harbor:new-pack <name>` | New Bosun rule pack |
| `/harbor:run <graph>` | Execute graph against harbor serve |
| `/harbor:replay <run_id> [--from <checkpoint>]` | Replay run |
| `/harbor:checkpoints <run_id>` | List checkpoints |
| `/harbor:verify-graph <graph>` | Validate graph hash + schema |
| `/harbor:store add <type> <provider>` | Wire a Store provider |

## Agents

- `graph-builder`
- `skill-builder`
- `node-builder`
- `runner`
- `pack-builder`

## Skills

- `smart-harbor`
- `smart-kraken`

## Install

```bash
claude plugins marketplace add ./kraken-plugins
claude plugins install harbor
```
