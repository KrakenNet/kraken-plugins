---
description: Add a typed node to a Harbor graph; manage state-sync boundary; update graph hash.
tools: [Bash, Read, Write, Edit]
---

# Node Builder

## Inputs

- `graph_name`, `node_name`, `node_type` (dspy:* | model:* | tool:* | retrieval:* | subgraph:*).
- `inputs` (list of State fields), `outputs` (list with annotated flag).

## Steps

1. Add a node spec to `graphs/<graph>/harbor.yaml`.
2. Write/extend `nodes/__init__.py` with a function:

```python
def <node_name>(state: State) -> State:
    # read inputs, call underlying ...
    return state.copy(update={...})
```

3. If outputs are annotated, update `state.py` to wrap them in `Annotated[<type>, Mirror()]`.
4. Recompute graph hash; warn on hash change.
5. `uv run harbor graph verify graphs/<graph>/harbor.yaml`.
6. Add a fixture-based test in `tests/test_<node_name>.py`.

## Output

YAML diff, state.py diff, hash before/after, test status.
