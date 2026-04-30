---
name: smart-nautilus
description: Core skill for all Nautilus plugin commands and agents — Broker API, nautilus.yaml schema, 8 built-in adapters, REST endpoints, CLI, attestation, audit log, project detection.
version: 1.0.0
user-invocable: false
---

# Smart Nautilus

## Configuration

| Setting | Default | Override |
|---|---|---|
| Local install | `uv add nautilus-rkm` | — |
| REST URL | `http://localhost:8000` | `NAUTILUS_URL` |
| Auth token | none | `NAUTILUS_TOKEN` |
| Config file | `./nautilus.yaml` | `NAUTILUS_CONFIG` |
| Audit log | `./audit.jsonl` | per-source override |

## Project Detection

`pyproject.toml` `name = "nautilus-rkm"` → contributor mode (scan `src/nautilus/`, `tests/`, `nautilus.yaml`).

## Broker API

```python
from nautilus import Broker
broker = Broker.from_config("nautilus.yaml")
response = broker.request("agent-id", "intent", {"clearance":..., "purpose":..., "session_id":...})
response.data, response.sources_queried, response.sources_denied, response.attestation_token, response.duration_ms
```

## nautilus.yaml Schema

```yaml
attestation_key_ref: vault:secret/data/attestation
audit:
  sink: jsonl
  path: ./audit.jsonl
  fsync: true
sources:
  - id: <id>
    adapter: <postgres|pgvector|elasticsearch|neo4j|rest|servicenow|influxdb|s3|nautobot|llm>
    url: ...
    classification: <unclassified|confidential|secret|top_secret>
    data_types: [...]
    scope:
      where: [...]
    cost_caps:
      per_request:
        max_tokens: 800000
        max_duration_seconds: 1800
        max_tool_calls: 120
      enforcement: hard|soft
    ingest_integrity:
      schema: ./schemas/feed-v2.json
      on_schema_violation: quarantine|reject|pass-through
      baseline_window: 7d
      anomaly_sigma: 3.0
    session_signing:  # LLM adapter only
      enabled: true
      key_ref: ...
      algorithm: ed25519
      ttl: 24h
rule_packs:
  - data-routing-nist
  - data-routing-hipaa
```

## Built-in Adapters

`postgres`, `pgvector`, `elasticsearch`, `neo4j`, `rest`, `servicenow`, `influxdb`, `s3`. Pluggable via entry point `nautilus.adapters`.

## REST Endpoints

| Verb | Path | Purpose |
|---|---|---|
| POST | /v1/request | broker request |
| POST | /v1/sources/{id}/disable | runtime disable (P0 issue) |
| POST | /v1/sources/{id}/enable | runtime enable |
| GET | /v1/sources | list with enabled status, reason, actor |
| GET | /health, /ready | probes |

## CLI

`nautilus serve / health / version / sources list / sources disable / sources enable / cost-caps show`.

## Attestation Envelope

Ed25519 JWS over (request_id, agent_id, intent, sources_queried, sources_denied, classification, decision, timestamp). Optional fields: `cost_caps`, `fact_set_hash`, `ingest_integrity_status`.

## Audit Log

JSONL, one entry per request. Fields: `request_id`, `agent_id`, `intent`, `outcome`, `sources_*`, `attestation`, `error?`. fsync'd.

## Verify-Before-Call

1. `GET /health` — confirm broker up.
2. `GET /v1/sources` — capture enabled set.
3. After source change, re-GET to confirm.

## Build-Test-Fix

Same 5-iter pattern as `smart-fathom`.
