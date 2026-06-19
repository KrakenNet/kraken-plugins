# Stargraph Store Protocols

Stargraph abstracts data tiers behind five Protocols: `vector`, `graph`, `doc`, `memory`, `fact`. Plugins register concrete providers via entry points; graphs declare which provider to mount per tier in the graph IR (`stargraph.yaml`). Embedded providers are the default so a fresh `stargraph run` works air-gapped without external services.

Every Protocol exposes a uniform lifecycle: `bootstrap()` (idempotent schema install), `health() -> StoreHealth`, and `migrate(plan)` (v1 supports `add_column` only). Embedded providers serialize writes through a single-writer-per-path lock.

## VectorStore

Dense retrieval. Methods:

```python
class VectorStore(Protocol):
    def add(self, id: str, vector: list[float], metadata: dict) -> None: ...
    def search(self, query_vector: list[float], k: int, filter: dict | None = None) -> list[Hit]: ...
    def delete(self, id: str) -> None: ...
```

`Hit` is `(id, score, metadata)`. `filter` is a provider-specific predicate language; portable filters use a small subset (`{"key": "value"}` exact match, `{"key": {"$gt": n}}` range).

Default provider: **`LanceDBVectorStore`** (provider id `stargraph.stores.lancedb`, wired as `lancedb:./.lance`). External: Pinecone, Weaviate, Qdrant.

## GraphStore

Property graph. Methods:

```python
class GraphStore(Protocol):
    def add_node(self, id: str, labels: list[str], props: dict) -> None: ...
    def add_edge(self, src: str, dst: str, type: str, props: dict) -> None: ...
    def query_subgraph(self, root: str, depth: int, edge_filter: dict | None = None) -> Subgraph: ...
    def cypher(self, query: str, params: dict | None = None) -> list[dict]: ...
```

Default provider: **`RyuGraphStore`** (provider id `stargraph.stores.ryugraph` / `stargraph.stores.cypher`, wired as `ryugraph:./.ryu`). RyuGraph is a Kuzu fork; queries use a portable Cypher subset (checked by `Linter`). External: Neo4j, Memgraph.

## DocStore

Document store with full-text search. Methods:

```python
class DocStore(Protocol):
    def put(self, id: str, doc: dict) -> None: ...
    def get(self, id: str) -> dict | None: ...
    def search(self, text: str, k: int, filter: dict | None = None) -> list[Hit]: ...
```

`doc` is any JSON-serializable mapping. `search` runs FTS on text fields the provider has indexed.

Default provider: **`SQLiteDocStore`** (provider id `stargraph.stores.sqlite_doc`, wired as `sqlite:./.docs`, SQLite WAL). External: Elasticsearch, OpenSearch, Postgres + tsvector.

## MemoryStore

Short-lived key/value with TTL. Methods:

```python
class MemoryStore(Protocol):
    def store(self, key: str, value: Any, ttl: int | None = None) -> None: ...
    def get(self, key: str) -> Any | None: ...
    def forget(self, key: str) -> None: ...
```

`ttl` in seconds. Values are JSON-serializable. Keys are scoped per run by default; cross-run keys require an explicit prefix.

Default provider: **`SQLiteMemoryStore`** (provider id `stargraph.stores.sqlite_memory`, wired as `sqlite:./.memory`, SQLite WAL). External: Redis, Memcached.

## FactStore

Semantic-fact storage, keyed at `(user, agent)` and session-independent. Methods:

```python
class FactStore(Protocol):
    async def pin(self, fact: Fact) -> None: ...
    async def query(self, pattern: FactPattern) -> list[Fact]: ...
    async def unpin(self, fact_id: str) -> None: ...
```

`pin` is insert-or-replace by `fact.id`. A `Fact` carries `id`, `user`, `agent`, `payload`, a **mandatory** `lineage` (each entry traces back to originating episode/triple ids or rule firings), `confidence`, `pinned_at`, and `metadata`. `FactPattern` matches on `subject`/`predicate`/`object` slots plus the `user`/`agent` columns; a `None` slot is a wildcard.

Default provider: **`SQLiteFactStore`** (provider id `stargraph.stores.sqlite_fact`, wired as `sqlite:./.facts`, SQLite WAL + the `FathomAdapter`). The `apply_delta` provider extension is the lineage seam used to promote consolidated memory deltas into pinned facts.

## Registration: StoreSpec and StoreRef

A provider plugin registers via the `stargraph.stores` entry-point group plus a `register_stores()` hook returning `list[StoreSpec]`:

```toml
# pyproject.toml of a store-providing plugin
[project.entry-points."stargraph.stores"]
my_vector = "my_pkg._plugin:manifest"
```

`StoreSpec` is the canonical registration record: `{name, provider, protocol, config_schema, capabilities}`. `protocol` is one of `vector`/`graph`/`doc`/`memory`/`fact`; `config_schema` is the JSON Schema for the provider's config; an empty `capabilities` list defaults to the `db.{name}:read` / `db.{name}:write` pair.

Inside an `IRDocument`, a graph mounts a store as a lightweight **`StoreRef`** — `{name, provider}`:

```yaml
stores:
  - { name: "kb",    provider: "stargraph.stores.lancedb" }
  - { name: "facts", provider: "stargraph.stores.sqlite_fact" }
```

`StoreRef.to_capabilities()` returns `["db.{name}:read", "db.{name}:write"]` — the capability strings Bosun's policy gates check.

The compact `<kind>: <provider>:<path>` form (e.g. `vector: lancedb:./.lance`) is the YAML shorthand the runtime parses into a `StoreRef`.

## Embedded vs External

| Tier | Embedded default | External options |
|---|---|---|
| Vector | LanceDB (`stargraph.stores.lancedb`) | Pinecone, Weaviate, Qdrant |
| Graph | RyuGraph (`stargraph.stores.ryugraph` / `…cypher`) | Neo4j, Memgraph |
| Doc | SQLite WAL (`stargraph.stores.sqlite_doc`) | Elasticsearch, Postgres + tsvector |
| Memory | SQLite WAL (`stargraph.stores.sqlite_memory`) | Redis, Memcached |
| Fact | SQLite WAL + FathomAdapter (`stargraph.stores.sqlite_fact`) | Postgres |

Embedded providers are the default because:

- `stargraph run` works on a fresh checkout with no docker / cloud setup.
- Air-gapped and on-device deployments are first-class.
- Tests run without fixtures or test containers.

External providers are the default in production-scale deployments where multiple processes share state, retention policies require managed services, or scale exceeds embedded engine limits.
