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


**Read:** `references/instrumentation-examples.md` for histogram bucket selection and language-specific instrumentation examples (Python, Go, Node.js).

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


---

## STEP 5: Alerting Rules

> **Reference:** See [references/alerting-rules.md](references/alerting-rules.md) for severity levels, alert rule structure, Alertmanager routing, and alert fatigue prevention.

---
## STEP 6: Grafana Dashboards


**Read:** `references/grafana-dashboards.md` for detailed step 6: grafana dashboards reference material.


## STEP 7: Log Aggregation


**Read:** `references/log-aggregation.md` for detailed step 7: log aggregation reference material.

---

## STEP 8: Distributed Tracing

> **Reference:** See [references/tracing-reference.md](references/tracing-reference.md) for OpenTelemetry setup, manual spans, trace context propagation, and sampling strategies.

---

## STEP 9: Application Instrumentation Patterns

> **Reference:** See [references/tracing-reference.md](references/tracing-reference.md) for HTTP middleware metrics, database query timing, cache metrics, and queue/worker metrics.

---
## STEP 10: Infrastructure Monitoring


**Read:** `references/infrastructure-monitoring.md` for detailed step 10: infrastructure monitoring reference material.


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
