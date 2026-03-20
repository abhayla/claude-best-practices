# STEP 10: Infrastructure Monitoring

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
