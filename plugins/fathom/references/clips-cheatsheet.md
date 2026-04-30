# CLIPS Operator Cheatsheet

Operators usable in Fathom rule conditions and actions, grouped by category.
Each entry: signature on one line, semantics on the next, minimal example.
This is the surface authors interact with through the YAML; the underlying
emission is documented in the fathom `concepts/yaml-compilation` source.

## Equality / Comparison

`eq(<value>)` — slot value equals literal.
- `{ slot: role, op: eq, value: admin }`

`neq(<value>)` — slot value does not equal literal.
- `{ slot: status, op: neq, value: revoked }`

`lt(<value>)` — slot value strictly less than.
- `{ slot: amount, op: lt, value: 1000 }`

`lte(<value>)` — slot value less than or equal.
- `{ slot: attempts, op: lte, value: 3 }`

`gt(<value>)` — slot value strictly greater than.
- `{ slot: severity, op: gt, value: 5 }`

`gte(<value>)` — slot value greater than or equal.
- `{ slot: score, op: gte, value: 0.9 }`

## Set membership

`in(<list>)` — slot value is one of the listed values.
- `{ slot: currency, op: in, value: [USD, EUR, GBP] }`

`not_in(<list>)` — slot value is not in the list.
- `{ slot: country, op: not_in, value: [KP, IR, CU] }`

`subset(<list>)` — slot (multivalue) is a subset of the listed set.
- `{ slot: scopes, op: subset, value: [read, list] }`

`superset(<list>)` — slot (multivalue) is a superset of the listed set.
- `{ slot: granted_scopes, op: superset, value: [read, write] }`

## Logical combinators (in conditions)

`and` — implicit by listing multiple conditions in `when:`.
- ```yaml
  when:
    - { template: agent, slot: role, op: eq, value: admin }
    - { template: agent, slot: clearance, op: gte, value: secret }
  ```

`or: [<conds>]` — disjunction of inner conditions.
- ```yaml
  when:
    - or:
        - { template: agent, slot: role, op: eq, value: admin }
        - { template: agent, slot: role, op: eq, value: auditor }
  ```

`not: { ... }` — negated condition; matches when no fact satisfies inner.
- `{ not: { template: revocation, slot: subject, op: eq, value: $a.id } }`

`exists: { ... }` — true if at least one fact satisfies inner; bind not exposed.
- `{ exists: { template: alert, slot: severity, op: gte, value: high } }`

## String ops

`matches(<regex>)` — slot string matches a Python regex (anchored as written).
- `{ slot: email, op: matches, value: '.*@example\.com$' }`

`starts_with(<prefix>)` — slot string starts with prefix.
- `{ slot: path, op: starts_with, value: '/admin' }`

`ends_with(<suffix>)` — slot string ends with suffix.
- `{ slot: filename, op: ends_with, value: '.exe' }`

`contains(<substring>)` — slot string contains substring.
- `{ slot: user_input, op: contains, value: 'ignore previous instructions' }`

## Arithmetic (in actions / bind expressions)

`+`, `-`, `*`, `/`, `%` — standard arithmetic in CLIPS s-expression form.
- `{ bind: ?total, value: "(+ $req.amount $req.fee)" }`
- `{ bind: ?ratio, value: "(/ $r.failed $r.total)" }`
- `{ bind: ?bucket, value: "(% $h.minutes 60)" }`

## Classification

Lattice ordering for hierarchies declared via `hierarchies:` (e.g.
`unclassified < confidential < secret < top_secret`). The four ops below
require a `type: classification` function and a matching hierarchy.

`below(<other>)` — left value's rank is strictly less than right's.
- `{ slot: clearance, op: below, value: $d.classification }`

`meets_or_exceeds(<other>)` — left rank >= right rank.
- `{ slot: clearance, op: meets_or_exceeds, value: secret }`

`dominates(<other>)` — total lattice ordering: left dominates right (>=).
- `{ slot: label, op: dominates, value: $req.requested_label }`

`compartment_subset(<other>)` — left compartment set is a subset of right.
- `{ slot: compartments, op: compartment_subset, value: $clearance.compartments }`

`compartment_intersects(<other>)` — left and right compartment sets share ≥1 elem.
- `{ slot: tags, op: compartment_intersects, value: [SCI, NOFORN] }`

`within_scope(<other>)` — both values are in-hierarchy (rank >= 0).
- `{ slot: clearance, op: within_scope, value: $d.classification }`

## Temporal

Window arguments are ISO-8601 durations (`PT5M`) or seconds (int). All read
back over the audit log of recently asserted facts; rule firings within the
window contribute to the count/rate.

`count_exceeds(template, slot, threshold, window)` — N matching facts in window.
- `{ test: "(count_exceeds login_failure user $u.id 5 PT15M)" }`

`rate_exceeds(template, slot, rate_per_sec, window)` — sliding-window rate.
- `{ test: "(rate_exceeds api_call endpoint /admin 10 PT1M)" }`

`changed_within(template, slot, window)` — slot's value changed in window.
- `{ test: "(changed_within agent role $a.id PT5M)" }`

`last_n(template, n)` — bind the most-recent N facts of template.
- `{ test: "(last_n login_event 10)" }`

`distinct_count(template, slot)` — number of distinct slot values in working mem.
- `{ test: "(distinct_count session ip_address)" }`

`sequence_detected(events)` — ordered sequence of named event facts seen.
- `{ test: "(sequence_detected (login_failure login_failure login_success))" }`

## Pattern syntax

**Bind variables**: prefix `?` (e.g. `?sid`, `?amt`). Bound on the LHS, usable
in peer conditions and on the RHS.
- `{ template: session, bind: ?s, slots: { id: ?sid } }`

**Wildcards**: `?_` matches any single value but does not bind.
- `{ template: agent, slot: role, op: eq, value: ?_ }`

**Slot pattern matching**: in the `slots:` map of a `bind` condition, each
entry is `<slot>: <pattern>`. A pattern may be a literal, a `?var` capture, a
cross-fact ref (`$alias.slot`), or an anchored sub-expression.
- `{ template: action, bind: ?act, slots: { actor: $a.id, type: read } }`

## Conflict resolution

When multiple rules are eligible at the same instant, Fathom resolves them in
this fixed order:

1. **Salience.** Higher `salience` fires first; lower `salience` fires later.
2. **Most recent fact (recency).** Within the same salience tier, the rule
   matching the most recently asserted fact fires first.
3. **Declared order.** Final tiebreak. Earlier-declared rule fires first.

The fail-closed convention is to give `deny` rules **lower** salience than
`allow` rules so `deny` fires *last* and last-write-wins on the decision fact
overwrites any prior `allow`.

## See also

- `rule-yaml-schema.md` — full schema for `templates`, `rules`, `modules`,
  `functions`.
- `rule-packs.md` — shipped packs and their decision spaces.
