# Nautilus YAML Reference

Complete schema reference for `nautilus.yaml`. Loaded by `Broker.from_config()` and the `nautilus serve` CLI.

## Top-level Keys

| Key | Type | Required | Default | Purpose |
|---|---|---|---|---|
| `attestation_key_ref` | string | yes | — | Reference to Ed25519 signing key (vault URI, file path, or env var). |
| `audit` | object | yes | — | Audit sink configuration. See [Audit Section](#audit-section). |
| `sources` | list | yes | — | Source declarations. See [Sources List](#sources-list). |
| `rule_packs` | list[string] | no | `[]` | Names of routing rule packs to load. |

Example minimal:

```yaml
attestation_key_ref: vault:secret/data/attestation
audit:
  sink: jsonl
  path: ./audit.jsonl
sources: []
rule_packs: []
```

## Audit Section

| Field | Type | Default | Purpose |
|---|---|---|---|
| `sink` | string | `jsonl` | Audit sink driver. Currently only `jsonl` is built in. |
| `path` | string | `./audit.jsonl` | File path for the JSONL audit log. |
| `fsync` | bool | `true` | If true, fsync after every line write for durability. |

Example:

```yaml
audit:
  sink: jsonl
  path: /var/log/nautilus/audit.jsonl
  fsync: true
```

## Sources List

`sources:` is a list of source objects. Each entry declares one upstream data source the broker can route requests to.

## Per-source Fields

### id

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string | yes | Unique stable identifier. Used in REST URLs (`/v1/sources/{id}`), audit log entries, and rule pack `where` clauses. |

Example: `id: prod-customer-pg`.

### adapter

| Field | Type | Required | Allowed values |
|---|---|---|---|
| `adapter` | string | yes | `postgres`, `pgvector`, `elasticsearch`, `neo4j`, `rest`, `servicenow`, `influxdb`, `s3`, `nautobot`, `llm`, or any adapter registered via the `nautilus.adapters` entry point. |

Adapter selection determines which fields under the source block are interpreted. See `references/adapter-sdk.md` for the contract.

### url

| Field | Type | Required | Notes |
|---|---|---|---|
| `url` | string | adapter-dependent | Connection string. For `postgres`: `postgres://user:pass@host:port/db`. For `rest`: full base URL. For `s3`: `s3://bucket/prefix`. |

Adapters MAY accept additional connection fields (e.g. `auth`, `tls`, `region`); see per-adapter docs.

### classification

| Field | Type | Required | Allowed values |
|---|---|---|---|
| `classification` | string | yes | `unclassified`, `confidential`, `secret`, `top_secret` |

Used by rule packs to enforce caller clearance ≥ source classification before routing.

### data_types

| Field | Type | Required | Notes |
|---|---|---|---|
| `data_types` | list[string] | yes | Free-form tags describing what the source serves. Used by rule packs and `/nautilus:adapter-coverage`. Examples: `customer-pii`, `network-topology`, `incident-tickets`, `embeddings`. |

### scope

Defines the default scope filter applied to every request hitting this source.

| Field | Type | Default | Notes |
|---|---|---|---|
| `scope.where` | list[string] | `[]` | Predicate expressions (adapter-evaluated). Example: `["region = 'us-east-1'", "tenant_id = $session.tenant"]`. |

The broker passes the scope dict to the adapter; adapters apply it via native API permissions OR broker-side filter (see Adapter SDK).

### cost_caps

Per-request resource ceilings.

| Field | Type | Default | Notes |
|---|---|---|---|
| `cost_caps.per_request.max_tokens` | int | `800000` | Hard ceiling on tokens consumed by an LLM-backed adapter. |
| `cost_caps.per_request.max_duration_seconds` | int | `1800` | Wall-clock budget. |
| `cost_caps.per_request.max_tool_calls` | int | `120` | Tool-invocation count cap. |
| `cost_caps.enforcement` | string | `hard` | `hard` aborts on breach; `soft` records breach in audit but continues. |

Example:

```yaml
cost_caps:
  per_request:
    max_tokens: 400000
    max_duration_seconds: 600
    max_tool_calls: 60
  enforcement: hard
```

### ingest_integrity

Validates incoming feed payloads against a JSON Schema and detects anomalies.

| Field | Type | Default | Notes |
|---|---|---|---|
| `ingest_integrity.schema` | string | — | Path to JSON Schema file. |
| `ingest_integrity.on_schema_violation` | string | `quarantine` | `quarantine`, `reject`, `pass-through`. |
| `ingest_integrity.baseline_window` | duration | `7d` | Rolling window over which volume/shape baselines are computed. |
| `ingest_integrity.anomaly_sigma` | float | `3.0` | Std-dev threshold for anomaly detection. |

### session_signing (LLM adapter only)

| Field | Type | Default | Notes |
|---|---|---|---|
| `session_signing.enabled` | bool | `false` | Turns on per-session signing for LLM responses. |
| `session_signing.key_ref` | string | — | Reference to signing key (same shapes as `attestation_key_ref`). |
| `session_signing.algorithm` | string | `ed25519` | Currently only `ed25519`. |
| `session_signing.ttl` | duration | `24h` | Session signature validity window. |

## Rule Packs

`rule_packs:` is a list of rule-pack names (strings). Each name is resolved against installed packs (via the `nautilus.rule_packs` entry point) at broker startup.

```yaml
rule_packs:
  - data-routing-nist
  - data-routing-hipaa
  - cost-cap-enforcer
```

See `references/rule-packs.md` (in the upstream Nautilus docs) for authoring rule packs.

## Attestation Key Ref

The `attestation_key_ref` value MAY be:

- `vault:secret/data/<path>` — HashiCorp Vault KV-v2 path.
- `file:///abs/path/to/key.pem` — local PEM file (Ed25519 private key).
- `env:NAUTILUS_ATTESTATION_KEY` — base64-encoded key in env var.

The corresponding public key is exposed at `${NAUTILUS_URL}/v1/pubkey`.

## Full Example

```yaml
attestation_key_ref: vault:secret/data/attestation
audit:
  sink: jsonl
  path: /var/log/nautilus/audit.jsonl
  fsync: true
sources:
  - id: prod-customer-pg
    adapter: postgres
    url: postgres://nautilus:${PG_PASS}@db.internal:5432/customers
    classification: confidential
    data_types: [customer-pii, billing]
    scope:
      where:
        - "tenant_id = $session.tenant"
    cost_caps:
      per_request:
        max_tokens: 200000
        max_duration_seconds: 60
        max_tool_calls: 20
      enforcement: hard

  - id: kb-vectors
    adapter: pgvector
    url: postgres://nautilus:${PG_PASS}@vectors.internal:5432/kb
    classification: unclassified
    data_types: [embeddings, kb-articles]

  - id: incidents
    adapter: servicenow
    url: https://acme.service-now.com
    classification: confidential
    data_types: [incident-tickets, change-requests]

  - id: network-topology
    adapter: nautobot
    url: https://nautobot.internal
    classification: confidential
    data_types: [network-topology, devices, ip-addresses]

  - id: logs-search
    adapter: elasticsearch
    url: https://es.internal:9200
    classification: confidential
    data_types: [logs, security-events]
    ingest_integrity:
      schema: ./schemas/log-event-v3.json
      on_schema_violation: quarantine
      baseline_window: 7d
      anomaly_sigma: 3.0

  - id: graph
    adapter: neo4j
    url: bolt://neo4j.internal:7687
    classification: secret
    data_types: [identity-graph]

  - id: metrics
    adapter: influxdb
    url: http://influx.internal:8086
    classification: unclassified
    data_types: [metrics, telemetry]

  - id: archive
    adapter: s3
    url: s3://nautilus-archive/runs/
    classification: confidential
    data_types: [archived-runs]

  - id: external-api
    adapter: rest
    url: https://api.partner.example.com/v2
    classification: unclassified
    data_types: [partner-data]

  - id: triage-llm
    adapter: llm
    url: https://api.anthropic.com
    classification: unclassified
    data_types: [reasoning]
    session_signing:
      enabled: true
      key_ref: vault:secret/data/llm-session
      algorithm: ed25519
      ttl: 24h

rule_packs:
  - data-routing-nist
  - data-routing-hipaa
  - cost-cap-enforcer
```
