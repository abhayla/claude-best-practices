# Distributed Tracing & Application Instrumentation Reference

OpenTelemetry setup, manual spans, trace context propagation, sampling strategies, and application-level instrumentation patterns for HTTP, database, cache, and queue metrics.

---

## STEP 8: Distributed Tracing

### 8.1 OpenTelemetry Setup

Use OpenTelemetry as the vendor-neutral instrumentation standard:

```python
# Python — OpenTelemetry auto-instrumentation
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor

# Initialize once at startup
provider = TracerProvider(resource=Resource.create({
    "service.name": "myapp",
    "service.version": "1.2.3",
    "deployment.environment": "production",
}))
provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(
    endpoint="http://otel-collector:4317"
)))
trace.set_tracer_provider(provider)

# Auto-instrument frameworks
FastAPIInstrumentor.instrument()
RequestsInstrumentor.instrument()
SQLAlchemyInstrumentor().instrument(engine=db_engine)
```

### 8.2 Manual Spans

Add custom spans for business-critical operations:

```python
tracer = trace.get_tracer("myapp.payments")

async def process_payment(payment_id: str, amount: float):
    with tracer.start_as_current_span("process_payment") as span:
        span.set_attribute("payment.id", payment_id)
        span.set_attribute("payment.amount", amount)
        span.set_attribute("payment.currency", "USD")

        # Nested span for sub-operation
        with tracer.start_as_current_span("validate_card") as child_span:
            result = await validate_card(payment.card)
            child_span.set_attribute("card.valid", result.valid)
            if not result.valid:
                child_span.set_status(StatusCode.ERROR, "Card validation failed")
                span.record_exception(CardValidationError(result.reason))
                raise CardValidationError(result.reason)

        with tracer.start_as_current_span("charge_gateway"):
            response = await gateway.charge(payment)
            span.set_attribute("payment.status", response.status)
```

### 8.3 Trace Context Propagation

Ensure trace context flows across service boundaries:

```python
# HTTP — automatic with OpenTelemetry instrumentation
# Headers propagated: traceparent, tracestate (W3C Trace Context)

# Message queues — manual propagation required
from opentelemetry.context import get_current
from opentelemetry.propagate import inject, extract

# Producer: inject context into message headers
def publish_message(queue, message):
    headers = {}
    inject(headers)  # Adds traceparent header
    queue.publish(message, headers=headers)

# Consumer: extract context from message headers
def consume_message(message):
    ctx = extract(message.headers)
    with tracer.start_as_current_span("process_message", context=ctx):
        handle(message)
```

### 8.4 Sampling Strategies

Balance trace completeness with storage/performance costs:

```yaml
# Head-based sampling — decide at trace start
sampling:
  # Always sample errors
  - type: status_code
    status: ERROR
    rate: 1.0

  # Sample 10% of normal traffic
  - type: probabilistic
    rate: 0.1

  # Always sample slow requests
  - type: latency
    threshold_ms: 1000
    rate: 1.0

  # Rate-limit to 100 traces/second max
  - type: rate_limiting
    rate: 100

# Tail-based sampling (requires OTel Collector) — decide after trace completes
# More accurate but requires buffering complete traces
processors:
  tail_sampling:
    decision_wait: 10s
    policies:
      - name: errors
        type: status_code
        status_code: {status_codes: [ERROR]}
      - name: slow-traces
        type: latency
        latency: {threshold_ms: 2000}
      - name: probabilistic
        type: probabilistic
        probabilistic: {sampling_percentage: 10}
```

---

## STEP 9: Application Instrumentation Patterns

### 9.1 HTTP Middleware Metrics

Standard metrics every HTTP service MUST expose:

```python
# FastAPI example — complete middleware
from starlette.middleware.base import BaseHTTPMiddleware

class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        method = request.method
        handler = self._get_handler(request)  # Normalize path params

        ACTIVE_REQUESTS.labels(method=method, handler=handler).inc()
        start = time.time()

        try:
            response = await call_next(request)
            status = str(response.status_code)
        except Exception as e:
            status = "500"
            EXCEPTIONS_TOTAL.labels(method=method, handler=handler, exception_type=type(e).__name__).inc()
            raise
        finally:
            duration = time.time() - start
            REQUEST_COUNT.labels(method=method, handler=handler, status=status).inc()
            REQUEST_LATENCY.labels(method=method, handler=handler).observe(duration)
            ACTIVE_REQUESTS.labels(method=method, handler=handler).dec()

        RESPONSE_SIZE.labels(method=method, handler=handler).observe(
            int(response.headers.get('content-length', 0))
        )
        return response

    def _get_handler(self, request):
        # Normalize to route template, NOT actual path
        # /api/users/123 -> /api/users/{id}
        route = request.scope.get("route")
        return route.path if route else request.url.path
```

### 9.2 Database Query Timing

```python
# SQLAlchemy event-based instrumentation
from sqlalchemy import event

DB_QUERY_DURATION = Histogram(
    'myapp_db_query_duration_seconds',
    'Database query execution time',
    ['operation', 'table'],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 5]
)
DB_QUERY_COUNT = Counter('myapp_db_queries_total', 'Total database queries', ['operation', 'table'])
DB_CONNECTION_POOL = Gauge('myapp_db_pool_connections', 'Database connection pool', ['state'])

@event.listens_for(engine, "before_cursor_execute")
def before_query(conn, cursor, statement, parameters, context, executemany):
    conn.info["query_start"] = time.time()

@event.listens_for(engine, "after_cursor_execute")
def after_query(conn, cursor, statement, parameters, context, executemany):
    duration = time.time() - conn.info["query_start"]
    operation = statement.strip().split()[0].upper()  # SELECT, INSERT, UPDATE, DELETE
    DB_QUERY_DURATION.labels(operation=operation, table="unknown").observe(duration)
    DB_QUERY_COUNT.labels(operation=operation, table="unknown").inc()
```

### 9.3 Cache Metrics

```python
CACHE_HITS = Counter('myapp_cache_hits_total', 'Cache hit count', ['cache', 'operation'])
CACHE_MISSES = Counter('myapp_cache_misses_total', 'Cache miss count', ['cache', 'operation'])
CACHE_LATENCY = Histogram('myapp_cache_operation_duration_seconds', 'Cache operation latency',
                          ['cache', 'operation'], buckets=[0.0005, 0.001, 0.005, 0.01, 0.05, 0.1])

class InstrumentedCache:
    def get(self, key):
        start = time.time()
        value = self.client.get(key)
        CACHE_LATENCY.labels(cache="redis", operation="get").observe(time.time() - start)
        if value is not None:
            CACHE_HITS.labels(cache="redis", operation="get").inc()
        else:
            CACHE_MISSES.labels(cache="redis", operation="get").inc()
        return value
```

### 9.4 Queue/Worker Metrics

```python
QUEUE_DEPTH = Gauge('myapp_queue_depth', 'Number of messages in queue', ['queue'])
QUEUE_PROCESSING_DURATION = Histogram('myapp_queue_processing_duration_seconds',
    'Time to process a queue message', ['queue', 'status'])
QUEUE_MESSAGES_TOTAL = Counter('myapp_queue_messages_total',
    'Total messages processed', ['queue', 'status'])

def process_message(message):
    start = time.time()
    try:
        handle(message)
        status = "success"
    except RetryableError:
        status = "retry"
        raise
    except Exception:
        status = "error"
        raise
    finally:
        QUEUE_PROCESSING_DURATION.labels(queue="orders", status=status).observe(time.time() - start)
        QUEUE_MESSAGES_TOTAL.labels(queue="orders", status=status).inc()
```

---