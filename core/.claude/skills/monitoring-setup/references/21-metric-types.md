# 2.1 Metric Types

### 2.1 Metric Types

Choose the correct metric type for each measurement:

| Type | Use Case | Example |
|------|----------|---------|
| **Counter** | Monotonically increasing values | `http_requests_total`, `errors_total`, `bytes_sent_total` |
| **Gauge** | Values that go up and down | `active_connections`, `queue_depth`, `temperature_celsius` |
| **Histogram** | Distribution of values (latency, size) | `http_request_duration_seconds`, `response_size_bytes` |
| **Summary** | Pre-calculated quantiles (client-side) | `rpc_duration_seconds` (use histogram instead when possible) |

