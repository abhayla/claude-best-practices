---
name: redis-patterns
description: >
  Redis 7+ development patterns and best practices: data structure selection, caching strategies,
  connection management, Redis Query Engine, vector search, JSON documents, streams, pub/sub,
  security, and observability. Use when designing or optimizing Redis-backed features.
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "<redis-task-or-question>"
---

# Redis Patterns Reference

Comprehensive Redis 7+ patterns for data modeling, caching, querying, and operations. Based on
the official Redis agent-skills repository (29 rules across 11 categories).

**Request:** $ARGUMENTS

---

## Data Structure Selection

| Use Case | Type | Why |
|----------|------|-----|
| Simple values, counters | String | Fast, atomic INCR/DECR |
| Object with fields | Hash | Memory efficient, partial updates, field-level expiration |
| Queue, recent items | List | O(1) push/pop at ends |
| Unique items, membership | Set | O(1) add/remove/check |
| Rankings, rate limiting | Sorted Set | Score-based ordering, range queries |
| Nested/hierarchical data | JSON | Path queries, nested atomic updates, geospatial indexing |
| Event logs, messaging | Stream | Persistent, consumer groups, replay |
| Similarity search | Vector Set | Native HNSW indexing |

```python
# Hash for objects — atomic field updates without read-modify-write
r.hset("user:1001", mapping={"name": "Alice", "email": "alice@example.com"})
r.hset("user:1001", "email", "new@example.com")  # Update single field

# Sorted Set for leaderboards
r.zadd("leaderboard", {"player:42": 1500, "player:7": 2100})
top_10 = r.zrevrange("leaderboard", 0, 9, withscores=True)
```

## Key Naming Conventions

Use colons as separators with a consistent hierarchy: `service:entity:id[:attribute]`

```
user:1001:profile
user:1001:settings
order:2024:items
cache:api:users:list
session:abc123
```

**Rules:**
- Keep keys short but readable -- they consume memory
- Use consistent separators (colons are conventional)
- Extract short identifiers from URLs instead of using full URLs as keys
- In Redis Cluster, use hash tags for multi-key ops: `{user:1001}:profile`, `{user:1001}:cart`

## Caching Patterns

### Cache-Aside (Lazy Loading)

```python
import json

def get_user(user_id: str) -> dict:
    cached = r.get(f"cache:user:{user_id}")
    if cached:
        return json.loads(cached)

    user = db.query_user(user_id)  # Fetch from primary store
    r.setex(f"cache:user:{user_id}", 3600, json.dumps(user))  # Cache with TTL
    return user
```

### Write-Through

```python
def update_user(user_id: str, data: dict):
    db.update_user(user_id, data)  # Write to primary store
    r.setex(f"cache:user:{user_id}", 3600, json.dumps(data))  # Update cache
```

### Client-Side Caching (Redis 7+ with RESP3)

```python
import redis

client = redis.Redis(
    host='localhost', port=6379,
    protocol=3,  # RESP3 required
    cache_config=redis.CacheConfig(max_size=1000)
)
# Subsequent reads for the same key avoid server round-trips
value = client.get("frequently:read:key")
```

## TTL and Memory Management

**MUST** set TTL on all cache keys to prevent unbounded growth:

```python
# Atomic set + TTL
r.setex("cache:user:1001", 3600, user_json)

# Hash with TTL
r.hset("session:abc", mapping=session_data)
r.expire("session:abc", 1800)

# Hash field expiration (Redis 7.4+)
r.hexpire("sensor:s1", 60, "air_quality", "battery_level")
```

**Memory limits** -- always configure in production:

```
maxmemory 2gb
maxmemory-policy allkeys-lru
```

| Policy | Use Case |
|--------|----------|
| `volatile-lru` | Evict keys with TTL, least recently used first |
| `allkeys-lru` | Evict any key, least recently used first |
| `volatile-ttl` | Evict keys closest to expiration |
| `noeviction` | Return errors when full (critical data) |

## Rate Limiting with Sorted Sets

```python
import time

def is_rate_limited(user_id: str, limit: int = 100, window: int = 60) -> bool:
    key = f"ratelimit:{user_id}"
    now = time.time()
    pipe = r.pipeline()
    pipe.zremrangebyscore(key, 0, now - window)  # Remove expired entries
    pipe.zadd(key, {f"{now}": now})               # Add current request
    pipe.zcard(key)                                # Count requests in window
    pipe.expire(key, window)                       # Auto-cleanup
    _, _, count, _ = pipe.execute()
    return count > limit
```

## Session Management

```python
import json, secrets

def create_session(user_id: str, ttl: int = 1800) -> str:
    session_id = secrets.token_urlsafe(32)
    r.hset(f"session:{session_id}", mapping={
        "user_id": user_id,
        "created_at": str(time.time()),
        "ip": request.remote_addr
    })
    r.expire(f"session:{session_id}", ttl)
    return session_id

def get_session(session_id: str) -> dict | None:
    data = r.hgetall(f"session:{session_id}")
    if data:
        r.expire(f"session:{session_id}", 1800)  # Slide expiration
    return data or None
```

## Connection Management

### Connection Pooling

```python
import redis

# CORRECT: Reuse connections via pool
pool = redis.ConnectionPool(host='localhost', port=6379, max_connections=50)
r = redis.Redis(connection_pool=pool)

# WRONG: New connection per request
def get_user(uid):
    r = redis.Redis(host='localhost', port=6379)  # Do NOT do this
    return r.get(f"user:{uid}")
```

### Timeouts

```python
r = redis.Redis(
    host='localhost',
    socket_timeout=5.0,         # Read/write timeout
    socket_connect_timeout=2.0,  # Connection timeout -- shorter for fast failure
    retry_on_timeout=True
)
```

### Pipelining for Bulk Operations

Batch multiple commands into a single round trip (5-10x faster):

```python
pipe = r.pipeline()
for user_id in user_ids:
    pipe.get(f"user:{user_id}")
results = pipe.execute()
```

### Transactions (MULTI/EXEC)

```python
# Atomic multi-command execution
pipe = r.pipeline(transaction=True)
pipe.set("person:1:name", "Alex")
pipe.set("person:1:rank", "Captain")
pipe.execute()  # All-or-nothing
```

Use `pipeline(transaction=False)` when you only need batching without atomicity.

### Atomic Counters

```python
# CORRECT: Atomic increment
new_value = r.incr("counter")
new_value = r.incrby("counter", 10)

# WRONG: Read-modify-write race condition
curr = int(r.get("counter"))
r.set("counter", str(curr + 1))  # Not atomic!
```

## JSON Document Patterns

### Partial Updates with JSON Paths

```python
# Store nested document
r.json().set("user:1001", "$", {
    "name": "Alice",
    "preferences": {"theme": "dark", "notifications": True}
})

# Update nested field atomically
r.json().set("user:1001", "$.preferences.theme", "light")

# Get specific field
theme = r.json().get("user:1001", "$.preferences.theme")

# Atomic numeric increment
r.json().numincrby("user:1001", "$.preferences.volume", 5)

# Append to array
r.json().arrappend("user:1001", "$.tags", "premium")
```

### JSON vs Hash vs String

| Feature | JSON | Hash | String |
|---------|------|------|--------|
| Nested structures | Yes | No (flat only) | Any (serialized) |
| Atomic partial updates | Yes (`$.field`) | Yes (`HGET/HSET`) | No |
| RQE indexing | Yes | Yes | No |
| Field-level expiration | No | Yes (`HEXPIRE`) | No |
| Memory efficiency | Higher overhead | More efficient | Most compact |

- **JSON**: Nested structures needing atomic partial updates and indexing
- **Hash**: Flat objects with atomic field access or field-level expiration
- **String**: Simple caching where you always read/write the entire object

## Redis Query Engine (RQE)

### Index Creation

Index only the fields you query. Always specify a prefix:

```python
from redis.commands.search.field import TextField, TagField, NumericField, VectorField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType

schema = [
    TextField("name", weight=2.0),
    TagField("category", sortable=True),
    NumericField("price", sortable=True),
]

r.ft("idx:products").create_index(
    schema,
    definition=IndexDefinition(prefix=["product:"], index_type=IndexType.HASH)
)
```

### Field Type Selection

| Field Type | Use When | Notes |
|------------|----------|-------|
| TEXT | Full-text search needed | Tokenized, stemmed |
| TAG | Exact match, filtering | 10x faster than TEXT for filtering |
| NUMERIC | Range queries, sorting | Prices, counts, timestamps |
| GEO | Point location queries | Lat/long coordinates |
| GEOSHAPE | Area/region queries | Polygons, circles |
| VECTOR | Similarity search | HNSW or FLAT algorithm |

### Querying

```python
# Specific filters + limit results
results = r.ft("idx:products").search(
    "@category:{electronics} @price:[100 500]",
    dialect=2
)

# Always use DIALECT 2 (required for vector search, better parsing)
```

### Index Management with Aliases (Zero-Downtime Updates)

```
FT.CREATE idx:products_v2 ON HASH PREFIX 1 product: SCHEMA ...
FT.ALIASADD products idx:products_v2
# Later: FT.ALIASUPDATE products idx:products_v3
```

### SKIPINITIALSCAN

Use when creating indexes for new data only (skips indexing existing keys):

```python
r.ft("idx").create_index(schema, definition=definition, skip_initial_scan=True)
```

## Vector Search

### Index Configuration

```python
from redis.commands.search.field import VectorField

VectorField(
    "embedding",
    algorithm="HNSW",
    attributes={
        "TYPE": "FLOAT32",
        "DIM": 1536,           # MUST match your embedding model
        "DISTANCE_METRIC": "COSINE"
    }
)
```

| Algorithm | Speed | Accuracy | Best For |
|-----------|-------|----------|----------|
| HNSW | Fast (approximate) | ~95%+ tunable | Large datasets (>10k vectors) |
| FLAT | Slower (exact) | 100% | Small datasets, accuracy-critical |

**HNSW tuning:** `M` (16-64, connections/node), `EF_CONSTRUCTION` (100-500, build quality), `EF_RUNTIME` (query accuracy vs speed).

### RAG Pattern with RedisVL

```python
from redisvl.index import SearchIndex
from redisvl.query import VectorQuery

# Store documents with embeddings
for doc in documents:
    embedding = embed_model.encode(doc["content"])
    index.load([{
        "content": doc["content"],
        "embedding": embedding.tolist(),
        "source": doc["source"]
    }])

# Query with vector similarity
results = index.search(VectorQuery(
    vector=embed_model.encode(user_question),
    vector_field_name="embedding",
    return_fields=["content", "source"],
    num_results=5
))

# Pass context to LLM
context = "\n".join([r["content"] for r in results])
response = llm.generate(f"Context: {context}\n\nQuestion: {user_question}")
```

### Hybrid Search (Vector + Filters)

```python
from redisvl.query import VectorQuery

query = VectorQuery(
    vector=query_embedding,
    vector_field_name="embedding",
    return_fields=["content", "category", "date"],
    num_results=10,
    filter_expression="@category:{technology} @date:[2024 2025]"
)
results = index.search(query)
```

Filters are applied before vector search, reducing computation. Use TAG for categories, NUMERIC for ranges.

## Semantic Caching (LangCache)

> LangCache is currently in preview on Redis Cloud.

```python
from langcache import LangCache

lang_cache = LangCache(
    server_url=f"https://{os.getenv('HOST')}",
    cache_id=os.getenv("CACHE_ID"),
    api_key=os.getenv("API_KEY")
)

result = lang_cache.search(prompt="What is Redis?", similarity_threshold=0.9)
if result:
    response = result[0]["response"]
else:
    response = llm.generate("What is Redis?")
    lang_cache.set(prompt="What is Redis?", response=response)
```

**Best practices:** Start threshold at 0.9. Use separate cache IDs for different LLM tasks. Use custom attributes for filtering within a cache.

## Pub/Sub vs Streams

| Requirement | Use |
|-------------|-----|
| Real-time notifications, OK to miss | Pub/Sub |
| Messages MUST NOT be lost | Streams |
| Replay/reprocess messages | Streams |
| Multiple workers on same queue | Streams (consumer groups) |
| Simple broadcast to connected clients | Pub/Sub |
| Event sourcing or audit trail | Streams |

### Pub/Sub

```python
# Publisher
r.publish("notifications", json.dumps({"event": "user_signup", "id": 42}))

# Subscriber
pubsub = r.pubsub()
pubsub.subscribe("notifications")
for message in pubsub.listen():
    if message["type"] == "message":
        handle(json.loads(message["data"]))
```

### Streams with Consumer Groups

```python
# Producer
r.xadd("orders:stream", {"order": json.dumps(order)})

# Consumer with acknowledgment
r.xreadgroup("workers", "worker-1", {"orders:stream": ">"}, count=10)
r.xack("orders:stream", "workers", message_id)
```

## Security

### Authentication and TLS

```python
r = redis.Redis(
    host='redis-host', port=6379,
    password='your-strong-password',
    ssl=True,
    ssl_cert_reqs='required'
)
```

### ACLs (Fine-Grained Access)

```
# Read-only cache user
ACL SETUSER app_readonly on >password ~cache:* +get +mget +scan

# Writer without dangerous commands
ACL SETUSER app_writer on >password ~* +@all -@dangerous
```

### Network Security

```
# redis.conf
bind 127.0.0.1 192.168.1.100
protected-mode yes

# Disable dangerous commands
rename-command FLUSHALL ""
rename-command DEBUG ""
rename-command CONFIG ""
```

## Observability

### Key Metrics to Monitor

| Metric | Alert When |
|--------|------------|
| `used_memory` | > 80% of maxmemory |
| `connected_clients` | Sudden spikes or drops |
| `blocked_clients` | > 0 sustained |
| `instantaneous_ops_per_sec` | Significant drops |
| `keyspace_hits/misses` | Hit ratio < 80% |
| `rejected_connections` | > 0 |

```python
info = r.info()
hit_ratio = info['keyspace_hits'] / (info['keyspace_hits'] + info['keyspace_misses']) * 100
print(f"Memory: {info['used_memory_human']}, Ops/sec: {info['instantaneous_ops_per_sec']}, Hit ratio: {hit_ratio:.1f}%")
```

### Debugging Commands

```
SLOWLOG GET 10          # Find slow commands
MEMORY USAGE mykey      # Per-key memory
MEMORY DOCTOR           # Memory diagnostics
FT.INFO idx:products    # Index stats
FT.PROFILE idx:products SEARCH QUERY "@name:laptop"  # Query profiling
CLIENT LIST             # Active connections
```

## Anti-Pattern Guardrails

| Anti-Pattern | Use Instead |
|--------------|-------------|
| `KEYS *` in production | `SCAN` with cursor and `COUNT` |
| `SMEMBERS` on large sets | `SSCAN` |
| `HGETALL` on large hashes | `HSCAN` |
| New connection per request | Connection pool (`ConnectionPool`) |
| Sequential commands in loops | `pipeline()` for batching |
| No `maxmemory` configured | Always set `maxmemory` + eviction policy |
| Cache keys without TTL | Always `setex()` or `expire()` |
| `FT.SEARCH "*" LIMIT 0 10000` | Use specific filters + `LIMIT` |
| `LOAD *` in aggregations | Return only needed fields |
| TEXT field for exact matching | TAG field (10x faster for filtering) |
| `bind 0.0.0.0` + `protected-mode no` | Bind specific interfaces, enable protection |
| Read-modify-write for counters | `INCR` / `INCRBY` (atomic) |

## Troubleshooting

| Issue | Diagnosis | Solution |
|-------|-----------|----------|
| High latency spikes | `SLOWLOG GET 10` | Replace `KEYS *` with `SCAN`; check large key ops |
| Memory growing unbounded | `INFO memory` | Set `maxmemory` + eviction; add TTL to cache keys |
| Connection refused | `INFO clients` | Enable connection pooling; check `maxclients` |
| CROSSSLOT error (Cluster) | Keys on different slots | Use hash tags: `{user:1001}:profile` |
| Vector search wrong results | Check index config | Verify `DIM` matches model; check `DISTANCE_METRIC` |
| Index not finding data | `FT.INFO idx` | Check prefix matches key pattern; verify field types |
| Stale reads from replicas | Replication lag | Use primary for consistency-critical reads |
| OOM kills | No `maxmemory` set | Configure memory limit and eviction policy |
| Slow index creation | Large existing dataset | Use `SKIPINITIALSCAN` if historical data not needed |

## References

- [Redis Best Practices](https://redis.io/docs/latest/develop/get-started/data-store/)
- [Redis Query Engine](https://redis.io/docs/latest/develop/interact/search-and-query/)
- [Redis Vector Search](https://redis.io/docs/latest/develop/interact/search-and-query/advanced-concepts/vectors/)
- [RedisVL](https://redis.io/docs/latest/integrate/redisvl/)
- [LangCache](https://redis.io/docs/latest/develop/ai/langcache/)
- [Redis Security](https://redis.io/docs/latest/operate/oss_and_stack/management/security/)
- [redis/agent-skills](https://github.com/redis/agent-skills) -- Source repository for these patterns
