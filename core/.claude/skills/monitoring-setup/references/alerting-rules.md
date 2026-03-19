# Alerting Rules Reference

Detailed alerting configuration including severity levels, alert rule structure, Alertmanager routing, and alert fatigue prevention strategies.

---

## Severity Levels

Define clear severity levels with specific response expectations:

| Severity | Response Time | Notification | Action |
|----------|--------------|--------------|--------|
| `critical` | Immediate (< 5 min) | PagerDuty / phone call | Wake someone up, customer impact |
| `warning` | Business hours (< 1 hour) | Slack channel | Needs attention today |
| `info` | Next sprint | Dashboard only | Track trend, no immediate action |

## Alert Rule Structure

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

## Alertmanager Routing

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

## Alert Fatigue Prevention

Rules to avoid desensitizing on-call engineers:

1. **Every alert MUST have a runbook** — No exceptions. A runbook URL is required in annotations.
2. **Every alert MUST be actionable** — If the response is "wait and see," it should be a dashboard, not an alert.
3. **Use `for` duration** — Always require a sustained condition (minimum 2-5 minutes) to avoid flapping.
4. **Group related alerts** — Use `group_by` so one incident produces one notification, not fifty.
5. **Review alerts monthly** — Delete alerts that nobody acted on. Track alert-to-action ratio.
6. **Silence during maintenance** — Create silences in Alertmanager before planned maintenance.
7. **Use inhibition rules** — Suppress downstream alerts when root cause alert fires.
8. **Page only for customer impact** — Internal system degradation without customer impact is a warning, not critical.
