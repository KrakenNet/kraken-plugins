# Fathom Plugin

Slash commands and agents for authoring + operating Fathom CLIPS rule packs.

## Commands

| Command | Purpose |
|---|---|
| `/fathom:new-rule-pack <name>` | Scaffold a rule pack |
| `/fathom:new-template <pack> <name>` | Add a deftemplate |
| `/fathom:new-rule <pack> <name>` | Add a defrule |
| `/fathom:validate [path]` | Run `fathom validate` |
| `/fathom:test [path]` | Run rule-pack tests |
| `/fathom:bench [path]` | Run `fathom bench` |
| `/fathom:evaluate` | POST /v1/evaluate |
| `/fathom:reload-rules` | POST /v1/rules/reload (≥0.4.0) |
| `/fathom:verify-artifact <path>` | Verify detached `.sig` |
| `/fathom:info` | Engine info, current ruleset hash |

## Agents

- `rule-pack-builder`
- `rule-author`
- `evaluator`
- `verifier`

## Skills

- `smart-fathom` — foundation skill for engine API, YAML schema, REST/gRPC endpoints, CLI.
- `smart-kraken` — cross-project detection (shared duplicate).

## Install

```bash
claude plugins marketplace add ./kraken-plugins
claude plugins install fathom
```
