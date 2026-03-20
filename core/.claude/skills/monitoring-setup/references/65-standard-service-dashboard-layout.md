# 6.5 Standard Service Dashboard Layout

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

