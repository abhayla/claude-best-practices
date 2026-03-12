---
name: monitoring-setup
description: >
  Set up comprehensive monitoring and observability for services. Covers Prometheus metrics,
  Grafana dashboards, alerting rules, SLO/SLI definition, golden signals, log aggregation,
  distributed tracing, application instrumentation, and infrastructure monitoring.
  Use when adding observability to a new or existing service.
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "<service-or-component-to-monitor>"
triggers:
  - /monitoring
  - /observability
  - /grafana
  - /prometheus
---

# Monitoring & Observability Setup

Set up production-grade monitoring and observability for the target service or component.

**Target:** $ARGUMENTS

---

## STEP 1: Assess Current State

1. Identify the service type (API, worker, database, frontend, queue consumer)
2. Check for existing monitoring configuration (prometheus configs, grafana dashboards, alertmanager rules)
3. Identify the tech stack and available instrumentation libraries
4. Determine the deployment environment (Kubernetes, Docker, bare metal, serverless)
5. Check for existing logging and tracing infrastructure

```bash
# Look for existing monitoring configs
find . -name "prometheus*.yml" -o -name "alertmanager*.yml" -o -name "grafana*" -o -name "*dashboard*.json" 2>/dev/null
# Check for instrumentation libraries in dependencies
grep -r "prometheus\|opentelemetry\|datadog\|newrelic\|statsd" package.json requirements.txt go.mod Cargo.toml pom.xml 2>/dev/null
```

---

## STEP 2: Prometheus Metrics

### 2.1 Metric Types

Choose the correct metric type for each measurement:

| Type | Use Case | Example |
|------|----------|---------|
| **Counter** | Monotonically increasing values | `http_requests_total`, `errors_total`, `bytes_sent_total` |
| **Gauge** | Values that go up and down | `active_connections`, `queue_depth`, `temperature_celsius` |
| **Histogram** | Distribution of values (latency, size) | `http_request_duration_seconds`, `response_size_bytes` |
| **Summary** | Pre-calculated quantiles (client-side) | `rpc_duration_seconds` (use histogram instead when possible) |

### 2.2 Naming Conventions

Follow Prometheus naming conventions strictly:

```
# Pattern: <namespace>_<subsystem>_<name>_<unit>

# GOOD
http_requests_total                    # counter — ends with _total
http_request_duration_seconds          # histogram — unit suffix
node_memory_usage_bytes                # gauge — unit suffix
process_cpu_seconds_total              # counter — unit suffix with _total

# BAD
httpRequests                           # no camelCase
http_request_latency                   # missing unit suffix
request_count                          # vague namespace
http_request_duration_milliseconds     # use base units (seconds, bytes, not ms/KB)
```

Rules:
- Use `snake_case` for all metric names
- Counters MUST end with `_total`
- Include the unit as a suffix: `_seconds`, `_bytes`, `_ratio`, `_total`
- Use base units: seconds (not milliseconds), bytes (not kilobytes)
- Prefix with application or subsystem name: `myapp_http_requests_total`

### 2.3 Labels

Labels add dimensions to metrics. Use them carefully:

```yaml
# GOOD — bounded, known cardinality
http_requests_total{method="GET", status="200", handler="/api/users"}
db_query_duration_seconds{operation="select", table="users"}

# BAD — unbounded cardinality (will kill Prometheus)
http_requests_total{user_id="12345"}        # unique per user
http_requests_total{url="/api/users/12345"}  # unique per resource
http_requests_total{request_id="abc-def"}    # unique per request
http_requests_total{timestamp="1234567890"}  # unique per second
```

Cardinality management rules:
- **NEVER** use unbounded values as labels (user IDs, email addresses, request IDs, URLs with path params)
- Keep total cardinality under 10,000 series per metric (labels multiply: 5 methods x 10 handlers x 5 status codes = 250 series)
- Use `le` (less-than-or-equal) buckets for histograms, not arbitrary labels
- Group high-cardinality values into buckets: status codes 200-299 become `2xx`
- Monitor cardinality with `prometheus_tsdb_head_series` and alert when growing unexpectedly

### 2.4 Histogram Bucket Selection

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

### 2.5 Instrumentation Examples

**Python (prometheus_client)**:
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

**Go (prometheus/client_golang)**:
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

**Node.js (prom-client)**:
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

---

## STEP 3: Golden Signals

Instrument every service with the four golden signals:

### 3.1 Latency

Measure how long requests take — separate successful from failed requests:

```promql
# p50 latency
histogram_quantile(0.5, rate(myapp_http_request_duration_seconds_bucket[5m]))

# p99 latency
histogram_quantile(0.99, rate(myapp_http_request_duration_seconds_bucket[5m]))

# p99 latency by handler
histogram_quantile(0.99, sum(rate(myapp_http_request_duration_seconds_bucket[5m])) by (handler, le))

# Latency of failed requests (useful to separate fast 4xx from slow 5xx)
histogram_quantile(0.99, rate(myapp_http_request_duration_seconds_bucket{status=~"5.."}[5m]))
```

### 3.2 Traffic

Measure demand on the system:

```promql
# Requests per second
sum(rate(myapp_http_requests_total[5m]))

# Requests per second by handler
sum(rate(myapp_http_requests_total[5m])) by (handler)

# Requests per second by status class
sum(rate(myapp_http_requests_total[5m])) by (status)
```

### 3.3 Errors

Measure the rate of failed requests:

```promql
# Error rate (5xx)
sum(rate(myapp_http_requests_total{status=~"5.."}[5m]))
  /
sum(rate(myapp_http_requests_total[5m]))

# Error rate by handler
sum(rate(myapp_http_requests_total{status=~"5.."}[5m])) by (handler)
  /
sum(rate(myapp_http_requests_total[5m])) by (handler)
```

### 3.4 Saturation

Measure how full the service is:

```promql
# CPU utilization
rate(process_cpu_seconds_total[5m])

# Memory usage ratio
process_resident_memory_bytes / node_memory_MemTotal_bytes

# Active connections vs limit
myapp_http_active_requests / myapp_http_max_connections

# Queue depth (for worker services)
myapp_queue_depth

# Thread pool utilization
myapp_thread_pool_active / myapp_thread_pool_max
```

---

## STEP 4: SLO/SLI Definition

### 4.1 Service Level Indicators (SLIs)

Define measurable indicators of service health:

```yaml
slis:
  availability:
    description: "Proportion of successful HTTP requests"
    good_events: 'sum(rate(myapp_http_requests_total{status!~"5.."}[5m]))'
    total_events: 'sum(rate(myapp_http_requests_total[5m]))'

  latency:
    description: "Proportion of requests faster than 500ms"
    good_events: 'sum(rate(myapp_http_request_duration_seconds_bucket{le="0.5"}[5m]))'
    total_events: 'sum(rate(myapp_http_requests_total[5m]))'

  correctness:
    description: "Proportion of requests returning correct data"
    good_events: 'sum(rate(myapp_data_validation_success_total[5m]))'
    total_events: 'sum(rate(myapp_data_validation_total[5m]))'
```

### 4.2 Service Level Objectives (SLOs)

Set targets based on business requirements:

```yaml
slos:
  - name: "API Availability"
    sli: availability
    target: 0.999          # 99.9% — 8.77 hours downtime/year
    window: 30d            # rolling 30-day window

  - name: "API Latency"
    sli: latency
    target: 0.99           # 99% of requests under 500ms
    window: 30d

  - name: "Data Correctness"
    sli: correctness
    target: 0.9999         # 99.99%
    window: 30d
```

Common SLO targets and their implications:

| Target | Monthly Downtime | Yearly Downtime | Suitable For |
|--------|-----------------|-----------------|--------------|
| 99% | 7.3 hours | 3.65 days | Internal tools, batch jobs |
| 99.5% | 3.65 hours | 1.83 days | Non-critical services |
| 99.9% | 43.8 minutes | 8.77 hours | Most production services |
| 99.95% | 21.9 minutes | 4.38 hours | Important customer-facing |
| 99.99% | 4.38 minutes | 52.6 minutes | Critical infrastructure |

### 4.3 Error Budget

Calculate and track error budget consumption:

```promql
# Error budget remaining (30-day window, 99.9% SLO)
1 - (
  (1 - (sum(rate(myapp_http_requests_total{status!~"5.."}[30d])) / sum(rate(myapp_http_requests_total[30d]))))
  /
  (1 - 0.999)
)

# Error budget burn rate (how fast budget is being consumed)
# 1.0 = consuming at exactly the sustainable rate
# >1.0 = consuming faster than budget allows
(
  1 - (sum(rate(myapp_http_requests_total{status!~"5.."}[1h])) / sum(rate(myapp_http_requests_total[1h])))
)
/
(1 - 0.999)
```

### 4.4 Burn Rate Alerts

Multi-window burn rate alerts catch both fast and slow burns:

```yaml
# Fast burn — high severity (2% budget in 1 hour)
- alert: SLOBurnRateCritical
  expr: |
    (
      error_ratio_1h / (1 - 0.999) > 14.4
      and
      error_ratio_5m / (1 - 0.999) > 14.4
    )
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "High error budget burn rate — 2% budget consumed in 1 hour"
    runbook_url: "https://runbooks.example.com/slo-burn-rate"

# Slow burn — warning (5% budget in 6 hours)
- alert: SLOBurnRateWarning
  expr: |
    (
      error_ratio_6h / (1 - 0.999) > 6
      and
      error_ratio_30m / (1 - 0.999) > 6
    )
  for: 15m
  labels:
    severity: warning
  annotations:
    summary: "Elevated error budget burn rate — 5% budget consumed in 6 hours"
    runbook_url: "https://runbooks.example.com/slo-burn-rate"
```

---

## STEP 5: Alerting Rules

### 5.1 Severity Levels

Define clear severity levels with specific response expectations:

| Severity | Response Time | Notification | Action |
|----------|--------------|--------------|--------|
| `critical` | Immediate (< 5 min) | PagerDuty / phone call | Wake someone up, customer impact |
| `warning` | Business hours (< 1 hour) | Slack channel | Needs attention today |
| `info` | Next sprint | Dashboard only | Track trend, no immediate action |

### 5.2 Alert Rule Structure

Every alert MUST include these annotations:

```yaml
groups:
  - name: myapp.rules
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate(myapp_http_requests_total{status=~"5.."}[5m]))
          /
          sum(rate(myapp_http_requests_total[5m]))
          > 0.01
        for: 5m                              # Avoid flapping — require sustained condition
        labels:
          severity: critical
          team: backend                      # Routing label
          service: myapp                     # Service ownership
        annotations:
          summary: "Error rate above 1% for {{ $labels.service }}"
          description: "Current error rate: {{ $value | humanizePercentage }}"
          impact: "Users receiving 500 errors on API requests"
          runbook_url: "https://runbooks.example.com/high-error-rate"
          dashboard_url: "https://grafana.example.com/d/myapp-overview"

      - alert: HighLatency
        expr: |
          histogram_quantile(0.99,
            sum(rate(myapp_http_request_duration_seconds_bucket[5m])) by (le)
          ) > 2
        for: 10m
        labels:
          severity: warning
          team: backend
          service: myapp
        annotations:
          summary: "p99 latency above 2s for {{ $labels.service }}"
          description: "Current p99 latency: {{ $value | humanizeDuration }}"
          runbook_url: "https://runbooks.example.com/high-latency"

      - alert: DiskSpaceLow
        expr: |
          (node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) < 0.1
        for: 15m
        labels:
          severity: warning
          team: platform
        annotations:
          summary: "Disk space below 10% on {{ $labels.instance }}"
          runbook_url: "https://runbooks.example.com/disk-space"
```

### 5.3 Alertmanager Routing

```yaml
# alertmanager.yml
route:
  receiver: default-slack
  group_by: ['alertname', 'service']
  group_wait: 30s                          # Wait before sending first notification
  group_interval: 5m                       # Wait between notifications for same group
  repeat_interval: 4h                      # Re-send if still firing
  routes:
    - match:
        severity: critical
      receiver: pagerduty-critical
      continue: true                       # Also send to Slack
    - match:
        severity: critical
      receiver: slack-critical
    - match:
        severity: warning
      receiver: slack-warning
    - match:
        team: backend
      receiver: slack-backend
    - match:
        team: platform
      receiver: slack-platform

receivers:
  - name: pagerduty-critical
    pagerduty_configs:
      - service_key: '<key>'
        severity: '{{ .CommonLabels.severity }}'
  - name: slack-critical
    slack_configs:
      - channel: '#alerts-critical'
        title: '[{{ .Status | toUpper }}] {{ .CommonLabels.alertname }}'
        text: '{{ .CommonAnnotations.summary }}'
  - name: slack-warning
    slack_configs:
      - channel: '#alerts-warning'
  - name: default-slack
    slack_configs:
      - channel: '#alerts-info'

inhibit_rules:
  - source_match:
      severity: critical
    target_match:
      severity: warning
    equal: ['alertname', 'service']        # Suppress warning when critical fires
```

### 5.4 Alert Fatigue Prevention

Rules to avoid desensitizing on-call engineers:

1. **Every alert MUST have a runbook** — No exceptions. A runbook URL is required in annotations.
2. **Every alert MUST be actionable** — If the response is "wait and see," it should be a dashboard, not an alert.
3. **Use `for` duration** — Always require a sustained condition (minimum 2-5 minutes) to avoid flapping.
4. **Group related alerts** — Use `group_by` so one incident produces one notification, not fifty.
5. **Review alerts monthly** — Delete alerts that nobody acted on. Track alert-to-action ratio.
6. **Silence during maintenance** — Create silences in Alertmanager before planned maintenance.
7. **Use inhibition rules** — Suppress downstream alerts when root cause alert fires.
8. **Page only for customer impact** — Internal system degradation without customer impact is a warning, not critical.

---

## STEP 6: Grafana Dashboards

### 6.1 Dashboard Structure

Organize dashboards in a hierarchy:

```
dashboards/
  overview/
    service-map.json              # Top-level service health
  services/
    myapp-overview.json           # Per-service golden signals
    myapp-detailed.json           # Deep-dive with all metrics
  infrastructure/
    nodes.json                    # Server/node metrics
    kubernetes.json               # K8s cluster metrics
  databases/
    postgres.json                 # Database metrics
    redis.json                    # Cache metrics
  business/
    revenue-impact.json           # Business KPIs correlated with tech metrics
```

### 6.2 Panel Types

Use the right visualization for each metric:

| Panel Type | Best For | Example |
|------------|----------|---------|
| **Time series** | Rates, latencies over time | Request rate, p99 latency |
| **Stat** | Single current values | Uptime, error budget remaining |
| **Gauge** | Values with known ranges | CPU %, disk %, SLO compliance |
| **Bar gauge** | Comparing across instances | Per-node memory usage |
| **Table** | Multi-dimension data | Top endpoints by latency |
| **Heatmap** | Distribution over time | Latency distribution |
| **Logs** | Correlated log lines | Errors from Loki/Elasticsearch |
| **Alert list** | Active alerts | Firing alerts for this service |

### 6.3 Template Variables

Use Grafana variables for reusable, filterable dashboards:

```json
{
  "templating": {
    "list": [
      {
        "name": "namespace",
        "type": "query",
        "query": "label_values(myapp_http_requests_total, namespace)",
        "refresh": 2
      },
      {
        "name": "service",
        "type": "query",
        "query": "label_values(myapp_http_requests_total{namespace=\"$namespace\"}, service)",
        "refresh": 2
      },
      {
        "name": "interval",
        "type": "interval",
        "options": [
          {"text": "1m", "value": "1m"},
          {"text": "5m", "value": "5m"},
          {"text": "15m", "value": "15m"}
        ],
        "current": {"text": "5m", "value": "5m"}
      }
    ]
  }
}
```

### 6.4 Dashboard as Code

Provision dashboards automatically using JSON models or Grafonnet:

```yaml
# grafana/provisioning/dashboards/default.yml
apiVersion: 1
providers:
  - name: default
    orgId: 1
    type: file
    disableDeletion: false
    updateIntervalSeconds: 30
    options:
      path: /var/lib/grafana/dashboards
      foldersFromFilesStructure: true
```

Store dashboard JSON in version control. Use `grafana-dashboard-manager` or Terraform for syncing.

### 6.5 Standard Service Dashboard Layout

Every service dashboard MUST include these rows (top to bottom):

```
Row 1: SLO Status
  - SLO compliance (stat panel, green/red)
  - Error budget remaining (gauge)
  - Error budget burn rate (time series)

Row 2: Golden Signals
  - Request rate (time series)
  - Error rate (time series, percentage)
  - p50/p95/p99 latency (time series, multiple queries)
  - Saturation — active connections or CPU (time series)

Row 3: Detailed Metrics
  - Requests by handler (time series, stacked)
  - Errors by handler (table, sorted by error count)
  - Latency heatmap (heatmap)

Row 4: Dependencies
  - Database query latency (time series)
  - Cache hit rate (stat + time series)
  - External API call latency (time series)
  - Queue depth (time series)

Row 5: Infrastructure
  - CPU usage (time series)
  - Memory usage (time series)
  - Disk I/O (time series)
  - Network I/O (time series)

Row 6: Alerts & Logs
  - Active alerts (alert list panel)
  - Recent error logs (logs panel from Loki)
```

---

## STEP 7: Log Aggregation

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

# Request-scoped correlation
request_id_var = contextvars.ContextVar('request_id', default='unknown')

class CorrelationMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        request_id = headers.get('x-request-id', str(uuid.uuid4()))
        request_id_var.set(request_id)
        # ... pass through

class StructuredLogger:
    def log(self, level, message, **kwargs):
        entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "message": message,
            "request_id": request_id_var.get(),
            "trace_id": get_current_trace_id(),
            "service": self.service_name,
            **kwargs
        }
        print(json.dumps(entry))
```

### 7.4 Loki / ELK Integration

**Loki** (recommended for Kubernetes — index-free, label-based):

```yaml
# Promtail config for shipping logs to Loki
scrape_configs:
  - job_name: kubernetes-pods
    kubernetes_sd_configs:
      - role: pod
    relabel_configs:
      - source_labels: [__meta_kubernetes_namespace]
        target_label: namespace
      - source_labels: [__meta_kubernetes_pod_name]
        target_label: pod
      - source_labels: [__meta_kubernetes_pod_label_app]
        target_label: app
    pipeline_stages:
      - json:
          expressions:
            level: level
            trace_id: trace_id
      - labels:
          level:
      - timestamp:
          source: timestamp
          format: RFC3339Nano
```

**LogQL queries** (Grafana Explore):

```logql
# Errors for a specific service
{app="myapp"} |= "error" | json | level="error"

# Trace a request across services
{app=~"myapp|auth-service|payment-service"} | json | request_id="req-001"

# Error rate from logs
sum(rate({app="myapp"} | json | level="error" [5m]))
  /
sum(rate({app="myapp"} [5m]))

# Top error messages
{app="myapp"} | json | level="error" | line_format "{{.message}}" | topk(10, sum by (message) (count_over_time({app="myapp"} | json | level="error" [1h])))
```

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

## STEP 10: Infrastructure Monitoring

### 10.1 Node/Host Metrics

Essential node-exporter metrics to monitor and alert on:

```yaml
alerts:
  # CPU
  - alert: HighCPUUsage
    expr: 100 - (avg by(instance) (rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100) > 85
    for: 15m
    labels:
      severity: warning

  # Memory
  - alert: HighMemoryUsage
    expr: (1 - node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes) > 0.9
    for: 10m
    labels:
      severity: warning

  # Disk space
  - alert: DiskSpaceCritical
    expr: (node_filesystem_avail_bytes{fstype!~"tmpfs|overlay"} / node_filesystem_size_bytes) < 0.05
    for: 5m
    labels:
      severity: critical

  # Disk I/O saturation
  - alert: HighDiskIOUtilization
    expr: rate(node_disk_io_time_seconds_total[5m]) > 0.9
    for: 15m
    labels:
      severity: warning

  # Network errors
  - alert: NetworkErrors
    expr: rate(node_network_receive_errs_total[5m]) + rate(node_network_transmit_errs_total[5m]) > 10
    for: 5m
    labels:
      severity: warning
```

### 10.2 Kubernetes Metrics

```promql
# Pod restart rate (indicates crash loops)
increase(kube_pod_container_status_restarts_total[1h]) > 3

# Pod not ready
kube_pod_status_ready{condition="false"} == 1

# Deployment replica mismatch
kube_deployment_spec_replicas != kube_deployment_status_available_replicas

# Container OOM kills
increase(kube_pod_container_status_last_terminated_reason{reason="OOMKilled"}[1h]) > 0

# HPA at max replicas
kube_horizontalpodautoscaler_status_current_replicas == kube_horizontalpodautoscaler_spec_max_replicas

# PVC nearly full
kubelet_volume_stats_used_bytes / kubelet_volume_stats_capacity_bytes > 0.85

# Node not ready
kube_node_status_condition{condition="Ready", status="true"} == 0
```

### 10.3 Container Metrics

```promql
# Container CPU throttling
rate(container_cpu_cfs_throttled_seconds_total[5m]) > 0.1

# Container memory vs limit
container_memory_working_set_bytes / container_spec_memory_limit_bytes > 0.9

# Container network receive/transmit
rate(container_network_receive_bytes_total[5m])
rate(container_network_transmit_bytes_total[5m])
```

---

## STEP 11: Stack-Specific Dashboard Templates

### 11.1 API Service Dashboard

Key panels for any REST/gRPC API:

```
- Request rate by endpoint (time series, stacked area)
- Error rate by endpoint (time series, percentage)
- p50/p95/p99 latency by endpoint (time series)
- Status code distribution (pie chart or bar)
- Active connections (gauge)
- Request size / response size distribution (heatmap)
- Top 10 slowest endpoints (table, sortable)
- Upstream dependency latency (time series)
```

### 11.2 Database Dashboard

```
- Queries per second by type (SELECT/INSERT/UPDATE/DELETE)
- Query latency p50/p95/p99 (time series)
- Active connections vs pool size (gauge)
- Slow query count (> 1s) (stat + time series)
- Replication lag (time series) — if replicated
- Cache hit ratio (stat) — buffer pool for Postgres, innodb for MySQL
- Table sizes / index sizes (table)
- Lock wait time (time series)
- Dead tuples / vacuum stats (Postgres) (time series)
- WAL generation rate (time series)
```

### 11.3 Queue/Worker Dashboard

```
- Queue depth over time (time series)
- Messages produced/consumed per second (time series)
- Processing latency p50/p95/p99 (time series)
- Consumer lag (time series) — Kafka specific
- Dead letter queue depth (stat, with alert)
- Retry count (time series)
- Worker utilization — busy vs idle (stacked area)
- Message age — oldest unprocessed (stat)
```

### 11.4 Frontend Dashboard

```
- Page load time p50/p75/p95 (time series)
- Core Web Vitals: LCP, FID/INP, CLS (stat panels with thresholds)
- JavaScript error rate (time series)
- API call latency from frontend (time series)
- Asset load time by type (time series)
- Active users / sessions (stat)
- Error rate by browser/device (table)
- CDN hit rate (stat)
```

---

## STEP 12: Anti-Patterns to Avoid

### 12.1 Alerting Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Alert on everything | Alert fatigue — team ignores all alerts | Alert only on customer-facing symptoms, not causes |
| No runbooks | On-call scrambles to diagnose at 3 AM | Every alert links to a runbook with diagnosis steps |
| No `for` duration | Transient spikes trigger pages | Require 2-15 minutes sustained condition |
| Alerting on causes, not symptoms | Generates cascading alerts | Alert on "error rate > 1%" not "pod restarted" |
| Same severity for everything | No prioritization | Use critical/warning/info consistently |
| No alert ownership | "Someone else will handle it" | Every alert has a `team` label for routing |

### 12.2 Metrics Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| High cardinality labels | Prometheus OOM, slow queries | Use bounded label values only; group into buckets |
| Using Summary over Histogram | Cannot aggregate across instances | Use Histogram — aggregatable with `histogram_quantile` |
| Metric names without units | Ambiguous: is it ms or seconds? | Always suffix with `_seconds`, `_bytes`, `_total` |
| Metrics inside hot loops | Performance degradation | Increment counters at operation boundaries, not inner loops |
| Missing `_total` suffix | Breaks Prometheus conventions | Counters MUST end with `_total` |
| Logging metrics instead of exposing | Cannot query, alert, or graph | Expose via `/metrics` endpoint, not log lines |

### 12.3 Logging Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| Unstructured logs | Cannot query or aggregate | Use structured JSON logging everywhere |
| Missing correlation IDs | Cannot trace request across services | Propagate request_id and trace_id in every log |
| Logging PII/secrets | Compliance violation, security risk | Scrub sensitive fields; never log passwords, tokens, SSNs |
| Logging at wrong level | Too noisy or too silent | Follow level guidelines: error/warn/info/debug |
| No log rotation | Disk fills up | Configure max size and retention policies |
| printf debugging in production | Noise, performance impact | Remove debug logs before merge; use `debug` level |

### 12.4 Tracing Anti-Patterns

| Anti-Pattern | Problem | Fix |
|-------------|---------|-----|
| No sampling strategy | Storage costs explode | Use head-based or tail-based sampling |
| Missing context propagation | Broken traces across services | Inject/extract trace context at every boundary |
| Too many spans | Trace viewer unusable, storage costs | Span per operation, not per function call |
| No span attributes | Traces have no useful metadata | Add business-relevant attributes to spans |

---

## Verification Checklist

Before reporting monitoring setup complete, verify:

| Check | Status |
|-------|--------|
| All four golden signals instrumented (latency, traffic, errors, saturation) | |
| Metrics follow naming conventions (`_total`, `_seconds`, `_bytes`) | |
| No high-cardinality labels (user IDs, request IDs in labels) | |
| SLOs defined with error budget tracking | |
| Burn rate alerts configured (fast + slow burn) | |
| Every alert has a runbook URL | |
| Alertmanager routing configured with severity levels | |
| Structured JSON logging with correlation IDs | |
| OpenTelemetry tracing with context propagation | |
| Grafana dashboard with standard layout (SLOs, golden signals, dependencies) | |
| Sampling strategy configured for traces | |
| Infrastructure alerts for disk, CPU, memory | |
| Dashboard committed as code (JSON in version control) | |

---

## CRITICAL RULES

- NEVER use high-cardinality values as metric labels (user IDs, request IDs, email addresses, full URLs)
- NEVER create alerts without a runbook URL — every alert MUST link to diagnosis steps
- NEVER alert without a `for` duration — always require a sustained condition to avoid flapping
- Always use base units in metrics: seconds (not milliseconds), bytes (not kilobytes)
- Always separate successful request latency from failed request latency in SLI calculations
- Counters MUST end with `_total`; include unit suffix on all metrics
- Use Histogram over Summary — histograms are aggregatable across instances
- Expose metrics via `/metrics` endpoint — never rely on log-derived metrics for alerting
- Every service MUST expose the four golden signals regardless of stack
- Dashboard JSON MUST be committed to version control — no manual dashboard creation
