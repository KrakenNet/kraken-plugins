# Stargraph IRDocument (graph YAML) Reference

A Stargraph graph is an **IRDocument** — a portable, JSON-Schema-typed description of an executable graph plus its rules, tools, skills, stores, and governance packs. It is authored as YAML (commonly `<graphdir>/stargraph.yaml`) and loaded by `stargraph run`, `stargraph serve --graph`, and `stargraph simulate`.

Every IR model subclasses `IRBase`, which pins `extra='forbid'` — unknown keys are rejected at load time. Validation is automatic on load; you can also call `stargraph.ir.validate(ir)` in Python (it returns a `list[ValidationError]`, never raises).

## Top-level Keys

| Key | Type | Required | Purpose |
|---|---|---|---|
| `ir_version` | string | yes | `MAJOR.MINOR.PATCH` (e.g. `"1.0.0"`). Major divergence from the build's IR version is rejected. |
| `id` | string | yes | Document identifier (e.g. `"graph:triage"`). |
| `nodes` | list | yes | Graph nodes (`NodeSpec`). |
| `rules` | list | no | Top-level rule definitions (`RuleSpec`). |
| `tools` | list | no | Tool references (`ToolRef`). |
| `skills` | list | no | Skill references (`SkillRef`). |
| `stores` | list | no | Store bindings (`StoreRef`). |
| `state_schema` | map | no | Flat `name -> type-string` map. Mutually exclusive with `state_class`. |
| `state_class` | string | no | `module.path:ClassName` of an existing Pydantic model. Mutually exclusive with `state_schema`. |
| `parallel` | list | no | Top-level parallel/join declarations (`ParallelBlock`). |
| `governance` | list | no | Mounted Bosun packs (`PackMount`). |
| `migrate` | list | no | Hash-to-hash migration descriptors for resume (`MigrateBlock`). |

A minimal valid document needs only `ir_version`, `id`, and `nodes`; every other section defaults to an empty list/dict.

## id

A free-form document identifier. Convention is a `graph:<slug>` form.

```yaml
id: "graph:research"
```

## state_schema / state_class

State is Pydantic-typed. Declare it one of two mutually-exclusive ways:

```yaml
# flat primitive map: field name -> type string
state_schema:
  message: "str"
  severity: "int"
```

```yaml
# OR reference an existing Pydantic model
state_class: "graph.state:RunState"
```

The two are mutually exclusive (resolved at `Graph` construction). See `references/state-schema.md`.

## nodes

List of `NodeSpec`. Each entry has `id` and `kind`; builtins may carry a `config` block.

```yaml
nodes:
  - id: ingest
    kind: "graph.nodes:IngestAlert"        # custom node: module.path:ClassName

  - id: risk_score
    kind: ml                                # builtin factory key
    config:
      model_id: soc-severity
      version: "1.0.0"
      runtime: onnx
      expected_sha256: "c314b6f6…"
      input_field: features
      output_field: risk

  - id: triage_decide
    kind: dspy

  - id: halt
    kind: echo
```

`kind` is either a **builtin factory key** or a `module.path:ClassName` reference to a custom node.

| Builtin `kind` | Purpose |
|---|---|
| `echo` | Pass state through unchanged. |
| `halt` | Terminal node. |
| `passthrough` | Pure dispatch point (no side effect); governance rules fire on it. |
| `dspy` | LLM-backed DSPy node. |
| `ml` | Direct ML model node (e.g. ONNX, sha256-pinned). |
| `interrupt` | HITL pause node (see `references/hitl-patterns.md`). |
| `human_input` | Human-input node. |
| `retrieval` | Retrieval over a mounted store. |
| `subgraph` | Embed another IR document as a node. |
| `write_artifact` | Write a run artifact. |

Tool-call nodes use `kind: tool` and reference the tool by its registry key:

```yaml
  - id: ask_broker
    kind: tool
    tool: nautilus.broker_request@1
    inputs:
      agent_id: "agent-42"
      intent: "{{state.user_intent}}"
    out: broker_reply
```

Node ids must match the slug regex `^[a-z0-9][a-z0-9_\-.]{0,127}$`.

## rules

A `RuleSpec` is `{id, when, then}`. `when` is a CLIPS-pattern condition string; `then` is a list of discriminated-union **actions** (no nesting).

```yaml
rules:
  - id: r-ingest-to-retrieval
    when: "?n <- (node-id (id ingest))"
    then: [{ kind: goto, target: retrieval }]

  - id: rule.escalate
    when: "(severity ?s&:(>= ?s 4))"
    then:
      - { kind: goto, target: triage_decide }
```

Action kinds (discriminated on `kind`):

| `kind` | Notable fields |
|---|---|
| `goto` | `target` |
| `halt` | `reason` (default `""`) |
| `parallel` | `targets`, `join`, `strategy` (`all`/`any`/`race`/`quorum`) |
| `retry` | `target`, `backoff_ms` |
| `assert` | `fact`, `slots` (JSON-encoded slot dict) |
| `retract` | `pattern` |
| `interrupt` | `prompt`, `interrupt_payload`, `requested_capability`, `timeout`, `on_timeout` |

There are **no explicit edges**. Routing is static fall-through (the engine walks `nodes` in declaration order when no rule fires) plus rule-driven `goto`.

## governance

Mount Bosun packs as `PackMount` entries: `{id, version, requires}`. `requires` is a `PackRequires` compat block checked at load (`check_pack_compat` raises `PackCompatError` on mismatch).

```yaml
governance:
  - id: stargraph.bosun.budgets
    version: "1.0"
    requires: { stargraph_facts_version: "1.0", api_version: "1" }
  - id: stargraph.bosun.audit
    version: "1.0"
    requires: { stargraph_facts_version: "1.0", api_version: "1" }
  - id: soc-policy
    version: "1.0"
    requires: { stargraph_facts_version: "1.0", api_version: "1" }
```

Pack ids are slug form with a separate `version` field. See `references/bosun-packs.md`.

## stores

`StoreRef` is `{name, provider}`. `to_capabilities()` derives `["db.{name}:read", "db.{name}:write"]`.

```yaml
stores:
  - { name: "kb", provider: "stargraph.stores.lancedb" }
  - { name: "facts", provider: "stargraph.stores.sqlite_fact" }
```

See `references/store-protocols.md` for the five protocols and real provider ids.

## migrate

`graph_hash` is the canonical IR hash (`dumps_canonical`, sorted keys). Resume rejects on hash mismatch unless a `migrate` block maps `from_hash -> to_hash`.

```yaml
migrate:
  - { from_hash: "<old>", to_hash: "<new>" }
```

## Validating a graph

There is no `graph verify` subcommand. Validate by loading:

```bash
# rule-firing trace, no node execution
stargraph run graphs/triage.yaml --inspect

# offline trace against synthetic node outputs
stargraph simulate graphs/triage.yaml --fixtures fixtures/triage.yaml
```

In Python: `stargraph.ir.validate(ir)` returns structured `ValidationError`s.

## Full Example

A SOC-triage graph (modeled on `demos/soc-triage/graph/stargraph.yaml`):

```yaml
ir_version: "1.0.0"
id: "graph:soc-triage"

state_class: "graph.state:RunState"

nodes:
  - id: ingest
    kind: "graph.nodes:IngestAlert"
  - id: retrieval
    kind: "graph.nodes:RetrievalPriors"
  - id: risk_score
    kind: ml
    config:
      model_id: soc-severity
      version: "1.0.0"
      runtime: onnx
      expected_sha256: "c314b6f6…"
      input_field: features
      output_field: risk
  - id: triage_decide
    kind: dspy
  - id: soc_policy
    kind: passthrough
  - id: analyst_gate
    kind: interrupt
    config:
      prompt: "Approve disposition {disposition} for alert {alert_id}?"
      requested_capability: "runs:respond"
      timeout: "PT900S"
      on_timeout: "halt"
  - id: write_artifact
    kind: "graph.nodes:SocWriteArtifact"
  - id: audit
    kind: "graph.nodes:AuditChain"
  - id: halt
    kind: echo

governance:
  - id: stargraph.bosun.budgets
    version: "1.0"
    requires: { stargraph_facts_version: "1.0", api_version: "1" }
  - id: soc-policy
    version: "1.0"
    requires: { stargraph_facts_version: "1.0", api_version: "1" }

rules:
  - id: r-ingest-to-retrieval
    when: "?n <- (node-id (id ingest))"
    then: [{ kind: goto, target: retrieval }]
  - id: r-policy-escalate-hitl
    when: "?n <- (node-id (id soc_policy)) (state (disposition escalate))"
    then: [{ kind: goto, target: analyst_gate }]
  - id: r-halt
    when: "?n <- (node-id (id halt))"
    then: [{ kind: halt, reason: "run complete" }]
```

This graph ingests an alert, retrieves priors, scores risk with a pinned ONNX model, decides a disposition with a DSPy node, applies the `soc-policy` Bosun pack at a passthrough dispatch point, routes escalations through a HITL interrupt gate, writes a case-note artifact, and seals a hash-chained audit record before halting.
