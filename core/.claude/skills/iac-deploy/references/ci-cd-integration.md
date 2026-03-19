# CI/CD Integration for Infrastructure as Code

## Plan on Pull Request

```yaml
# .github/workflows/terraform-plan.yml
name: Terraform Plan
on:
  pull_request:
    paths:
      - 'infrastructure/**'
jobs:
  plan:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
      pull-requests: write
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: 1.7.0

      - name: Terraform Init
        run: terraform init
        working-directory: infrastructure/

      - name: Terraform Validate
        run: terraform validate
        working-directory: infrastructure/

      - name: Terraform Plan
        id: plan
        run: terraform plan -var-file=environments/${{ github.base_ref }}.tfvars -no-color -out=tfplan
        working-directory: infrastructure/
        continue-on-error: true

      - name: Comment Plan on PR
        uses: actions/github-script@v7
        with:
          script: |
            const plan = `${{ steps.plan.outputs.stdout }}`;
            const truncated = plan.length > 60000 ? plan.substring(0, 60000) + '\n\n... truncated' : plan;
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `#### Terraform Plan\n\`\`\`\n${truncated}\n\`\`\``
            });
```

## Apply on Merge

```yaml
# .github/workflows/terraform-apply.yml
name: Terraform Apply
on:
  push:
    branches: [main]
    paths:
      - 'infrastructure/**'
jobs:
  apply:
    runs-on: ubuntu-latest
    environment: production  # Requires manual approval
    permissions:
      id-token: write
      contents: read
    steps:
      - uses: actions/checkout@v4
      - uses: hashicorp/setup-terraform@v3
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: us-east-1

      - run: terraform init
        working-directory: infrastructure/

      - run: terraform apply -auto-approve -var-file=environments/prod.tfvars
        working-directory: infrastructure/
```

## Approval Gates

| Gate | Implementation |
|------|---------------|
| Plan review | PR comment with plan output |
| Manual approval | GitHub environment protection rules |
| Policy check | OPA/Conftest step before apply |
| Cost estimate | Infracost integration |
| Security scan | tfsec or checkov step |

## Pipeline State Locking

```yaml
# Use concurrency to prevent parallel applies
concurrency:
  group: terraform-${{ github.ref }}
  cancel-in-progress: false  # Don't cancel running applies
```

## CI/CD Rules

- MUST run `terraform plan` on every PR that touches infrastructure code.
- MUST post plan output as a PR comment for human review.
- MUST use GitHub environment protection rules for production applies.
- MUST use `concurrency` groups to prevent parallel applies to the same environment.
- NEVER use `-auto-approve` without environment protection gates.
- MUST run `terraform validate` and `terraform fmt -check` in CI.
