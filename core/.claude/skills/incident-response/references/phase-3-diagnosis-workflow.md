# PHASE 3: Diagnosis Workflow

### 3.1 Structured Diagnosis Checklist

Work through these in order — most incidents are caused by recent changes:

| # | Check | Command / Action | Finding |
|---|-------|-----------------|---------|
| 1 | Recent deployments | Check CI/CD pipeline for deploys in the last 4 hours | |
| 2 | Recent config changes | Review config management for changes in the last 24 hours | |
| 3 | Error logs | Search application logs for new error patterns | |
| 4 | Metrics dashboards | Check error rate, latency, CPU, memory, disk, connections | |
| 5 | Dependency status | Verify third-party service status pages and internal dependencies | |
| 6 | Infrastructure | Check cloud provider status, DNS, load balancers, certificates | |
| 7 | Database | Check connection pools, slow queries, replication lag, locks | |
| 8 | Traffic patterns | Look for unusual traffic spikes, DDoS indicators, bot activity | |
| 9 | Cron/scheduled jobs | Check if a scheduled job is running or failed recently | |
| 10 | Feature flags | Review recently toggled feature flags | |

### 3.2 Log Analysis

```bash
