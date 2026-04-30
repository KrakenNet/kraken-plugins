# Rule YAML Schema

Authoring reference for Fathom rule-pack YAML. Every rule pack is one or more YAML
files containing some combination of four top-level keys: `templates`, `rules`,
`modules`, `functions`. Each is a list of dicts. The compiler parses, validates
(Pydantic), and emits CLIPS source. For the underlying compilation pipeline see
the `concepts/yaml-compilation` doc in the fathom source repo.

## Top-level keys

| Key         | Shape           | Purpose                                                    |
|-------------|-----------------|------------------------------------------------------------|
| `templates` | list of dicts   | Fact shapes (deftemplate). Live in `MAIN`; visible to all. |
| `rules`     | list of dicts   | When/then logic (defrule). Scoped by `module:` field.      |
| `modules`   | list of dicts   | Namespace + focus-stack ordering for groups of rules.      |
| `functions` | list of dicts   | Author-defined CLIPS deffunctions and classification fams. |

Identifiers everywhere must match `^[A-Za-z_][A-Za-z0-9_\-]*$`. Empty strings,
spaces, and parentheses in names are rejected at validation time.

## `templates[*]`

Declares a fact shape with typed slots.

```yaml
templates:
  - name: agent
    description: An autonomous agent in the system.
    slots:
      id:        { type: string, required: true }
      role:      { type: enum, values: [admin, user, guest], required: true }
      clearance: { type: enum, values: [unclassified, confidential, secret, top_secret] }
      attempts:  { type: int, default: 0 }
```

Slot-spec keys:

| Key           | Type                       | Default | Notes                                                     |
|---------------|----------------------------|---------|-----------------------------------------------------------|
| `type`        | `string\|int\|float\|bool\|enum\|datetime` | —    | Required. `enum` is a closed set of allowed symbols.      |
| `required`    | `bool`                     | `false` | If true, asserts via the SDK/REST path that omit the slot fail validation. Rule-RHS asserts bypass this check. |
| `values`      | `list[str]`                | —       | Required for `enum`. Ignored for numeric types.           |
| `default`     | scalar                     | `null`  | Emitted as `(default <value>)` in the generated CLIPS.    |
| `description` | `str`                      | `""`    | Author-facing prose; not emitted to CLIPS.                |

## `rules[*]`

Pairs LHS conditions (`when`) with RHS actions (`then`).

```yaml
rules:
  - name: deny-overclearance
    module: access-control       # optional; defaults to MAIN
    salience: -10                # optional; default 0. Higher fires first.
    when:
      - { template: agent, slot: clearance, op: below, value: data.classification }
    then:
      - { decision: deny, reason: "agent clearance below data classification" }
```

Top-level rule fields:

| Field      | Type           | Default | Description                                                               |
|------------|----------------|---------|---------------------------------------------------------------------------|
| `name`     | str            | —       | Required. Unique within the module.                                       |
| `module`   | str            | `MAIN`  | The module namespace this rule belongs to.                                |
| `salience` | int            | `0`     | Conflict-resolution priority. Higher fires first; ties broken below.      |
| `when`     | list           | —       | One or more conditions. Empty list rejected by `compile_rule`.            |
| `then`     | list           | —       | One or more actions.                                                      |

## Condition shapes

Four condition shapes are recognised on the LHS:

### 1. Slot constraint — `{ template, slot, op, value }`

```yaml
when:
  - { template: request, slot: amount, op: gt, value: 1000 }
  - { template: request, slot: currency, op: in, value: [USD, EUR] }
```

Constrains a slot of the matched template to satisfy the operator. `value` may be
a literal scalar/list, or a cross-fact reference (e.g. `data.classification`)
resolved at compile time.

### 2. Bound-fact reference — `{ template, bind, slots: { ... } }`

```yaml
when:
  - { template: agent, bind: ?a, slots: { role: admin } }
  - { template: action, bind: ?act, slots: { actor: $a.id } }
```

Binds the matched fact to a variable for cross-condition reference. Bind names
start with `?`. Use `$<bind>.<slot>` in peer conditions to refer to slots of the
bound fact.

### 3. Negation — `{ not: { ... } }`

```yaml
when:
  - { not: { template: revocation, slot: subject, op: eq, value: $a.id } }
```

Matches when no fact satisfies the inner condition.

### 4. Existential — `{ exists: { ... } }`

```yaml
when:
  - { exists: { template: alert, slot: severity, op: gte, value: high } }
```

Matches if at least one fact satisfies the inner condition; the bound fact is
not exposed to the RHS.

A bare list of conditions is implicit AND. Use `or:` (a list) for disjunction.

## Action shapes

Four action shapes on the RHS:

### 1. Decision — `{ decision, reason }`

```yaml
then:
  - { decision: deny, reason: "insufficient clearance for {data.classification}" }
```

Emits a `__fathom_decision` fact that the engine reads at end-of-evaluation.
`{placeholder}` references in `reason` interpolate LHS bind values via CLIPS
`(str-cat …)`. `decision` is an `ActionType`: `allow|deny|escalate|scope|route`.

### 2. Assert a new fact — `{ assert: <template>, slots: { ... } }`

```yaml
then:
  - { assert: audit-log, slots: { subject: $a.id, action: deny } }
```

Inserts a fact into working memory. The new fact may match other rules in the
same evaluation cycle.

### 3. Retract — `{ retract: <bind-var> }`

```yaml
then:
  - { retract: ?a }
```

Removes the bound fact from working memory.

### 4. Bind — `{ bind: <var>, value: <expr> }`

```yaml
then:
  - { bind: ?score, value: "(* $a.attempts 10)" }
```

Computes a value once for use in subsequent same-`then` actions or as an
interpolated reason placeholder.

## `modules[*]`

```yaml
modules:
  - name: classification
    description: Label-derivation rules.
    priority: 100        # metadata only — does not affect ordering today
  - name: access-control
    description: Core access decisions.

focus_order:
  - classification
  - access-control
```

Module ordering is driven by the explicit top-level `focus_order:` list (or
`Engine.set_focus(...)` at runtime). The first name in `focus_order` runs first.
`priority` is preserved for tooling but does **not** drive the focus stack in
the current runtime.

### Conflict resolution

When several rules are simultaneously eligible:

1. **Salience first.** Higher `salience` fires first.
2. **Last-write-wins on the decision fact.** When two rules at different
   salience both emit a `__fathom_decision`, the lower-salience rule fires
   *later* and overwrites. Fathom's fail-closed convention puts `deny` rules
   below `allow` rules so deny wins on conflict.
3. **Declared order tiebreak.** Within a single salience tier, ties resolve in
   declaration order (first-declared fires first).

## `functions[*]`

```yaml
functions:
  - name: classification-check
    type: classification        # one of: classification, raw, temporal
    params: [a, b]
    hierarchy_ref: clearance    # required for type=classification

hierarchies:
  - name: clearance
    levels: [unclassified, confidential, secret, top_secret]
```

Three subtypes:

| `type`           | What it emits                                                                                          |
|------------------|--------------------------------------------------------------------------------------------------------|
| `classification` | Family of `<hier>-rank`, `<hier>-below`, `<hier>-meets-or-exceeds`, `<hier>-within-scope` deffunctions. |
| `raw`            | `body:` emitted verbatim — author owns the full `(deffunction …)` form.                                |
| `temporal`       | Reserved; emits empty string. Built-in temporal operators are Python externals under `fathom-` prefix. |

Raw example:

```yaml
functions:
  - name: double
    type: raw
    params: [x]
    body: "(deffunction MAIN::double (?x) (* ?x 2))"
```

The `fathom-` prefix is reserved for engine-registered builtins; avoid it in raw
bodies.

## Complete example

```yaml
templates:
  - name: agent
    slots:
      id:        { type: string, required: true }
      clearance: { type: enum, values: [unclassified, confidential, secret, top_secret] }
  - name: data
    slots:
      id:             { type: string, required: true }
      classification: { type: enum, values: [unclassified, confidential, secret, top_secret] }

hierarchies:
  - name: clearance
    levels: [unclassified, confidential, secret, top_secret]

functions:
  - name: clearance-check
    type: classification
    params: [a, b]
    hierarchy_ref: clearance

modules:
  - name: access-control

focus_order:
  - access-control

rules:
  - name: deny-overclearance
    module: access-control
    salience: -10
    when:
      - { template: agent, bind: ?a, slots: {} }
      - { template: data, bind: ?d, slots: {} }
      - { template: agent, slot: clearance, op: below, value: $d.classification }
    then:
      - { decision: deny, reason: "agent {?a.id} clearance below {?d.classification}" }
```

## See also

- `clips-cheatsheet.md` — full operator catalogue.
- `rule-packs.md` — shipped packs and their decision spaces.
- `attestation.md` — JWS envelope over evaluation results.
