# Harbor harbor.yaml Reference

`harbor.yaml` is the declarative manifest for a Harbor graph. It binds a Pydantic state class, a list of nodes, mounted Bosun rule and governance packs, store providers, checkpoint policy, triggers, and plugin dependencies.

## Top-level Keys

| Key | Type | Required | Purpose |
|---|---|---|---|
| `name` | string | yes | Graph identifier; unique within a registry. |
| `state` | string | yes | Path to Pydantic State class. |
| `nodes` | list | yes | Ordered (or DAG) list of node definitions. |
| `rules` | list | no | Bosun rule packs to mount. |
| `governance` | list | no | Governance packs (budgets, audit, policy). |
| `stores` | map | no | Store-tier provider mounts. |
| `checkpoints` | map | no | Checkpoint policy. |
| `triggers` | list | no | External run initiators. |
| `plugins` | list | no | Harbor plugins this graph depends on. |

## name

A graph identifier. Must be unique in the registry that hosts it.

```yaml
name: research
```

Conventions: lowercase, kebab-case, no version suffix (versions are tracked by graph hash and registry tags).

## state

Module path with class name, separated by `:`.

```yaml
state: ./state.py:State
```

The path is resolved relative to `harbor.yaml`. The class must subclass `pydantic.BaseModel`. See `references/state-schema.md`.

## nodes

List of node definitions. Each entry has `name` and `type`; additional keys depend on the type.

```yaml
nodes:
  - name: plan
    type: dspy:ChainOfThought
    signature: ./signatures.py:PlanSignature

  - name: search
    type: tool:browser.search
    args:
      max_results: 10

  - name: classify
    type: model:onnx:./models/intent.onnx

  - name: retrieve
    type: retrieval:vector
    k: 8

  - name: answer
    type: subgraph:synthesize
```

Type formats:

| Format | Meaning |
|---|---|
| `dspy:<Module>` | DSPy module class (e.g. `Predict`, `ChainOfThought`, `ReAct`). |
| `model:<format>:<id>` | Direct ML model: `onnx`, `transformers`, `gguf`, etc. `<id>` is a path or hub identifier. |
| `tool:<namespace>.<name>` | Registered tool. Namespace is the plugin; name is the tool. |
| `retrieval:<store>` | Retrieval over a mounted store tier (`vector`, `graph`, `doc`). |
| `subgraph:<name>` | Embed another graph by name. |

## rules

List of Bosun rule pack mounts. Each entry is a `{pack: <spec>}` mapping.

```yaml
rules:
  - pack: bosun:routing/research
  - pack: bosun:safety/pii@1.2.0
  - pack: ./packs/local-rules
```

Pack specs:

- `bosun:<group>/<name>` — registry-resolved, latest.
- `bosun:<group>/<name>@<version>` — pinned version.
- `./relative/path` — local pack.

## governance

Same shape as `rules`, but mounted into the governance phase (runs before/after every node, not as routing).

```yaml
governance:
  - pack: bosun:budgets
  - pack: bosun:audit
  - pack: bosun:policy/no-pii-egress
```

## stores

Map of tier name to `<provider>:<config>`.

```yaml
stores:
  vector: lancedb:./.lance
  graph: kuzu:./.kuzu
  doc: sqlite:./.docs
  memory: sqlite:./.memory
  fact: sqlite:./.facts
```

Tier names: `vector`, `graph`, `doc`, `memory`, `fact`. Any omitted tier uses its embedded default. See `references/store-protocols.md`.

## checkpoints

```yaml
checkpoints:
  every: node-exit       # node-exit | rule-fire | manual
  store: sqlite:./.checkpoints
  retain: 100            # optional: keep last N
```

`every` controls cadence:

- `node-exit` — snapshot after every node returns (default).
- `rule-fire` — also snapshot after each Bosun rule activation.
- `manual` — only when a node calls `harbor.checkpoint()` explicitly.

`store` is a checkpoint provider URI (typically SQLite).

## triggers

```yaml
triggers:
  - type: cron
    schedule: "0 */6 * * *"
    payload:
      query: "weekly digest"

  - type: webhook
    path: /research
    auth: token

  - type: file_watch
    glob: "./inbox/*.json"

  - type: mcp
    method: research/start

  - type: manual
```

Each trigger initiates a run with provided or constructed initial state. `manual` is implicit if no triggers are declared.

## plugins

Entry-point names of installed Harbor plugins this graph depends on. Used at load time to verify the environment.

```yaml
plugins:
  - harbor-browser
  - harbor-bosun
  - harbor-pinecone
```

Missing a declared plugin is a load-time error.

## Full Example

A complete Research graph:

```yaml
name: research
state: ./state.py:ResearchState

nodes:
  - name: plan
    type: dspy:ChainOfThought
    signature: ./signatures.py:PlanSignature

  - name: search
    type: tool:browser.search
    args:
      max_results: 10

  - name: rerank
    type: model:onnx:./models/reranker.onnx

  - name: synthesize
    type: dspy:ChainOfThought
    signature: ./signatures.py:SynthesizeSignature

rules:
  - pack: bosun:routing/research
  - pack: bosun:quality/citation-required

governance:
  - pack: bosun:budgets
  - pack: bosun:audit
  - pack: bosun:policy/no-pii-egress

stores:
  vector: lancedb:./.lance
  graph: kuzu:./.kuzu
  doc: sqlite:./.docs

checkpoints:
  every: node-exit
  store: sqlite:./.checkpoints
  retain: 50

triggers:
  - type: cron
    schedule: "0 9 * * MON"
    payload:
      query: "weekly research digest"
  - type: webhook
    path: /research
    auth: token
  - type: manual

plugins:
  - harbor-browser
  - harbor-bosun
```

This graph plans, searches, reranks, and synthesizes; mounts routing and quality rule packs; enforces budgets, audit, and a no-PII-egress policy; persists to embedded stores; checkpoints at every node-exit retaining the last 50; and accepts cron, webhook, and manual triggers.
