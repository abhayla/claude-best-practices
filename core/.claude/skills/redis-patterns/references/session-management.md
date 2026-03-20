# Session Management

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

