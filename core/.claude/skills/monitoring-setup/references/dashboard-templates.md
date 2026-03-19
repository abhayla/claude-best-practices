# Stack-Specific Dashboard Templates

Panel layout recommendations for common service types: API services, databases, queue/worker systems, and frontend applications.

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