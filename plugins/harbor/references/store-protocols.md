# Harbor Store Protocols

Harbor abstracts data tiers behind five Protocols. Plugins register concrete providers via entry points; graphs declare which provider to mount per tier in `harbor.yaml`. Embedded providers are the default so a fresh `harbor run` works air-gapped without external services.

## VectorStore

Dense retrieval. Methods:

```python
class VectorStore(Protocol):
    def add(self, id: str, vector: list[float], metadata: dict) -> None: ...
    def search(self, query_vector: list[float], k: int, filter: dict | None = None) -> list[Hit]: ...
    def delete(self, id: str) -> None: ...
```

`Hit` is `(id, score, metadata)`. `filter` is a provider-specific predicate language; portable filters use a small subset (`{"key": "value"}` exact match, `{"key": {"$gt": n}}` range).

Default provider: **LanceDB** (`lancedb:./.lance`). External: Pinecone, Weaviate, Qdrant.

## GraphStore

Property graph. Methods:

```python
class GraphStore(Protocol):
    def add_node(self, id: str, labels: list[str], props: dict) -> None: ...
    def add_edge(self, src: str, dst: str, type: str, props: dict) -> None: ...
    def query_subgraph(self, root: str, depth: int, edge_filter: dict | None = None) -> Subgraph: ...
    def cypher(self, query: str, params: dict | None = None) -> list[dict]: ...
```

Default provider: **Kuzu** (`kuzu:./.kuzu`). External: Neo4j, Memgraph.

## DocStore

Document store with full-text search. Methods:

```python
class DocStore(Protocol):
    def put(self, id: str, doc: dict) -> None: ...
    def get(self, id: str) -> dict | None: ...
    def search(self, text: str, k: int, filter: dict | None = None) -> list[Hit]: ...
```

`doc` is any JSON-serializable mapping. `search` runs FTS on text fields the provider has indexed.

Default provider: **SQLite + FTS5** (`sqlite:./.docs`). External: Elasticsearch, OpenSearch, Postgres + tsvector.

## MemoryStore

Short-lived key/value with TTL. Methods:

```python
class MemoryStore(Protocol):
    def store(self, key: str, value: Any, ttl: int | None = None) -> None: ...
    def get(self, key: str) -> Any | None: ...
    def forget(self, key: str) -> None: ...
```

`ttl` in seconds. Values are JSON-serializable. Keys are scoped per run by default; cross-run keys require an explicit prefix.

Default provider: **SQLite** (`sqlite:./.memory`). External: Redis, Memcached.

## FactStore

Provenance-typed fact log. Methods:

```python
class FactStore(Protocol):
    def assert_fact(self, fact: Fact, provenance: Provenance) -> None: ...
    def query(self, pattern: dict) -> list[Fact]: ...
    def retract(self, fact: Fact) -> None: ...
```

Note: `assert` is a Python keyword, so the method is `assert_fact`. `pattern` is a structured matcher: `{"template": "citation", "origin": "tool", "min_confidence": 0.8}`.

Default provider: **in-memory + SQLite persist** (`sqlite:./.facts`). The in-memory tier is the live CLIPS environment; the SQLite tier is the append-only audit log used for replay.

## Provider Registration

Providers register via Python entry points under the `harbor.stores.<type>` group:

```toml
# pyproject.toml of a harbor-pinecone plugin
[project.entry-points."harbor.stores.vector"]
pinecone = "harbor_pinecone:PineconeProvider"
```

A graph then mounts it:

```yaml
stores:
  vector: pinecone:my-index?env=production
```

The string after the provider name is provider-specific config (URI, query string, or JSON depending on the provider).

## Embedded vs External

| Tier | Embedded default | External options |
|---|---|---|
| Vector | LanceDB | Pinecone, Weaviate, Qdrant |
| Graph | Kuzu | Neo4j, Memgraph |
| Doc | SQLite + FTS5 | Elasticsearch, Postgres + tsvector |
| Memory | SQLite | Redis, Memcached |
| Fact | SQLite + in-memory CLIPS | Postgres |

Embedded providers are the default because:

- `harbor run` works on a fresh checkout with no docker / cloud setup.
- Air-gapped and on-device deployments are first-class.
- Tests run without fixtures or test containers.

External providers are the default in production-scale deployments where multiple processes share state, retention policies require managed services, or scale exceeds embedded engine limits.
