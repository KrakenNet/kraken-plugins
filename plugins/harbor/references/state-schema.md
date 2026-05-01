# Harbor State Schema

State is the typed bundle that flows through every node of a Harbor graph. It is the source of truth — facts in CLIPS are merely a projection of annotated state at node boundaries.

## Pydantic Foundation

State is a Pydantic `BaseModel`. Nodes receive State as input and return a (possibly mutated) State as output. Inside the node body, mutate freely in plain Python — Harbor only cares about the boundary.

```python
from pydantic import BaseModel, Field
from datetime import datetime

class State(BaseModel):
    query: str
    documents: list[str] = Field(default_factory=list)
    answer: str | None = None
    started_at: datetime = Field(default_factory=datetime.utcnow)
```

Nodes are pure-ish functions of `State -> State`. Use `model_copy(update={...})` for immutable style; direct mutation is also allowed because Harbor snapshots at node-exit.

## Annotated Fields

Fields wrapped in `Annotated[<type>, Mirror()]` are mirrored to CLIPS at the node-exit boundary. Non-mirrored fields stay Python-only — useful for blobs, large tensors, secrets, or anything you don't want rules pattern-matching on.

```python
from typing import Annotated
from pydantic import BaseModel, Field
from harbor.annotations import Mirror

class State(BaseModel):
    query: Annotated[str, Mirror()]
    confidence: Annotated[float, Mirror()] = 0.0
    answer: Annotated[str | None, Mirror()] = None
    raw_embeddings: list[float] = Field(default_factory=list)  # NOT mirrored
```

`Mirror()` accepts options: `Mirror(name="...")` to override the CLIPS slot name, `Mirror(template="...")` to target a specific deftemplate.

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

For non-Python contributors, Harbor compiles a YAML schema to Pydantic at graph load time. The DSL covers the common case; drop to Python for anything advanced.

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

Checkpoints record the graph hash. `harbor replay` and `harbor run --resume` reject mismatches unless the graph declares a `migrate:` block mapping old → new fields.

## Worked Example

A small Research graph state:

```python
from typing import Annotated, Literal
from datetime import datetime
from pydantic import BaseModel, Field
from harbor.annotations import Mirror

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

At node-exit, Harbor mirrors `query`, `plan`, `citations` (each Citation as a nested fact), `answer`, and `phase` into CLIPS. A Bosun rule pack can then match e.g. `(state (phase "search") (citations $?cs&:(>= (length$ ?cs) 3)))` to route to synthesis.
