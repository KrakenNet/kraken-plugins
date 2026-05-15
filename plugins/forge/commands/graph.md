---
description: Forge spec graph operations — rebuild index, query, get task context, list open questions, export to graphify.
argument-hint: [status | rebuild | query <kw> | context-for-task <id> | open-questions [--topic X] | export-graphify]
allowed-tools: [Bash]
---

# /forge:graph

Spec graph is a SQLite-backed index over `.forge/*.md` + `.forge/prd.json`. Used by Phase 1 agents and Ralph Loop to query focused context (~1-2k tokens) instead of re-reading whole spec files (~15k tokens).

## Usage

```bash
# overview
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/forge_graph.py" status

# rebuild from current .forge/ contents (idempotent)
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/forge_graph.py" rebuild

# keyword/tag search
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/forge_graph.py" query "auth middleware" --max-tokens 1500

# task context bundle (use this BEFORE reading source files)
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/forge_graph.py" context-for-task auth-middleware --max-tokens 2000

# open questions (optionally filtered by topic)
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/forge_graph.py" open-questions --topic auth

# export to graphify-compatible JSONL
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/forge_graph.py" export-graphify --out .forge/memory/graph-export.jsonl
```

## When to rebuild

- After Phase 1 stage completes (PRD written, shared.md written, reviews added)
- After `/forge:scaffold` emits prd.json
- After any manual edit to `.forge/*.md`

Build is fast (sub-second for typical feature). Run liberally.

Parse `$ARGUMENTS` and dispatch. Default to `status`.
