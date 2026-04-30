# Railyard KB Plugin

A Claude Code plugin for managing the Railyard Knowledge Base lifecycle and enforcing KB-driven development.

## Commands

| Command | Description |
|---------|-------------|
| `/kb:init [--quick]` | Bootstrap a KB in the current project |
| `/kb:new [domain/scope]` | Create a new KB article (interactive or `--quick`) |
| `/kb:update <path>` | Refresh an article to match current code |
| `/kb:enrich <path\|domain>` | Add external reference material to articles |
| `/kb:split <path\|domain>` | Decompose oversized articles into focused sub-articles |
| `/kb:audit [domain]` | Find codebase features not covered by the KB |
| `/kb:lint [domain]` | Run health checks on KB consistency |
| `/kb:stale [domain]` | Find articles whose source code has changed |
| `/kb:gaps [path]` | List and manage gap files |
| `/kb:plan [--source] [--issues]` | Turn analysis into prioritized tasks or GitHub issues |

## Skills

- **kb-enforcement** — Auto-triggers on code tasks to load relevant KB articles, check gap files, and warn about staleness
- **kb-conventions** — Shared article format rules loaded by agents

## Agents

- **kb-writer** — Creates and updates KB articles (with automatic source file discovery)
- **kb-auditor** — Runs audit and staleness checks
- **kb-linter** — Runs KB health checks
- **kb-bootstrapper** — Initializes KB structure from project scan
- **kb-planner** — Creates prioritized work plans and GitHub issues from analysis results

## Installation

```bash
claude plugins marketplace add se-jo-ma/railyard-kb-plugin
claude plugins install kb
```
