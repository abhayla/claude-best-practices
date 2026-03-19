# FinOps — Cost Estimation and Optimization

Infrastructure cost management using Infracost, right-sizing, budget alerts, and optimization strategies.

---

## FinOps Overview

### 13.1 Infracost Integration

Estimate infrastructure cost changes per PR before apply.

```bash
# Install infracost
curl -fsSL https://raw.githubusercontent.com/infracost/infracost/master/scripts/install.sh | sh

# Generate cost estimate
infracost breakdown --path=infrastructure/ --format=table

# Compare cost between main and current branch
infracost diff --path=infrastructure/ --compare-to=infracost-base.json --format=table
```

### 13.2 CI/CD Cost Check

```yaml
# .github/workflows/infracost.yml
name: Infracost
on: [pull_request]
jobs:
  infracost:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      - uses: infracost/actions/setup@v3
        with:
          api-key: ${{ secrets.INFRACOST_API_KEY }}
      - run: infracost breakdown --path=infrastructure/ --format=json --out-file=/tmp/infracost.json
      - uses: infracost/actions/comment@v3
        with:
          path: /tmp/infracost.json
          behavior: update
```

### 13.3 Resource Right-Sizing

| Resource | Check | Tool |
|----------|-------|------|
| EC2/GCE instances | CPU/memory utilization < 20% avg | AWS Compute Optimizer, `kubectl top` |
| RDS/CloudSQL | Storage auto-scaling enabled, CPU < 50% | CloudWatch, Performance Insights |
| Lambda functions | Memory over-provisioned, cold starts | AWS Lambda Power Tuning |
| K8s pods | requests >> actual usage | `kubectl top pods`, VPA recommendations |
| S3/GCS | Lifecycle policies for old objects | S3 Analytics, GCS Lifecycle |

```bash
# Kubernetes: compare requested vs actual resource usage
kubectl top pods -n production --sort-by=cpu
kubectl get pods -n production -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[0].resources.requests.cpu}{"\t"}{.spec.containers[0].resources.requests.memory}{"\n"}{end}'
```

### 13.4 Cost Tagging Strategy

```hcl
# Enforce cost allocation tags on all resources
provider "aws" {
  default_tags {
    tags = {
      Environment = var.environment
      Project     = var.project_name
      Team        = var.team_name
      CostCenter  = var.cost_center
      ManagedBy   = "terraform"
    }
  }
}
```

| Tag | Purpose | Example Values |
|-----|---------|---------------|
| `Environment` | Filter cost by env | `dev`, `staging`, `prod` |
| `Project` | Allocate cost to project | `my-app`, `data-pipeline` |
| `Team` | Allocate cost to team | `backend`, `platform`, `ml` |
| `CostCenter` | Finance cost center | `CC-1234` |
| `ManagedBy` | Distinguish IaC vs manual | `terraform`, `pulumi`, `manual` |

### 13.5 Budget Alerts

```hcl
# AWS Budget with alert
resource "aws_budgets_budget" "monthly" {
  name         = "${local.name_prefix}-monthly-budget"
  budget_type  = "COST"
  limit_amount = var.monthly_budget_usd
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  notification {
    comparison_operator       = "GREATER_THAN"
    threshold                 = 80  # Alert at 80% of budget
    threshold_type            = "PERCENTAGE"
    notification_type         = "ACTUAL"
    subscriber_email_addresses = var.budget_alert_emails
  }

  notification {
    comparison_operator       = "GREATER_THAN"
    threshold                 = 100  # Alert at 100% forecasted
    threshold_type            = "PERCENTAGE"
    notification_type         = "FORECASTED"
    subscriber_email_addresses = var.budget_alert_emails
  }
}
```

### 13.6 Cost Optimization Checklist

- [ ] Reserved Instances or Savings Plans for steady-state workloads (30-60% savings)
- [ ] Spot Instances for fault-tolerant batch jobs (60-90% savings)
- [ ] S3 Intelligent-Tiering or lifecycle policies for infrequently accessed data
- [ ] Right-size instances based on actual utilization metrics
- [ ] Delete unused EBS volumes, snapshots, and unattached EIPs
- [ ] Use `NAT Instance` instead of `NAT Gateway` for dev environments ($30/mo vs $1/day)
- [ ] Schedule non-production environments to shut down outside business hours

---
