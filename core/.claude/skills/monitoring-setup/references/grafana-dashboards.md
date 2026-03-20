# STEP 6: Grafana Dashboards

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
