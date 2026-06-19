---
description: Validate a Stargraph graph by loading it (IRDocument schema) and tracing its rules
argument-hint: <graph-path> [--fixtures <file>]
allowed-tools: [Bash, Read]
---

# Stargraph Verify Graph

There is no dedicated verify subcommand. A graph is validated by **loading**
it: the IR YAML is parsed and validated against `IRDocument`, and every IR
model pins `extra='forbid'`, so unknown keys, bad node `kind`s, malformed
rule `when/then` actions, or out-of-spec ids fail loudly at load.

## Run

Validate + print the rule-firing trace without executing any node:

```bash
uv run stargraph run "<graph-path>" --inspect
```

This prints a leading `graph_hash=<hex>` and `rule_firings=<count>` line. A
non-zero exit or a parse/validation error means the graph is invalid.

For a deeper check of rule logic against synthetic node outputs (still no
tools/LLM/checkpoint):

```bash
uv run stargraph simulate "<graph-path>" --fixtures "<fixtures.yaml>"
```

To validate in Python (e.g. in a test):

```python
import yaml
from stargraph import ir

doc = ir.validate(yaml.safe_load(open("<graph-path>")))  # raises on invalid IR
print(doc.id)
```

## Report

✓ valid, `graph_hash=<hex>`, summary of nodes/rules/stores (and `rule_firings`
from the `--inspect`/`simulate` trace). Or ✗ with the IRDocument validation
error block.
