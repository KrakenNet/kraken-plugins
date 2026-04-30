---
description: Scaffold + verify Harbor graphs. Writes state.py, nodes/, rules/, harbor.yaml, tests; runs harbor graph verify; iterates.
tools: [Bash, Read, Write, Edit]
---

# Graph Builder

## Inputs

- `graph_name`, `purpose`, `nodes` (list), `state_fields` (list of (name, type, annotated)), `rule_packs`, `stores`.

## Steps

1. Create dir `graphs/<graph_name>/`.
2. Write `state.py`:

```python
from pydantic import BaseModel, Field
from typing import Annotated
from harbor.annotations import Mirror

class State(BaseModel):
    # for each field: if annotated, wrap with `Annotated[<type>, Mirror()]`
    pass
```

3. Write `nodes/__init__.py` exporting node functions/classes.
4. Write `rules/_starter.yaml` (one default routing rule).
5. Write `harbor.yaml` per the schema in `references/graph-yaml-schema.md`.
6. Write `tests/test_graph.py` — runs the graph against fixture state, asserts at least one transition.
7. Run `uv run harbor graph verify graphs/<graph_name>/harbor.yaml`.
8. On error, parse + fix, retry.

## Output

Tree, verify status.
