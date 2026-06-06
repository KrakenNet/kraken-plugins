---
description: Wire a Store provider for a Stargraph graph (vector/graph/doc/memory/fact)
argument-hint: add <type> <provider> [--config <json>]
allowed-tools: [Bash, Read, Write, AskUserQuestion]
---

# Stargraph Store

## Subcommand: add

`<type>` ∈ {vector, graph, doc, memory, fact}. `<provider>` ∈ {lancedb, kuzu, sqlite, ...}.

## Steps

1. Read `stargraph.yaml`.
2. Insert `stores: <type>: <provider>:<config-uri>`.
3. Validate via `stargraph graph verify`.

## Report

YAML diff + verify status.
