# STEP 8: Health Endpoint

## STEP 8: Health Endpoint

Create a health check endpoint per stack:

**Python (FastAPI):**
```python
@app.get("/health")
async def health():
    return {"status": "healthy", "version": settings.VERSION}
```

**Node (Express/Next.js API):**
```typescript
app.get('/health', (req, res) => {
  res.json({ status: 'healthy', version: process.env.npm_package_version });
});
```

**Go:**
```go
http.HandleFunc("/health", func(w http.ResponseWriter, r *http.Request) {
    json.NewEncoder(w).Encode(map[string]string{"status": "healthy"})
})
```

**Android (Kotlin — for apps with an embedded HTTP server or health check Activity):**
```kotlin
// If using Ktor embedded server or similar:
get("/health") {
    call.respond(mapOf("status" to "healthy", "version" to BuildConfig.VERSION_NAME))
}

// If no HTTP server, create a health-check mechanism via a ContentProvider or WorkManager diagnostic:
class HealthCheckProvider : ContentProvider() {
    override fun call(method: String, arg: String?, extras: Bundle?): Bundle {
        return Bundle().apply { putString("status", "healthy") }
    }
    // ... other required overrides return null/false/0
}
```

**Rust (Actix Web):**
```rust
#[get("/health")]
async fn health() -> impl Responder {
    HttpResponse::Ok().json(serde_json::json!({
        "status": "healthy",
        "version": env!("CARGO_PKG_VERSION")
    }))
}
```

The health endpoint MUST:
- Return HTTP 200 when the service is ready
- Include version information
- NOT require authentication
- Be excluded from request logging (to avoid log noise)

---

