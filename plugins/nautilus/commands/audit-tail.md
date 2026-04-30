---
description: Tail the JSONL audit log; render as a table; offer filters
argument-hint: [--path <path>] [--since <ts>] [--agent-id <id>] [--outcome <o>]
allowed-tools: [Bash, Read]
---

# Audit Tail

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-nautilus/SKILL.md`.

## Run

```bash
tail -n 100 "${NAUTILUS_AUDIT:-./audit.jsonl}" | jq -c 'select(.outcome=="<o>")'
```

Or with date filter:

```bash
awk -v since="$SINCE" '$0 ~ since' "${NAUTILUS_AUDIT}"
```

## Report

Table: timestamp, agent_id, intent (truncated), outcome, sources_queried, sources_denied, audit_id.
