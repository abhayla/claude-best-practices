# STEP 12: Anti-Patterns to Avoid

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

