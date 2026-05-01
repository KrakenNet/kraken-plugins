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
      id:
        type: STRING
        required: true
      role:
        type: SYMBOL
        allowed: [admin, user, guest]
        required: true
      clearance:
        type: SYMBOL
        allowed: [unclassified, confidential, secret, top_secret]
      attempts:
        type: INTEGER
        default: 0
```

Slot-spec keys (see fathom's `reference/yaml/template.md` for the canonical list):

| Key           | Type                                       | Default | Notes                                                                              |
|---------------|--------------------------------------------|---------|------------------------------------------------------------------------------------|
| `type`        | `STRING\|SYMBOL\|INTEGER\|FLOAT\|BOOLEAN`  | —       | Required. `SYMBOL` with `allowed:` is the closed-set form (replaces "enum").       |
| `required`    | `bool`                                     | `false` | SDK/REST asserts that omit a required slot fail validation. RHS asserts bypass.    |
| `allowed`     | `list[str]`                                | —       | Closed value set for `SYMBOL` slots.                                               |
| `default`     | scalar                                     | `null`  | Emitted as `(default <value>)` in the generated CLIPS.                             |
| `description` | `str`                                      | `""`    | Author-facing prose; not emitted to CLIPS.                                         |

## `rules[*]`

Pairs LHS fact patterns (`when`) with an RHS `ThenBlock` (`then`).

```yaml
rules:
  - name: deny-overclearance
    salience: -10                # optional; default 0. Higher fires first.
    when:
      - template: agent
        alias: a
        conditions:
          - slot: clearance
            expression: below(secret)
      - template: data_request
        conditions:
          - slot: classification
            expression: equals(secret)
    then:
      action: deny
      reason: "agent clearance below requested classification"
```

Top-level rule fields:

| Field         | Type                | Default | Description                                                                          |
|---------------|---------------------|---------|--------------------------------------------------------------------------------------|
| `name`        | str                 | —       | Required. CLIPS identifier; emitted as `<module>::<name>`.                           |
| `description` | str                 | `""`    | Author-facing prose; not emitted to CLIPS.                                           |
| `salience`    | int                 | `0`     | Conflict-resolution priority. `(declare (salience N))` emitted only when `!= 0`.     |
| `when`        | `list[FactPattern]` | —       | One or more fact patterns. Empty list is rejected by `compile_rule`.                 |
| `then`        | `ThenBlock`         | —       | Single dict with `action` and/or `assert: [...]`. See [Action shape](#action-shape). |

Module membership is established by the enclosing `modules[*].rules:` list,
not a per-rule `module:` field.

## Fact pattern (`when[*]`) — `FactPattern`

Each entry in `when` is a `FactPattern`: a template name, optional alias, and a
list of `ConditionEntry` items.

| Field        | Type                   | Default | Description                                                                                                |
|--------------|------------------------|---------|------------------------------------------------------------------------------------------------------------|
| `template`   | str                    | —       | Required. The template name this pattern matches.                                                          |
| `alias`      | str \| null            | `null`  | Optional. Used as the cross-fact prefix in peer patterns' expressions: `$<alias>.<slot>`.                  |
| `conditions` | `list[ConditionEntry]` | —       | Required. Slot constraints and/or `(test …)` CEs. May be empty (emits a bare `(<template>)` pattern).      |

```yaml
when:
  - template: agent
    alias: a
    conditions:
      - slot: role
        expression: equals(admin)
      - slot: id
        bind: ?aid
  - template: action
    conditions:
      - slot: actor
        expression: equals($a.id)
      - test: (policy-allows ?aid)
```

## Condition entry — `ConditionEntry`

A `ConditionEntry` has four shapes (validator: `_require_bind_or_expression`):

### 1. `slot` + `expression` — slot constraint

```yaml
- slot: amount
  expression: greater_than(1000)
- slot: currency
  expression: in([USD, EUR])
```

Operators use functional-call syntax: `<op>(<arg>)`. `arg` may be a literal,
list, or a cross-fact reference `$alias.field` (resolved to `?alias-field` at
compile time). See [Supported operators](#supported-operators).

### 2. `slot` + `bind` — capture without constraint

```yaml
- slot: subject_id
  bind: ?sid
```

`bind` must start with `?`. Captures the slot value for use in peer conditions
(via `$alias.slot` cross-refs) or on the RHS.

### 3. Standalone `test` — escape hatch CE

```yaml
- test: (my-fn ?sid)
```

`test` must be a parenthesized CLIPS expression. Emits `(test <expr>)` after
all pattern CEs. Used to call functions registered via
`Engine.register_function` and the temporal externals (`fathom-count-exceeds`,
etc.).

### 4. Combinations

`bind` + `expression` constrains and captures the same slot. A `test` may
accompany a slot/expression or stand alone.

```yaml
- slot: amount
  bind: ?amt
  expression: greater_than(100)
  test: (policy-allows ?amt)
```

What the validator rejects: empty entry; `slot` without `expression` or
`bind`; `slot` alongside a standalone `test` only; `bind` not starting with
`?`; `test` empty or unparenthesized.

## Supported operators

Syntax: `expression: <op>(<arg>)`. Source: `_compile_condition` in
`fathom/compiler.py`.

| Group          | Operators                                                                                          |
|----------------|----------------------------------------------------------------------------------------------------|
| Comparison     | `equals`, `not_equals`, `greater_than`, `less_than`                                                |
| Set            | `in`, `not_in`                                                                                     |
| String         | `contains`, `matches`                                                                              |
| Classification | `below`, `meets_or_exceeds`, `within_scope`                                                        |
| Temporal       | `changed_within`, `count_exceeds`, `rate_exceeds`, `last_n`, `distinct_count`, `sequence_detected` |

Classification operators require a function declared with a `hierarchy_ref`.
Any other operator name raises `CompilationError`.

## Action shape — `ThenBlock`

`then` is a single dict (not a list).

```yaml
then:
  action: deny
  reason: "insufficient clearance for {classification}"
  notify: [compliance, ops]
  attestation: true
  assert:
    - template: audit-log
      slots:
        subject: "?aid"
        action: deny
```

| Field         | Type                  | Default            | Description                                                                                              |
|---------------|-----------------------|--------------------|----------------------------------------------------------------------------------------------------------|
| `action`      | `ActionType \| null`  | `null`             | One of `allow`, `deny`, `escalate`, `scope`, `route`. Emitted on the `__fathom_decision` fact.           |
| `reason`      | str                   | `""`               | `{placeholder}` refs compile to `(str-cat …)`; literal reasons emit as quoted strings.                   |
| `log`         | `none\|summary\|full` | `summary`          | Emitted as the `log-level` slot on the decision fact.                                                    |
| `notify`      | `list[str]`           | `[]`               | Joined with `", "` and emitted as a single quoted string.                                                |
| `attestation` | bool                  | `false`            | Emitted as `TRUE`/`FALSE` on the decision fact's `attestation` slot.                                     |
| `metadata`    | `dict[str, str]`      | `{}`               | JSON-serialized (sorted keys); empty dict emits `""`.                                                    |
| `assert`      | `list[AssertSpec]`    | `[]`               | Each entry becomes one `(assert (<template> …))` on the RHS.                                             |

`_require_action_or_asserts` enforces that at least one of `action` or a
non-empty `assert` list is provided. Rules may assert-only, decide-only, or
both.

### `AssertSpec`

```yaml
- template: audit-log
  slots:
    subject: "?aid"
    action: deny
```

`template` must be a valid CLIPS identifier. `slots` values pass through
`_validate_slot_value`: `?var` refs must be well-formed, s-expressions must
have balanced parens, embedded NULs are rejected.

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
      id:
        type: STRING
        required: true
      clearance:
        type: SYMBOL
        allowed: [unclassified, confidential, secret, top_secret]
  - name: data
    slots:
      id:
        type: STRING
        required: true
      classification:
        type: SYMBOL
        allowed: [unclassified, confidential, secret, top_secret]

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
    rules: [deny-overclearance]

focus_order:
  - access-control

rules:
  - name: deny-overclearance
    salience: -10
    when:
      - template: agent
        alias: a
        conditions:
          - slot: id
            bind: ?aid
          - slot: clearance
            bind: ?ac
      - template: data
        alias: d
        conditions:
          - slot: classification
            bind: ?dc
          - slot: clearance
            expression: below($d.classification)
    then:
      action: deny
      reason: "agent {aid} clearance {ac} below {dc}"
```

## See also

- `clips-cheatsheet.md` — full operator catalogue.
- `rule-packs.md` — shipped packs and their decision spaces.
- `attestation.md` — JWS envelope over evaluation results.
