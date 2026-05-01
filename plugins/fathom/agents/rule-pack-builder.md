---
description: Scaffold + validate + test loop for Fathom rule packs. Writes pack.yaml, templates/, rules/, modules/, functions/, tests/, README; runs `fathom validate` and `fathom test`; iterates on failures.
tools: [Bash, Read, Write, Edit, AskUserQuestion]
---

# Rule Pack Builder

## Inputs

- `pack_name` (kebab-case)
- `target_dir` (absolute path)
- `description`, `license`, `domain`, `decision_space`
- `initial_rule_sketch` (optional)

## Steps

1. `mkdir -p <target_dir>/{templates,rules,modules,functions,tests}`
2. Write `<target_dir>/pack.yaml`:

```yaml
name: <pack-name>
version: 0.1.0
description: <description>
license: <license>
fathom_min_version: "0.3.1"
templates_dir: ./templates
rules_dir: ./rules
modules_dir: ./modules
functions_dir: ./functions
```

3. Write `<target_dir>/README.md` with title, decision space table, install instructions.
4. Write `<target_dir>/templates/_starter.yaml` with one minimal `deftemplate` (e.g., `request` with `id`, `purpose`).
5. Write `<target_dir>/rules/_starter.yaml` with a single placeholder rule that always emits the default decision.
6. Write `<target_dir>/tests/test_starter.py` with a pytest that loads the pack and runs one assertion.

## Build-Test-Fix Loop

Max 5 iters.

1. Run `cd <target_dir> && uv run fathom validate .` (if Fathom installed).
2. On error: parse first error line, fix the offending file, retry.
3. Run `uv run pytest tests/`.
4. On failure: read failure, fix or surface to user.

## Output

Report:
- File tree
- Validate status
- Test status
- Suggested next commands (`/fathom:new-rule`, `/fathom:new-template`).
