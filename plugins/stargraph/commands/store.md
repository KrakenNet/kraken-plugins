---
description: Wire a Store provider for a Stargraph graph (vector/graph/doc/memory/fact)
argument-hint: add <protocol> <provider> [--config <json>]
allowed-tools: [Bash, Read, Write, AskUserQuestion]
---

# Stargraph Store

## Subcommand: add

`<protocol>` ∈ {`vector`, `graph`, `doc`, `memory`, `fact`} — the five `Store`
protocols. `<provider>` is a provider id; the default embedded tier:

| Protocol | Default provider id          | Compact scheme | Backed by              |
|----------|------------------------------|----------------|------------------------|
| vector   | `stargraph.stores.lancedb`   | `lancedb:`     | LanceDB                |
| graph    | `stargraph.stores.ryugraph` (or `stargraph.stores.cypher`) | `ryugraph:` | RyuGraph (Kuzu fork) |
| doc      | `stargraph.stores.sqlite_doc`    | `sqlite:`  | SQLite (WAL)           |
| memory   | `stargraph.stores.sqlite_memory` | `sqlite:`  | SQLite (WAL)           |
| fact     | `stargraph.stores.sqlite_fact`   | `sqlite:`  | SQLite (WAL) + Fathom  |

## Steps

1. Read the graph IR `stargraph.yaml`.
2. Insert/extend the top-level `stores:` block. Compact form keys by protocol;
   value is `<scheme>:<path>`:

   ```yaml
   stores:
     vector: lancedb:./.lance
     graph:  ryugraph:./.ryu
     doc:    sqlite:./.docs
     memory: sqlite:./.memory
     fact:   sqlite:./.facts
   ```

   The runtime parses each entry into a `StoreRef(name, provider)`, whose
   `to_capabilities()` derives `db.{name}:read` / `db.{name}:write` for the
   Bosun policy gates.
3. Validate by loading: `stargraph run <graph.yaml> --inspect` (rule trace, no
   exec) or `stargraph simulate <graph.yaml> --fixtures <f>`. IRDocument
   validation runs automatically on load (`extra='forbid'`).

## Custom providers

A third-party provider ships as a plugin under entry-point group
`stargraph.stores`, with `register_stores() -> list[StoreSpec]`. A `StoreSpec`
is the canonical registration record: `{name, provider, protocol,
config_schema, capabilities}`. List registered stores against a running server
with `GET /v1/registry/stores`.

## Report

YAML diff + the validation result (`run --inspect` / `simulate`).
