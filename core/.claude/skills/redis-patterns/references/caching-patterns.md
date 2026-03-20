# Caching Patterns

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
