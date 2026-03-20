# Instrumentation Examples

## Histogram Bucket Selection

Choose buckets based on your SLO targets and expected distribution:

```yaml
# API latency — typical web service
buckets: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]

# Background job duration — longer operations
buckets: [0.1, 0.5, 1, 5, 10, 30, 60, 120, 300, 600]

# Response size in bytes
buckets: [100, 1000, 10000, 100000, 1000000, 10000000]

# Database query latency — fast operations
buckets: [0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 5]
```

Always include a bucket near your SLO threshold (e.g., if SLO is p99 < 500ms, include a 0.5 bucket).

## Python (prometheus_client)

```python
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Define metrics at module level — never inside functions
REQUEST_COUNT = Counter(
    'myapp_http_requests_total',
    'Total HTTP requests',
    ['method', 'handler', 'status']
)
REQUEST_LATENCY = Histogram(
    'myapp_http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'handler'],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10]
)
ACTIVE_REQUESTS = Gauge(
    'myapp_http_active_requests',
    'Currently active HTTP requests'
)

# Middleware example
def metrics_middleware(request, call_next):
    ACTIVE_REQUESTS.inc()
    method = request.method
    handler = request.url.path
    start = time.time()
    try:
        response = call_next(request)
        REQUEST_COUNT.labels(method=method, handler=handler, status=response.status_code).inc()
        return response
    finally:
        REQUEST_LATENCY.labels(method=method, handler=handler).observe(time.time() - start)
        ACTIVE_REQUESTS.dec()
```

## Go (prometheus/client_golang)

```go
var (
    requestCount = promauto.NewCounterVec(prometheus.CounterOpts{
        Name: "myapp_http_requests_total",
        Help: "Total HTTP requests",
    }, []string{"method", "handler", "status"})

    requestLatency = promauto.NewHistogramVec(prometheus.HistogramOpts{
        Name:    "myapp_http_request_duration_seconds",
        Help:    "HTTP request latency",
        Buckets: prometheus.DefBuckets,
    }, []string{"method", "handler"})
)
```

## Node.js (prom-client)

```javascript
const client = require('prom-client');

const requestCount = new client.Counter({
    name: 'myapp_http_requests_total',
    help: 'Total HTTP requests',
    labelNames: ['method', 'handler', 'status'],
});

const requestLatency = new client.Histogram({
    name: 'myapp_http_request_duration_seconds',
    help: 'HTTP request latency',
    labelNames: ['method', 'handler'],
    buckets: [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
});
```
