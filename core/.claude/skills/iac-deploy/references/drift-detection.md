# Drift Detection

## Plan/Preview Before Apply

NEVER run `terraform apply` or `pulumi up` without reviewing the plan first.

```bash
# Terraform — always plan first
terraform plan -var-file=environments/prod.tfvars -out=tfplan
# Review the plan output carefully
terraform apply tfplan

# Pulumi — preview first
pulumi preview
# Review the preview output
pulumi up
```

## Detecting Manual Changes

```bash
# Terraform — detect drift
terraform plan -detailed-exitcode -var-file=environments/prod.tfvars
# Exit code 0 = no changes, 1 = error, 2 = changes detected

# Terraform — refresh state from actual infrastructure
terraform refresh -var-file=environments/prod.tfvars
# Or combined with plan:
terraform plan -refresh-only -var-file=environments/prod.tfvars
```

## Reconciliation Strategies

| Scenario | Action |
|----------|--------|
| Manual change aligns with desired state | Update config to match, run `plan` to confirm no diff |
| Manual change is unwanted | Run `apply` to revert infrastructure to declared state |
| Resource was deleted outside IaC | Remove from state with `terraform state rm`, or re-import |
| Resource was created outside IaC | Import into state, add resource block |

## Scheduled Drift Detection

```yaml
# GitHub Actions — weekly drift check
name: Drift Detection
on:
  schedule:
    - cron: '0 8 * * 1'  # Monday 8 AM
jobs:
  detect-drift:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
      - run: terraform init
      - run: terraform plan -detailed-exitcode -var-file=environments/prod.tfvars
        id: plan
        continue-on-error: true
      - name: Notify on drift
        if: steps.plan.outputs.exitcode == 2
        run: echo "::warning::Infrastructure drift detected!"
```
