# Nautilus Adapter SDK

Reference for authoring custom Nautilus adapters. Adapters bridge the broker to a concrete data source (Postgres, REST API, vector store, etc.).

## Adapter Protocol

An adapter is a Python class implementing the following protocol:

```python
from typing import Protocol
from nautilus.types import AdapterResult, ScopeFilter

class Adapter(Protocol):
    def __init__(self, config: dict) -> None: ...
    def query(self, scope_filter: ScopeFilter, limit: int) -> AdapterResult: ...
    def health(self) -> bool: ...
    def close(self) -> None: ...
    def attest(self, payload: bytes) -> bytes: ...  # optional
```

### Required methods

| Method | Purpose |
|---|---|
| `__init__(config)` | Receives the source block from `nautilus.yaml`. Validate required fields here, fail fast. |
| `query(scope_filter, limit)` | Execute the request. Return an `AdapterResult`. |
| `health()` | Cheap liveness probe. Return `True` if the adapter can reach its source. |
| `close()` | Release connection-pool / file-handle / network resources. Called at broker shutdown. |

### Optional methods

| Method | Purpose |
|---|---|
| `attest(payload)` | Co-sign attestation payloads when the adapter is the signing authority for its data (e.g. an LLM session-signing adapter). Return raw signature bytes. |

## Result Shape

```python
from dataclasses import dataclass

@dataclass
class AdapterResult:
    rows: list           # list of dicts (or any JSON-serializable records)
    source_id: str       # the source's id from nautilus.yaml
    scope_applied: dict  # the scope filter the adapter actually applied
    error: str | None    # None on success; error message on failure
```

`scope_applied` is round-tripped back through the audit log so operators can verify scope enforcement happened where they expected.

## Entry-Point Registration

Adapters register via Python entry points in `pyproject.toml`:

```toml
[project.entry-points."nautilus.adapters"]
mycorp-warehouse = "mycorp_nautilus.warehouse:WarehouseAdapter"
```

The broker discovers and loads adapters at startup. Multiple adapters per package are fine.

## Capability Declaration

Adapters MUST declare what `data_types` and operations they support. Two equivalent forms are supported:

### Class attribute form

```python
class WarehouseAdapter:
    SUPPORTED_DATA_TYPES = {"customer-pii", "orders"}
    SUPPORTED_OPERATIONS = {"read", "search"}
    SCOPE_MODE = "native"  # or "broker-side"
```

### Method form

```python
class WarehouseAdapter:
    @classmethod
    def capabilities(cls) -> dict:
        return {
            "data_types": ["customer-pii", "orders"],
            "operations": ["read", "search"],
            "scope_mode": "native",
        }
```

`/nautilus:adapter-coverage` consumes these declarations to render the coverage matrix.

## Scope Filter Contract

The broker passes a normalized scope dict to `query()`:

```python
{
  "where": ["tenant_id = $session.tenant", "region = 'us-east-1'"],
  "limit": 100,
  "session": {"tenant": "acme", "user": "u-123"},
}
```

The adapter MUST apply the filter in one of two modes (declared via `SCOPE_MODE` / `scope_mode`):

- `native` — translate the filter into the source's native authorization or query (e.g. row-level security, IAM policy, SQL `WHERE`). Preferred for sources that have native enforcement.
- `broker-side` — fetch a candidate set, then filter in-process before returning. Required for sources without native predicate support (e.g. some REST APIs).

In either mode, set `scope_applied` on the result to the filter expressions that were enforced.

## Configuration

Adapters receive their `nautilus.yaml` source block via `__init__(config)`. Validate at init:

```python
class WarehouseAdapter:
    def __init__(self, config: dict):
        self.url = config["url"]
        self.classification = config["classification"]
        if not self.url.startswith("warehouse://"):
            raise ValueError(f"WarehouseAdapter url must be warehouse://; got {self.url}")
        self._pool = self._connect()
```

Fail fast on missing required fields. The broker surfaces init errors at startup so operators see them immediately.

## Conformance Tests

Use `nautilus.testing.AdapterConformance` to verify your adapter satisfies the protocol:

```python
from nautilus.testing import AdapterConformance
from mycorp_nautilus.warehouse import WarehouseAdapter

def test_conformance():
    suite = AdapterConformance(WarehouseAdapter, config={
        "id": "test",
        "adapter": "mycorp-warehouse",
        "url": "warehouse://test",
        "classification": "unclassified",
        "data_types": ["orders"],
    })
    suite.run()  # raises on any conformance violation
```

The suite checks: `__init__` validation, `query()` return shape, `health()` truthiness, `close()` idempotency, `scope_applied` echo, capability declaration presence.

## Minimal Adapter Example

```python
# mycorp_nautilus/warehouse.py
from nautilus.types import AdapterResult

class WarehouseAdapter:
    SUPPORTED_DATA_TYPES = {"orders"}
    SUPPORTED_OPERATIONS = {"read"}
    SCOPE_MODE = "broker-side"

    def __init__(self, config: dict):
        self.source_id = config["id"]
        self.url = config["url"]
        if not self.url.startswith("warehouse://"):
            raise ValueError("warehouse:// url required")
        self._client = _connect(self.url)

    def query(self, scope_filter, limit: int) -> AdapterResult:
        try:
            rows = self._client.fetch_orders(limit=limit)
            applied = {"where": scope_filter.get("where", [])}
            rows = [r for r in rows if _matches(r, applied["where"])]
            return AdapterResult(
                rows=rows,
                source_id=self.source_id,
                scope_applied=applied,
                error=None,
            )
        except Exception as e:
            return AdapterResult(rows=[], source_id=self.source_id, scope_applied={}, error=str(e))

    def health(self) -> bool:
        try:
            return self._client.ping()
        except Exception:
            return False

    def close(self) -> None:
        self._client.close()
```

Register in `pyproject.toml`:

```toml
[project.entry-points."nautilus.adapters"]
mycorp-warehouse = "mycorp_nautilus.warehouse:WarehouseAdapter"
```

Use in `nautilus.yaml`:

```yaml
sources:
  - id: orders
    adapter: mycorp-warehouse
    url: warehouse://prod
    classification: confidential
    data_types: [orders]
```
