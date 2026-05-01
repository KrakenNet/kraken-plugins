---
description: Translate natural-language constraints into Fathom defrule YAML + pytest test cases. Iterates until validate + test pass.
tools: [Bash, Read, Write, Edit]
---

# Rule Author

## Inputs

- `pack_dir`, `rule_name`
- `description` (natural language)
- `templates` (list of in-pack templates)
- `decision`, `test_cases`

## Steps

1. Decompose the description into `when` conditions, mapping operators from `references/clips-cheatsheet.md`.
2. Write `<pack-dir>/rules/<rule-name>.yaml`:

```yaml
rules:
  - name: <rule-name>
    when:
      - template: <template>
        alias: <alias>            # optional; required for $alias.field cross-refs
        conditions:
          - slot: <slot>
            expression: <op>(<arg>)
    then:
      action: <decision>
      reason: "<rendered reason>"
```

3. Write `<pack-dir>/tests/test_<rule-name>.py` covering each test case.
4. Run `uv run fathom validate <pack-dir>` — fix on errors.
5. Run `uv run pytest <pack-dir>/tests/test_<rule-name>.py` — fix on failures.
6. Max 5 iters.

## Output

Rule body, test file, validate + test status.
