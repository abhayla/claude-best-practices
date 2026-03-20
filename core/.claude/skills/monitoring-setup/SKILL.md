---
name: monitoring-setup
description: >
  Set up comprehensive monitoring and observability for services. Covers Prometheus metrics,
  Grafana dashboards, alerting rules, SLO/SLI definition, golden signals, log aggregation,
  distributed tracing, application instrumentation, and infrastructure monitoring.
  Use when adding observability to a new or existing service.
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "<service-or-component-to-monitor>"
version: "1.0.1"
type: workflow
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


**Read:** `references/slosli-definition.md` for detailed step 4: slo/sli definition reference material.

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

> **Reference:** See [references/alerting-rules.md](references/alerting-rules.md) for severity levels, alert rule structure, Alertmanager routing, and alert fatigue prevention.

---
## STEP 6: Grafana Dashboards


**Read:** `references/grafana-dashboards.md` for detailed step 6: grafana dashboards reference material.

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

## STEP 7: Log Aggregation


**Read:** `references/log-aggregation.md` for detailed step 7: log aggregation reference material.

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

> **Reference:** See [references/tracing-reference.md](references/tracing-reference.md) for OpenTelemetry setup, manual spans, trace context propagation, and sampling strategies.

---

## STEP 9: Application Instrumentation Patterns

> **Reference:** See [references/tracing-reference.md](references/tracing-reference.md) for HTTP middleware metrics, database query timing, cache metrics, and queue/worker metrics.

---
## STEP 10: Infrastructure Monitoring


**Read:** `references/infrastructure-monitoring.md` for detailed step 10: infrastructure monitoring reference material.

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

> **Reference:** See [references/dashboard-templates.md](references/dashboard-templates.md) for API, database, queue/worker, and frontend dashboard panel layouts.

---
## STEP 12: Anti-Patterns to Avoid


**Read:** `references/anti-patterns-to-avoid.md` for detailed step 12: anti-patterns to avoid reference material.

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
