---
description: Wire a Store provider for a Harbor graph (vector/graph/doc/memory/fact)
argument-hint: add <type> <provider> [--config <json>]
allowed-tools: [Bash, Read, Write, AskUserQuestion]
---

# Harbor Store

## Subcommand: add

`<type>` ∈ {vector, graph, doc, memory, fact}. `<provider>` ∈ {lancedb, kuzu, sqlite, ...}.

## Steps

1. Read `harbor.yaml`.
2. Insert `stores: <type>: <provider>:<config-uri>`.
3. Validate via `harbor graph verify`.

## Report

YAML diff + verify status.
