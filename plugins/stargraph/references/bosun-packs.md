# Bosun Rule Packs

Bosun is the in-tree set of governance rule packs that ship with Stargraph
(`stargraph.bosun.*`). They're regular Fathom/CLIPS rule packs, mounted on
graphs declaratively through the IR `governance:` section.

## Two flavors

| Flavor | Job | Examples |
|---|---|---|
| **Routing** | Decide what node runs next. Match on state/facts; emit `goto` / `parallel` / `halt`. | project routing packs (e.g. `soc-policy`) |
| **Governance** | Constrain, observe, or modify execution. Budgets, retries, audit, safety guards. | `stargraph.bosun.budgets`, `stargraph.bosun.audit` |

The engine treats them identically — `flavor` is convention, not a code path.
A pack should pick one flavor and stick to it; mixing routing and governance
in the same pack makes inspection harder.

## Mounting

Packs are mounted as `PackMount` entries under the IR `governance:` key. A
`PackMount` is `{id, version, requires}`, where `requires` is a `PackRequires`
compat block:

```yaml
# in the graph IR (stargraph.yaml)
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

- Pack `id` is a **slug** (`^[a-z0-9][a-z0-9_\-.]{0,127}$`), with `version` as a
  **separate field** — not `vendor:pack@version`.
- `requires.stargraph_facts_version` and `requires.api_version` are enforced at
  pack-load by `stargraph.ir._versioning.check_pack_compat`, which raises
  `PackCompatError` on mismatch (force-loud — silent runtime drift is impossible).
  Comparison is pinned-string equality.

## Reference: Bosun packs shipped with Stargraph

These live in `src/stargraph/bosun/` and are governance-flavor:

| Pack | Purpose | Key facts emitted |
|---|---|---|
| `stargraph.bosun.budgets` | Enforce token / time / dollar caps per run. | `budget.exceeded`, `budget.warn` |
| `stargraph.bosun.audit` | Emit a structured, signed audit fact per transition. | `audit.transition` |

Routing-flavor packs are typically authored per project (e.g. the demos'
`soc-policy`) and mounted the same way.

## Authoring a new pack

A pack's CLIPS rules live in `rules.clp` (split into top-level constructs at
load). It declares a public fact vocabulary (deftemplates) and which runtime
fact templates it reads; anything else is private.

### Provenance discipline

Every fact a pack asserts MUST carry its provenance — `origin`, `source`
(`<pack>:<rule>`), `run_id`, `step`, `confidence`, `timestamp`. The Fathom
adapter enforces this; packs that forget will fail validation. See
`references/provenance-facts.md`.

### Routing rule — emit shape

```yaml
- name: when-confident-act
  when:
    - { template: classify_intent.confidence, op: gte, value: 0.7 }
  then:
    goto: act
```

### Governance rule — emit shape

```yaml
- name: budget-trip
  when:
    - { template: stargraph.cost.tokens, op: gte, value: ${budget.tokens.cap} }
  then:
    halt: true
    reason: budget.exceeded
    emit:
      - { template: budget.exceeded, slots: { kind: tokens, cap: ${cap} } }
```

## Distribution

In-tree Bosun packs ship under `stargraph.bosun.*`. Third-party packs ship as
separate pip distributions registering under the `stargraph.packs` entry-point
group via a `register_packs()` hook returning `list[PackSpec]` (`PackSpec` =
`{id, version, manifest_path}`).

```toml
# pyproject.toml of a pack-providing distribution
[project.entry-points."stargraph.packs"]
my_pack = "my_pkg._plugin:manifest"
```

## Signing

Production requires Ed25519 / JWS-signed packs. Stargraph release artifacts are
themselves signed with Ed25519 (detached `.sig`); the signing key is rotated on
a published schedule (fingerprint recorded in `SECURITY.md`). At pack load,
`check_pack_compat` enforces the `requires` block before the pack's rules are
admitted.

## Versioning

Packs use semver. Breaking = changed fact templates, removed rules, changed
emit shapes. Re-version on any of those. The graph hash captures the mounted
pack version, so checkpoints from a `1.x` pack won't resume under `2.x` unless
the graph declares a `migrate` block mapping `from_hash → to_hash`.
