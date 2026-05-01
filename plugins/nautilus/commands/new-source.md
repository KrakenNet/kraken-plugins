---
description: Append a source block to nautilus.yaml after an interview; validate against schema
argument-hint: [--config <path>]
allowed-tools: [Bash, Read, Write, AskUserQuestion, Task]
---

# New Source

## Load Foundation

Read `${CLAUDE_PLUGIN_ROOT}/skills/smart-nautilus/SKILL.md`.

## Resolve Config

`--config` or `${NAUTILUS_CONFIG:-./nautilus.yaml}`. Read existing.

## Interview

1. **id?** (kebab-case, unique)
2. **adapter?** (from list of 8 + `nautobot` if available + `llm`)
3. **url / connection?**
4. **classification?** (unclassified|confidential|secret|top_secret)
5. **data_types?** (list)
6. **scope where-clause?** (optional)
7. **cost_caps?** (paste P0-issue block; per_request {max_tokens, max_duration_seconds, max_tool_calls}, enforcement hard|soft)
8. **ingest_integrity?** (rest adapters only; schema path, on_schema_violation, baseline_window, anomaly_sigma)
9. **session_signing?** (llm adapter only; enabled, key_ref, algorithm, ttl)

## Delegate

Task tool → `source-builder` agent.

## Report

Diff of nautilus.yaml + validation result + smoke-test suggestion (`/nautilus:request` against the new source).
