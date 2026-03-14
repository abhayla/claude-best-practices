---
name: middleware-test
description: >
  Test middleware layers: auth (multi-layer), rate limiting, caching, request validation.
  Covers pass-through, rejection, and edge cases for each middleware type.
  Use when modifying or adding middleware to backend services.
allowed-tools: "Bash Read Grep Glob Write Edit"
triggers:
  - middleware test
  - auth middleware
  - rate limit test
  - cache test
argument-hint: "<middleware-type: auth|rate-limit|cache|validation|all>"
---

# Middleware Testing Patterns

Test middleware at multiple layers with pass-through, rejection, and edge case coverage.

**Arguments:** $ARGUMENTS

---

## AUTH MIDDLEWARE TESTING

### Multi-Layer Auth Verification

Test authentication at every enforcement point:

```python
# Layer 1: Edge middleware (pre-route)
async def test_auth_edge_rejects_no_token():
    response = await client.get("/api/users")
    assert response.status_code == 401
    assert response.json()["detail"] == "Missing authorization header"

async def test_auth_edge_rejects_expired_token():
    expired_token = create_token(exp=datetime.now() - timedelta(hours=1))
    response = await client.get("/api/users", headers={"Authorization": f"Bearer {expired_token}"})
    assert response.status_code == 401
    assert response.json()["detail"] == "Token expired"

# Layer 2: Handler-level permission checks
async def test_user_cannot_access_admin_endpoint():
    user_token = create_token(role="user")
    response = await client.get("/api/admin/users", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 403

async def test_user_cannot_access_other_user_data():
    user_token = create_token(user_id="user-1")
    response = await client.get("/api/users/user-2/profile", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 403

# Layer 3: Database session verification
async def test_deleted_user_token_rejected():
    token = create_token(user_id="deleted-user")
    # User exists in token but was deleted from DB
    response = await client.get("/api/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401
```

### Token Lifecycle Testing

```python
async def test_token_refresh_flow():
    # Login -> get access + refresh tokens
    login_response = await client.post("/api/auth/login", json={"email": "test@example.com", "password": "pass"})
    access_token = login_response.json()["access_token"]
    refresh_token = login_response.json()["refresh_token"]

    # Use access token
    response = await client.get("/api/users/me", headers={"Authorization": f"Bearer {access_token}"})
    assert response.status_code == 200

    # Refresh -> get new access token
    refresh_response = await client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
    new_access_token = refresh_response.json()["access_token"]
    assert new_access_token != access_token

    # Old access token should still work until expiry (or be revoked)
    # New access token should work
    response = await client.get("/api/users/me", headers={"Authorization": f"Bearer {new_access_token}"})
    assert response.status_code == 200
```

---

## RATE LIMITER TESTING

### Algorithm-Specific Tests

```python
# Fixed Window
async def test_fixed_window_rate_limit():
    for i in range(100):
        response = await client.get("/api/data")
        if i < 100:
            assert response.status_code == 200

    # 101st request should be rate limited
    response = await client.get("/api/data")
    assert response.status_code == 429
    assert "Retry-After" in response.headers
    retry_after = int(response.headers["Retry-After"])
    assert retry_after > 0

# Token Bucket — verify burst capacity
async def test_token_bucket_allows_burst():
    # Send burst of 10 requests simultaneously
    responses = await asyncio.gather(*[client.get("/api/data") for _ in range(10)])
    success_count = sum(1 for r in responses if r.status_code == 200)
    assert success_count == 10  # Burst capacity allows all 10

# Sliding Window — verify smooth rate limiting
async def test_sliding_window_smooth():
    responses = []
    for _ in range(120):  # Limit is 100/min
        responses.append(await client.get("/api/data"))
        await asyncio.sleep(0.5)  # Spread over 60 seconds

    # Should get ~100 successes with sliding window
    success_count = sum(1 for r in responses if r.status_code == 200)
    assert 95 <= success_count <= 105  # Sliding window is approximate
```

### Per-User vs Global Rate Limits

```python
async def test_per_user_rate_limit_isolation():
    """User A hitting their limit should NOT affect User B."""
    # User A exhausts their limit
    for _ in range(100):
        await client.get("/api/data", headers={"Authorization": f"Bearer {user_a_token}"})

    # User B should still have full capacity
    response = await client.get("/api/data", headers={"Authorization": f"Bearer {user_b_token}"})
    assert response.status_code == 200
```

---

## CACHE MIDDLEWARE TESTING

### Cache Hit/Miss/Invalidation

```python
async def test_cache_miss_then_hit():
    # First request — cache miss (hits DB)
    response1 = await client.get("/api/products/123")
    assert response1.headers.get("X-Cache") == "MISS"

    # Second request — cache hit (no DB query)
    response2 = await client.get("/api/products/123")
    assert response2.headers.get("X-Cache") == "HIT"
    assert response1.json() == response2.json()

async def test_cache_invalidation_on_update():
    # Populate cache
    await client.get("/api/products/123")

    # Update the resource
    await client.put("/api/products/123", json={"name": "Updated Product"})

    # Next GET should be cache miss with updated data
    response = await client.get("/api/products/123")
    assert response.headers.get("X-Cache") == "MISS"
    assert response.json()["name"] == "Updated Product"

async def test_cache_ttl_expiry():
    # Populate cache
    await client.get("/api/products/123")

    # Wait for TTL to expire (use time mocking in practice)
    await advance_time(seconds=301)  # TTL is 300s

    # Should be cache miss after TTL
    response = await client.get("/api/products/123")
    assert response.headers.get("X-Cache") == "MISS"

async def test_cache_stampede_protection():
    """Multiple concurrent requests for expired key should hit DB only once."""
    # Let cache expire, then send 10 concurrent requests
    responses = await asyncio.gather(*[client.get("/api/products/123") for _ in range(10)])

    # All should succeed
    assert all(r.status_code == 200 for r in responses)
    # Only 1 should be MISS (lock prevents stampede)
    misses = sum(1 for r in responses if r.headers.get("X-Cache") == "MISS")
    assert misses == 1
```

---

## REQUEST VALIDATION MIDDLEWARE

### Boundary and Malformed Input Testing

```python
async def test_rejects_malformed_json():
    response = await client.post("/api/users", content=b"not json",
                                  headers={"Content-Type": "application/json"})
    assert response.status_code == 422

async def test_rejects_wrong_content_type():
    response = await client.post("/api/users", content=b"name=test",
                                  headers={"Content-Type": "text/plain"})
    assert response.status_code == 415

async def test_rejects_oversized_payload():
    large_payload = {"data": "x" * 10_000_001}  # Over 10MB limit
    response = await client.post("/api/upload", json=large_payload)
    assert response.status_code == 413

async def test_error_response_matches_schema():
    """Error responses must match the documented error schema."""
    response = await client.post("/api/users", json={})  # Missing required fields
    assert response.status_code == 422
    error = response.json()
    assert "detail" in error
    assert isinstance(error["detail"], list)
    for err in error["detail"]:
        assert "loc" in err
        assert "msg" in err
        assert "type" in err
```

---

## MIDDLEWARE TESTING CHECKLIST

For each middleware type, test three cases:

| Middleware | Pass-Through | Rejection | Edge Case |
|-----------|-------------|-----------|-----------|
| **Auth** | Valid token -> 200 | No token -> 401 | Expired token, wrong scope, deleted user |
| **Rate Limit** | Under limit -> 200 | Over limit -> 429 | Burst capacity, per-user isolation, Retry-After header |
| **Cache** | Cache hit -> fast response | -- | Cache miss, invalidation, TTL expiry, stampede |
| **Validation** | Valid payload -> 200 | Invalid -> 422 | Malformed JSON, wrong content-type, oversized payload |
| **CORS** | Allowed origin -> headers | Disallowed origin -> no headers | Preflight OPTIONS, credentials |
| **Compression** | Accept-Encoding: gzip -> compressed | No header -> uncompressed | Large vs small responses |
