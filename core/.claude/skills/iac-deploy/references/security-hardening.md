# Security Hardening

## Credential Management

NEVER hardcode credentials in IaC files. Use these approaches:

```hcl
# BAD — hardcoded credentials
provider "aws" {
  access_key = "AKIAIOSFODNN7EXAMPLE"   # NEVER
  secret_key = "wJalrXUtnFEMI/K7MDENG"  # NEVER
}

# GOOD — environment-based authentication
provider "aws" {
  region = var.aws_region
  # Credentials from: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY env vars
  # Or: ~/.aws/credentials profile
  # Or: IAM instance role (EC2/ECS)
  # Or: OIDC federation (GitHub Actions)
}
```

```yaml
# GitHub Actions — OIDC federation (no long-lived keys)
- uses: aws-actions/configure-aws-credentials@v4
  with:
    role-to-assume: arn:aws:iam::123456789012:role/github-actions-role
    aws-region: us-east-1
```

```bash
# Pass sensitive values via environment variables
export TF_VAR_db_password="$(aws secretsmanager get-secret-value --secret-id db-password --query SecretString --output text)"
terraform apply
```

## Least Privilege IAM

```hcl
# Create scoped IAM roles for applications
resource "aws_iam_role" "app" {
  name = "${local.name_prefix}-app-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ecs-tasks.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy" "app" {
  name = "${local.name_prefix}-app-policy"
  role = aws_iam_role.app.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["s3:GetObject", "s3:PutObject"]
        Resource = "${aws_s3_bucket.data.arn}/*"
      },
      {
        Effect   = "Allow"
        Action   = ["secretsmanager:GetSecretValue"]
        Resource = aws_secretsmanager_secret.app.arn
      }
    ]
  })
}
```

## Policy as Code

```bash
# OPA / Conftest — validate Terraform plans
terraform plan -out=tfplan
terraform show -json tfplan > tfplan.json
conftest test tfplan.json -p policy/

# Sentinel (Terraform Cloud/Enterprise)
# Policies are defined in .sentinel files and enforced at plan time
```

```rego
# policy/deny_public_s3.rego
package main

deny[msg] {
  resource := input.resource_changes[_]
  resource.type == "aws_s3_bucket"
  resource.change.after.acl == "public-read"
  msg := sprintf("S3 bucket '%s' must not be public", [resource.name])
}

deny[msg] {
  resource := input.resource_changes[_]
  resource.type == "aws_security_group_rule"
  resource.change.after.cidr_blocks[_] == "0.0.0.0/0"
  resource.change.after.from_port == 22
  msg := sprintf("SSH must not be open to the world in '%s'", [resource.name])
}
```

## Security Rules

- NEVER commit credentials, access keys, or secrets to IaC files or tfvars.
- MUST use OIDC federation for CI/CD — no long-lived access keys in GitHub Secrets.
- MUST mark sensitive variables and outputs with `sensitive = true`.
- MUST use scoped IAM policies — no `*` in actions or resources for production.
- MUST run policy-as-code checks (OPA/Conftest/Sentinel) in CI before apply.
- State files contain secrets in plaintext — MUST encrypt the state backend.
