# Redis Query Engine (RQE)

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
