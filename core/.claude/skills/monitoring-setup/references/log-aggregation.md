# STEP 7: Log Aggregation

### 7.1 Structured Logging

All logs MUST be structured JSON — never unstructured text:

```json
{
  "timestamp": "2025-01-15T10:30:45.123Z",
  "level": "error",
  "message": "Failed to process payment",
  "service": "payment-service",
  "trace_id": "abc123def456",
  "span_id": "789ghi",
  "request_id": "req-001",
  "user_id": "user-42",
  "error": {
    "type": "PaymentGatewayError",
    "message": "Connection timeout",
    "stack": "..."
  },
  "context": {
    "payment_id": "pay-123",
    "amount": 99.99,
    "currency": "USD"
  }
}
```

### 7.2 Log Levels

Use log levels consistently across all services:

| Level | When to Use | Example |
|-------|-------------|---------|
| `error` | Something failed, requires investigation | Payment processing failed, database connection lost |
| `warn` | Degraded but functional, or unexpected input | Retry succeeded, deprecated API called, rate limit approaching |
| `info` | Normal significant events | Request completed, job finished, config loaded |
| `debug` | Diagnostic detail for troubleshooting | SQL queries, cache lookups, request/response bodies |

Rules:
- Production MUST run at `info` level minimum
- `debug` logs MUST NOT contain PII or secrets
- Log at the boundary — entry and exit of significant operations, not every internal step
- Include duration for all operations: `"duration_ms": 145`

### 7.3 Correlation IDs

Propagate trace context through every log entry:

```python
import uuid
import contextvars

