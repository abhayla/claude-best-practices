# STEP 4: SLO/SLI Definition

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
