---
name: smart-fathom
description: Core skill for all Fathom plugin commands and agents — Engine API, YAML rule schema, classification + temporal operators, REST/gRPC endpoints, CLI commands, attestation envelope, project detection.
version: 1.0.0
user-invocable: false
---

# Smart Fathom

## Configuration

| Setting | Default | Override |
|---|---|---|
| Local install | `uv add fathom-rules` | — |
| REST URL | `http://localhost:8080` | `FATHOM_URL` env |
| gRPC URL | `localhost:50051` | `FATHOM_GRPC_URL` env |
| Auth token | none | `FATHOM_TOKEN` env |
| Rules dir | `./rules` | `FATHOM_RULES_DIR` env |

## Project Detection

If `pyproject.toml` in PWD has `name = "fathom-rules"`, contributor mode: scan `src/fathom/`, `rule-packs/`, `tests/`. Otherwise, treat the engine as an external dependency.

## Engine API (Python)

```python
from fathom import Engine
engine = Engine()
engine.load_templates("templates/")
engine.load_rules("rules/")
engine.assert_fact("agent", {...})
result = engine.evaluate()  # EvaluationResult
result.decision  # str
result.reason    # str
result.duration_us  # int
result.attestation  # JWS string (Ed25519)
```

## YAML Rule Schema (sketch)

```yaml
templates:
  - name: agent
    slots:
      id: { type: string, required: true }
      clearance: { type: enum, values: [unclassified, confidential, secret, top_secret] }
rules:
  - name: deny-overclearance
    when:
      - { template: agent, slot: clearance, op: below, value: data_classification }
    then:
      - { decision: deny, reason: "insufficient clearance" }
modules:
  - name: access-control
    rules: [deny-overclearance]
functions:
  - name: classification_dominates
    args: [a, b]
    body: ...
```

## Operators

- Classification: `below`, `meets_or_exceeds`, `dominates`, compartment ops.
- Temporal: `count_exceeds`, `rate_exceeds`, `changed_within`, `last_n`, `distinct_count`, `sequence_detected`.
- See `references/clips-cheatsheet.md` for full list.

## REST Endpoints

| Verb | Path | Purpose |
|---|---|---|
| POST | /v1/evaluate | run an evaluation |
| POST | /v1/rules/reload | hot-reload rules (≥0.4.0); returns attestation |
| GET | /info | version + current ruleset hash |
| GET | /health, /ready | probes |
| GET | /metrics | Prometheus |

Bearer auth on all but health/ready/metrics.

## gRPC

Service `fathom.v1.Fathom` with `Evaluate(EvaluateRequest) returns (EvaluateResponse)`.

## CLI

| Command | Purpose |
|---|---|
| `fathom validate <path>` | static check |
| `fathom test <path>` | run rule-pack tests |
| `fathom bench <path>` | perf bench (target <100µs/eval) |
| `fathom info` | print version + ruleset hash |
| `fathom repl` | interactive |
| `fathom verify-artifact <path>` | check detached signature (≥release-signing version) |

## Attestation Envelope (Ed25519 JWS)

Header: `{"alg":"EdDSA","typ":"JWT"}`. Payload includes: `iss`, `sub` (request_id), `iat`, `exp`, `decision`, `reason`, `ruleset_hash`, `engine_version`.

## Verify-Before-Call

1. `GET /info` — confirm reachable + capture `ruleset_hash`.
2. List existing artifacts before scaffolding (avoid clobber).
3. Re-fetch `info` after `rules/reload` — confirm hash changed.

## Build-Test-Fix

Max 5 iters. On `fathom validate` fail, parse first error line, surface to user, attempt minimal fix.

## Communication Style

Brevity. Tables over prose. End with action steps.
