# Stargraph State Schema

State is the typed bundle that flows through every node of a Stargraph graph. It is the source of truth — facts in CLIPS are merely a projection of annotated state at node boundaries.

## Declaring state in the IR

An `IRDocument` declares state one of two mutually-exclusive ways:

- `state_class: "module.path:ClassName"` — reference an existing Pydantic model.
- `state_schema:` — a flat `name -> type-string` map for simple primitive state.

```yaml
# stargraph.yaml — reference a Pydantic model
state_class: "graph.state:RunState"
```

```yaml
# OR a flat primitive map
state_schema:
  message: "str"
  severity: "int"
```

The two are mutually exclusive (resolved at `Graph` construction, not in IR validation).

## Pydantic Foundation

State is a Pydantic `BaseModel`. Nodes receive State as input and return a (possibly mutated) State as output. Inside the node body, mutate freely in plain Python — Stargraph only cares about the boundary.

```python
from pydantic import BaseModel, Field
from datetime import datetime

class State(BaseModel):
    query: str
    documents: list[str] = Field(default_factory=list)
    answer: str | None = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
```

Nodes are pure-ish functions of `State -> State`. Use `model_copy(update={...})` for immutable style; direct mutation is also allowed because Stargraph snapshots at node-exit.

## Annotated Fields

Fields wrapped in `Annotated[<type>, Mirror()]` are mirrored to CLIPS at the node-exit boundary. Non-mirrored fields stay Python-only — useful for blobs, large tensors, secrets, or anything you don't want rules pattern-matching on.

```python
from typing import Annotated
from pydantic import BaseModel, Field
from stargraph.ir import Mirror

class State(BaseModel):
    query: Annotated[str, Mirror()]
    confidence: Annotated[float, Mirror()] = 0.0
    answer: Annotated[str | None, Mirror()] = None
    raw_embeddings: list[float] = Field(default_factory=list)  # NOT mirrored
```

`Mirror` is a frozen marker appended to a field's `Annotated[...]` chain. `Mirror(template="...")` overrides the target CLIPS deftemplate (default: the field name); `Mirror(lifecycle=...)` tags the sync boundary as `"run"`, `"step"`, or `"pinned"`.

## Type Compatibility

Python types map to CLIPS facts as follows:

| Python | CLIPS |
|---|---|
| `str` | string slot |
| `int` | integer slot |
| `float` | float slot |
| `bool` | symbol slot (`TRUE`/`FALSE`) |
| `datetime` | string slot (ISO-8601) |
| `list[T]` | multislot of T |
| `dict[str, T]` | nested template |
| `BaseModel` | nested deftemplate |
| `Enum` | symbol slot |

Pydantic models nested under State become nested fact templates. `None` becomes the symbol `NIL`.

## YAML DSL Subset

For non-Python contributors, Stargraph compiles a YAML schema to Pydantic at graph load time. The DSL covers the common case; drop to Python for anything advanced.

YAML:

```yaml
state:
  fields:
    - name: query
      type: str
      mirror: true
    - name: confidence
      type: float
      default: 0.0
      mirror: true
    - name: documents
      type: list[str]
      default: []
```

Equivalent Python:

```python
class State(BaseModel):
    query: Annotated[str, Mirror()]
    confidence: Annotated[float, Mirror()] = 0.0
    documents: list[str] = Field(default_factory=list)
```

The YAML DSL supports: scalar types, `list[T]`, `dict[str, T]`, `Optional[T]` (via `nullable: true`), defaults, `mirror: true`, and `enum` declarations. Nested models, validators, computed fields, and custom serializers require Python.

## Schema Hash

The state schema contributes to the graph hash:

```
graph_hash = sha256(topology + node_signatures + state_schema_hash)
```

`state_schema_hash` is computed from the JSON Schema of the State model (stable field ordering). Adding a non-mirrored field with a default does not invalidate the hash if the JSON Schema is unchanged. Renaming a mirrored field, changing a type, or removing a field changes the hash.

Checkpoints record the graph hash. Resume rejects a hash mismatch unless the graph declares a `migrate:` block mapping `from_hash → to_hash`.

## Replay-Safe Collections

State fields must use hashable, immutable collections so replay is deterministic. A field typed as `set` or `set[X]` (including a nested `set`) is **rejected** at construction time — use `frozenset` instead. When state is a skill's `state_schema`, its field names double as the declared output channels (the write-whitelist the engine enforces at the subgraph boundary); see `references/store-protocols.md` and the skill model for detail.

## Worked Example

A small Research graph state:

```python
from typing import Annotated, Literal
from datetime import datetime
from pydantic import BaseModel, Field
from stargraph.ir import Mirror

class Citation(BaseModel):
    url: Annotated[str, Mirror()]
    snippet: str
    score: Annotated[float, Mirror()]

class ResearchState(BaseModel):
    query: Annotated[str, Mirror()]
    plan: Annotated[list[str], Mirror()] = Field(default_factory=list)
    citations: Annotated[list[Citation], Mirror()] = Field(default_factory=list)
    answer: Annotated[str | None, Mirror()] = None
    phase: Annotated[Literal["plan", "search", "synthesize", "done"], Mirror()] = "plan"
    started_at: datetime = Field(default_factory=datetime.utcnow)  # not mirrored
    notes: str = ""  # not mirrored
```

At node-exit, Stargraph mirrors `query`, `plan`, `citations` (each Citation as a nested fact), `answer`, and `phase` into CLIPS. A Bosun rule pack can then match e.g. `(state (phase "search") (citations $?cs&:(>= (length$ ?cs) 3)))` to route to synthesis.
