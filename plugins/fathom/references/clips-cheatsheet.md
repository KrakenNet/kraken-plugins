# Fathom Operator Cheatsheet

Operators usable in Fathom rule conditions, grouped by category. Source of
truth: `_compile_condition` in `fathom/compiler.py` and the
`reference/yaml/rule.md` doc in the fathom source repo.

Conditions use functional-call syntax in YAML:

```yaml
- slot: <slot-name>
  expression: <op>(<arg>)
```

`arg` may be a literal scalar, a list, or a cross-fact reference
`$alias.field` (resolved to `?alias-field` at compile time).

## Comparison

`equals(<value>)` — slot value equals literal.
- `{ slot: role, expression: equals(admin) }`

`not_equals(<value>)` — slot value does not equal literal.
- `{ slot: status, expression: not_equals(revoked) }`

`greater_than(<value>)` — slot value strictly greater than.
- `{ slot: severity, expression: greater_than(5) }`

`less_than(<value>)` — slot value strictly less than.
- `{ slot: amount, expression: less_than(1000) }`

## Set membership

`in([...])` — slot value is one of the listed values.
- `{ slot: currency, expression: in([USD, EUR, GBP]) }`

`not_in([...])` — slot value is not in the list.
- `{ slot: country, expression: not_in([KP, IR, CU]) }`

## String

`contains(<substring>)` — slot string contains substring.
- `{ slot: user_input, expression: contains("ignore previous instructions") }`

`matches(<regex>)` — slot string matches a regex.
- `{ slot: email, expression: matches(".*@example\.com$") }`

## Classification

Lattice ordering for hierarchies declared via classification functions
(`type: classification` with a `hierarchy_ref:`). The three ops below emit
calls to the generated `<hier>-below`, `<hier>-meets-or-exceeds`, and
`<hier>-within-scope` deffunctions.

`below(<other>)` — left rank is strictly less than right's.
- `{ slot: clearance, expression: below($d.classification) }`

`meets_or_exceeds(<other>)` — left rank >= right rank.
- `{ slot: clearance, expression: meets_or_exceeds(secret) }`

`within_scope(<other>)` — both values are in-hierarchy (rank >= 0).
- `{ slot: clearance, expression: within_scope($d.classification) }`

## Temporal

Temporal operators emit `(test …)` CEs that call external functions
registered at runtime. Window arguments are typically ISO-8601 durations
(`PT5M`) or seconds (int).

`changed_within(<window>)` — slot value changed in window.

`count_exceeds(<threshold>, <window>)` — N matching facts in window.

`rate_exceeds(<rate>, <window>)` — sliding-window rate.

`last_n(<n>)` — bind the most-recent N facts of the template.

`distinct_count(<slot>)` — number of distinct slot values in working memory.

`sequence_detected(<events>)` — ordered sequence of named event facts seen.

Example:

```yaml
- slot: user
  expression: count_exceeds(5, PT15M)
```

## Logical combinators

Implicit AND: a `when` list of multiple `FactPattern` entries is conjunctive.
Each pattern's `conditions:` list is also AND.

There is no top-level `or:` / `not:` / `exists:` keyword in the YAML — these
patterns are expressed using CLIPS-level test CEs (the `test:` shape) when
required.

## Cross-fact references and binds

**Bind variable:** `bind: ?var` on a slot captures the slot's value. The
variable is then usable in peer `expression:` args (via the alias prefix) or
in `test:` CEs and on the RHS.

```yaml
when:
  - template: session
    alias: s
    conditions:
      - slot: id
        bind: ?sid
  - template: action
    conditions:
      - slot: actor
        expression: equals($s.id)
```

`$alias.slot` cross-references resolve to `?alias-slot` in the emitted CLIPS.

## Test CEs (escape hatch)

```yaml
- test: (my-fn ?sid)
```

Any parenthesized CLIPS expression. Used to invoke functions registered via
`Engine.register_function`. Emitted after all pattern CEs, in source order.

## Conflict resolution

When multiple rules are eligible at the same instant:

1. **Salience.** Higher `salience` fires first; lower `salience` fires later.
2. **Last-write-wins on the decision fact.** The lower-salience rule fires
   *later* and overwrites prior decisions. Fail-closed convention: `deny`
   rules below `allow` rules so `deny` wins on conflict.
3. **Declared order tiebreak.** Within a salience tier, earlier-declared
   rules fire first.

## See also

- `rule-yaml-schema.md` — full schema for `templates`, `rules`, `modules`,
  `functions`.
- `rule-packs.md` — shipped packs and their decision spaces.
