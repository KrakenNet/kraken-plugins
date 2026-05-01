# Kraken Plugins

A Claude Code / Cursor plugin marketplace covering the Kraken Networks stack:

| Plugin | Purpose | Version |
|---|---|---|
| **railyard** | Guided ops for the Railyard platform (agents, workflows, KGs, ML, …) | 1.2.0 |
| **kb** | Knowledge-base lifecycle for any Kraken project | 0.3.0 |
| **fathom** | Author + operate Fathom CLIPS rule packs | 0.1.0 |
| **nautilus** | Author + operate Nautilus data brokers | 0.1.0 |
| **harbor** | Author Harbor orchestration graphs, skills, tools, markdown SKILL.md skills, directory plugins | 0.3.0 |

## Install (Claude Code)

```bash
claude plugins marketplace add KrakenNet/kraken-plugins
claude plugins install railyard kb fathom nautilus harbor
```

## Install (Cursor)

```bash
cursor plugins marketplace add KrakenNet/kraken-plugins
cursor plugins install railyard kb fathom nautilus harbor
```

## Plugin entry points

After install, type `/help` in Claude Code or Cursor to see all slash commands. Each plugin's commands are namespaced with its short name:

- `/railyard:*` — Railyard ops
- `/kb:*` — KB lifecycle
- `/fathom:*` — Fathom rule pack authoring + ops
- `/nautilus:*` — Nautilus broker authoring + ops
- `/harbor:*` — Harbor graph authoring + light ops

See each plugin's directory under `plugins/` for its README and command list.

## Project repos

| Plugin | Project |
|---|---|
| railyard, kb | <https://github.com/KrakenNet/railyard> |
| fathom | <https://github.com/KrakenNet/fathom> |
| nautilus | <https://github.com/KrakenNet/nautilus> |
| harbor | <https://github.com/KrakenNet/harbor> |

## Contributing

Each plugin lives at `plugins/<name>/`. Conventions:
- Slash commands → `commands/*.md`
- Task-tool agents → `agents/*.md`
- Skills → `skills/<skill-name>/SKILL.md`
- Reference docs (loaded on demand) → `references/*.md`
- Manifest → `.claude-plugin/plugin.json`

Linting and validation: `make lint` (see `scripts/`).

## License

MIT — see [LICENSE](LICENSE).
