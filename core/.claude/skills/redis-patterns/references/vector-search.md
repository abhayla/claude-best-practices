# Vector Search

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

