# Bosun Rule Packs

Bosun is the in-tree set of governance rule packs that ship with Harbor
(`harbor.bosun.*`). They're regular Fathom rule packs, mounted on graphs
declaratively.

## Two flavors

| Flavor | Job | Examples |
|---|---|---|
| **Routing** | Decide what node runs next. Match on state/facts; emit `goto` / `parallel` / `halt`. | `bosun:routing/research`, `bosun:routing/triage` |
| **Governance** | Constrain, observe, or modify execution. Budgets, retries, audit, safety guards. | `bosun:budgets`, `bosun:retries`, `bosun:audit`, `bosun:safety` |

The engine treats them identically — `flavor` is convention, not a code path.
A pack should pick one flavor and stick to it; mixing routing and governance
in the same pack makes inspection harder.

## Mounting

```yaml
# in harbor.yaml
rules:
  - pack: bosun:routing/research@1.4
governance:
  - bosun:budgets@2.0
  - bosun:retries
  - bosun:audit
```

- `pack: vendor:name@version` — version is required for packs that move state
  between major versions; optional otherwise (resolves to latest).
- `governance:` is a *list* — packs fire in declaration order on every
  matching transition. Order matters for budgets-before-retries etc.

## Reference: Bosun packs shipped with Harbor

These live in `src/harbor/bosun/` and are governance-flavor:

| Pack | Purpose | Key facts emitted |
|---|---|---|
| `bosun:budgets` | Enforce token / time / dollar caps per run. | `budget.exceeded`, `budget.warn` |
| `bosun:retries` | Exponential backoff on tool failures. | `retry.attempt`, `retry.giveup` |
| `bosun:audit` | Emit a structured, signed audit fact per transition (see `signing.py`). | `audit.transition` |
| `bosun:safety_pii` | Halt on PII/secret leak markers in tool outputs. | `safety.violation` |

Routing-flavor packs are not shipped in-tree — author them per project with
`/harbor:new-pack --flavor routing` and mount via `rules:`.

## Authoring a new pack

Use `/harbor:new-pack <name> --flavor routing|governance`. It scaffolds:

```
bosun-packs/<name>/
  pack.yaml
  templates/      # deftemplate YAML — fact shapes
  rules/          # defrule YAML — productions
  modules/        # CLIPS modules (if you need scoping)
  functions/      # deffunction YAML
  tests/          # pytest cases — pack-level unit tests
  README.md
```

`pack.yaml` declares the public fact vocabulary (templates) and which Harbor
runtime fact templates the pack reads. Anything else is private.

### Provenance discipline

Every fact a pack asserts MUST carry `(origin=rule, source=<pack>:<rule>,
run_id, step, ts)`. This is enforced by the Fathom adapter — packs that
forget will fail validation.

### Routing rules — emit shape

```yaml
- name: when-confident-act
  when:
    - { template: classify_intent.confidence, op: gte, value: 0.7 }
  then:
    goto: act
```

### Governance rules — emit shape

```yaml
- name: budget-trip
  when:
    - { template: harbor.cost.tokens, op: gte, value: ${budget.tokens.cap} }
  then:
    halt: true
    reason: budget.exceeded
    emit:
      - { template: budget.exceeded, slots: { kind: tokens, cap: ${cap} } }
```

## Validation

```bash
fathom validate bosun-packs/<name>
fathom test     bosun-packs/<name>
fathom bench    bosun-packs/<name>     # µs/eval; regressions vs published targets
```

Mount a candidate pack on a real graph in a sandbox:

```bash
harbor simulate <graph> --mount bosun-packs/<name>
```

## Versioning

Packs use semver. Breaking = changed fact templates, removed rules, changed
emit shapes. Re-version on any of those. Harbor's graph hash captures the
mounted pack version, so checkpoints from `bosun:budgets@1.x` won't resume
under `@2.x` unless you declare a `migrate` block.

## Distribution

Bosun packs ship in-tree under `harbor.bosun.*`. Third-party packs ship as
separate pip distributions registering under the `harbor.packs` entry point
(see `design-docs/harbor-plugin-api.md`).
