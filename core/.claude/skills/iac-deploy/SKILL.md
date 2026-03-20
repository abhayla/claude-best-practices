---
name: iac-deploy
description: >
  Infrastructure as Code deployment skill covering Terraform and Pulumi.
  Handles provider configuration, resource management, state backends,
  module composition, environment management, drift detection, security
  hardening, CI/CD integration, common cloud resource patterns, FinOps
  (cost estimation with Infracost, right-sizing, budget alerts), serverless
  deployment (Lambda/Cloud Functions), and static site deployment
  (Vercel/Netlify/Cloudflare Pages/Firebase Hosting).
  Use for any IaC planning, writing, reviewing, or troubleshooting.
allowed-tools: "Bash Read Write Edit Grep Glob"
triggers: "iac, terraform, pulumi, infrastructure, infrastructure as code, tf plan, tf apply, cloud provisioning"
argument-hint: "<'plan' or 'write <resource>' or 'review' or 'migrate-state' or 'modularize' or 'drift-check'>"
version: "1.0.1"
type: workflow
---

# Infrastructure as Code — Terraform & Pulumi

Deploy and manage cloud infrastructure using declarative IaC tools.

**Request:** $ARGUMENTS

---

## STEP 1: Assess the Infrastructure Context

Before writing any IaC, understand what already exists.

### 1.1 Discover Existing Configuration

```bash
# Terraform files
find . -name "*.tf" -o -name "*.tfvars" -o -name "*.tfstate" | head -40

# Pulumi files
find . -name "Pulumi.yaml" -o -name "Pulumi.*.yaml" -o -name "__main__.py" -o -name "index.ts" | head -40

# Check for lock files
find . -name ".terraform.lock.hcl" -o -name "package-lock.json" -o -name "requirements.txt" | head -20
```

### 1.2 Identify the IaC Tool

| Signal | Tool |
|--------|------|
| `*.tf` files, `.terraform/` directory | Terraform (HCL) |
| `Pulumi.yaml`, language-specific source files | Pulumi |
| Both present | Hybrid — clarify scope with user |
| Neither present | Greenfield — recommend based on team skills |

### 1.3 Check Provider/Cloud Target

```bash
# Terraform — extract providers
grep -r 'provider "' *.tf 2>/dev/null || echo "No Terraform providers found"
grep -r 'required_providers' *.tf 2>/dev/null

# Pulumi — check dependencies
cat Pulumi.yaml 2>/dev/null
cat requirements.txt 2>/dev/null | grep pulumi
cat package.json 2>/dev/null | grep pulumi
```

---

## STEP 2: Terraform Fundamentals

### 2.1 Provider Configuration

Every Terraform project starts with provider blocks. Pin versions to avoid breaking changes.

```hcl
# versions.tf — always separate from main config
terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }
}

# provider.tf — provider-specific configuration
provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Environment = var.environment
      ManagedBy   = "terraform"
      Project     = var.project_name
    }
  }
}
```

**Key rules:**
- MUST pin provider versions with `~>` (pessimistic constraint) to allow patch updates only.
- MUST set `required_version` for Terraform itself.
- MUST use `default_tags` (AWS) or equivalent to tag all resources consistently.
- NEVER hardcode regions or account IDs — use variables.

### 2.3 Data Sources

Data sources read existing infrastructure without managing it.

```hcl
# Look up existing VPC
data "aws_vpc" "main" {
  filter {
    name   = "tag:Name"
    values = ["${var.project_name}-vpc"]
  }
}

# Look up latest AMI
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

# Reference: data.aws_vpc.main.id, data.aws_ami.ubuntu.id
```

**When to use data sources vs. resources:**
- Data source: infrastructure exists and is managed elsewhere (or manually).
- Resource: you want Terraform to create and manage it.
- NEVER use data sources to reference resources in the same configuration — use direct references instead.

### 2.4 Variables, Outputs, and Locals

```hcl
# variables.tf
variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
}

# locals.tf
locals {
  name_prefix = "${var.project_name}-${var.environment}"
  common_tags = {
    Environment = var.environment
    Project     = var.project_name
  }

  # Computed values
  is_production = var.environment == "prod"
  instance_type = local.is_production ? "t3.large" : "t3.micro"
}

# outputs.tf
output "vpc_id" {
  description = "ID of the created VPC"
  value       = aws_vpc.main.id
}

output "db_endpoint" {
  description = "Database connection endpoint"
  value       = aws_db_instance.main.endpoint
  sensitive   = true
}
```

**Key rules:**
- MUST add `description` to every variable and output.
- MUST mark credentials and endpoints as `sensitive = true`.
- MUST use `validation` blocks for variables with constrained values.
- Use `locals` for computed values, DRY naming, and conditional logic — not variables.
- NEVER set defaults for sensitive variables — force explicit input.

---

## STEP 3: Pulumi Fundamentals

# Pulumi.yaml
name: my-infra
runtime: python  # or nodejs, go, dotnet
description: Core infrastructure for my-project
```

### 3.2 Stack Configuration

```bash
# Create stacks
pulumi stack init dev
pulumi stack init staging
pulumi stack init prod

# Set config values
pulumi config set aws:region us-east-1
pulumi config set instanceType t3.micro
pulumi config set --secret dbPassword 'supersecret'

# Stack-specific config
pulumi stack select prod
pulumi config set instanceType t3.large
```

# Common tags applied to all resources
common_tags = {
    "Environment": environment,
    "ManagedBy": "pulumi",
    "Project": project_name,
}

# S3 bucket
data_bucket = aws.s3.Bucket(
    "data-lake",
    bucket=f"{project_name}-{environment}-data-lake",
    versioning=aws.s3.BucketVersioningArgs(enabled=True),
    server_side_encryption_configuration=aws.s3.BucketServerSideEncryptionConfigurationArgs(
        rule=aws.s3.BucketServerSideEncryptionConfigurationRuleArgs(
            apply_server_side_encryption_by_default=aws.s3.BucketServerSideEncryptionConfigurationRuleApplyServerSideEncryptionByDefaultArgs(
                sse_algorithm="aws:kms",
            ),
        ),
    ),
    tags={**common_tags, "Purpose": "Data lake storage"},
)

pulumi.export("bucket_name", data_bucket.bucket)
pulumi.export("bucket_arn", data_bucket.arn)
```

## STEP 4: State Management

### 4.1 Remote Backends — Terraform

NEVER use local state for shared infrastructure. Configure a remote backend immediately.

```hcl
# backend.tf — S3 backend (AWS)
terraform {
  backend "s3" {
    bucket         = "mycompany-terraform-state"
    key            = "projects/my-project/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "terraform-state-lock"
    encrypt        = true
  }
}
```

```hcl
# backend.tf — GCS backend (GCP)
terraform {
  backend "gcs" {
    bucket = "mycompany-terraform-state"
    prefix = "projects/my-project"
  }
}
```

```hcl
# backend.tf — Azure Blob backend
terraform {
  backend "azurerm" {
    resource_group_name  = "terraform-state-rg"
    storage_account_name = "mycompanytfstate"
    container_name       = "tfstate"
    key                  = "projects/my-project/terraform.tfstate"
  }
}
```

### 4.2 Remote Backends — Pulumi

Pulumi uses backends for state storage. Options:

```bash
# Pulumi Cloud (default, managed)
pulumi login

# S3-compatible backend
pulumi login s3://mycompany-pulumi-state

# Local filesystem (development only)
pulumi login --local
```

# DynamoDB lock table for Terraform S3 backend
resource "aws_dynamodb_table" "terraform_lock" {
  name         = "terraform-state-lock"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "LockID"

  attribute {
    name = "LockID"
    type = "S"
  }
}
```

### 4.4 State Migration

```bash
# Terraform — migrate from local to S3
# 1. Add backend config to backend.tf
# 2. Run init with migration flag
terraform init -migrate-state

# Force unlock if state is stuck (use with extreme caution)
terraform force-unlock <LOCK_ID>
```

### 4.5 Import Existing Resources

```hcl
# Terraform 1.5+ — import blocks (preferred, declarative)
import {
  to = aws_s3_bucket.existing_bucket
  id = "my-existing-bucket-name"
}

resource "aws_s3_bucket" "existing_bucket" {
  bucket = "my-existing-bucket-name"
}
```

```bash
# Terraform — CLI import (older approach)
terraform import aws_s3_bucket.existing_bucket my-existing-bucket-name

# Pulumi — import
pulumi import aws:s3/bucket:Bucket existing-bucket my-existing-bucket-name
```

**State management rules:**
- MUST use remote state with locking for any shared or production infrastructure.
- MUST enable encryption on the state backend (state contains secrets in plaintext).
- NEVER manually edit state files — use `terraform state mv`, `terraform state rm`, or `pulumi state delete`.
- MUST back up state before any migration or import operation.
- Use separate state files per environment (separate backends or key paths).

---

## STEP 5: Module Composition


**Read:** `references/module-composition.md` for detailed step 5: module composition reference material.

# modules/vpc/variables.tf — inputs
variable "cidr_block" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition     = can(cidrhost(var.cidr_block, 0))
    error_message = "Must be a valid CIDR block."
  }
}

variable "availability_zones" {
  description = "List of AZs for subnet distribution"
  type        = list(string)
}

variable "enable_nat_gateway" {
  description = "Whether to provision NAT gateways for private subnets"
  type        = bool
  default     = true
}

# modules/vpc/outputs.tf — outputs
output "vpc_id" {
  description = "The ID of the VPC"
  value       = aws_vpc.main.id
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = aws_subnet.public[*].id
}
```

### 5.3 Calling Modules

```hcl
# Root module — main.tf
module "vpc" {
  source = "./modules/vpc"

  cidr_block         = "10.0.0.0/16"
  availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]
  enable_nat_gateway = var.environment == "prod"
}

module "database" {
  source = "./modules/database"

  vpc_id             = module.vpc.vpc_id
  subnet_ids         = module.vpc.private_subnet_ids
  instance_class     = var.environment == "prod" ? "db.r6g.large" : "db.t3.micro"
  master_password    = var.db_password
}
```

### 5.4 Module Versioning

```hcl
# From Terraform Registry
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"
}

# From Git with tag
module "vpc" {
  source = "git::https://github.com/myorg/terraform-modules.git//vpc?ref=v2.1.0"
}
```

**Module rules:**
- MUST version-pin all external module sources.
- MUST define clear input/output contracts with descriptions and validations.
- NEVER put provider blocks inside modules — providers are passed from root.
- Modules MUST be stateless — no backend configuration inside modules.
- Keep modules focused: one logical concern per module (networking, compute, database).

---

## STEP 6: Environment Management

### 6.1 Terraform Workspaces

```bash
# Create workspaces
terraform workspace new dev
terraform workspace new staging
terraform workspace new prod

# Switch workspace
terraform workspace select prod

# List workspaces
terraform workspace list
```

```hcl
# Reference workspace in config
locals {
  environment = terraform.workspace
  is_prod     = terraform.workspace == "prod"
}
```

**Workspace limitations:** Workspaces share the same backend config and code. For significantly different environments, use separate directories or Terragrunt instead.

# environments/prod.tfvars
environment    = "prod"
instance_type  = "t3.large"
instance_count = 3
enable_waf     = true
db_multi_az    = true
```

```bash
# Apply with environment-specific vars
terraform plan -var-file=environments/prod.tfvars
terraform apply -var-file=environments/prod.tfvars
```

### 6.3 Pulumi Stacks (Environment Management)

```bash
# Each stack is a separate environment
pulumi stack select dev
pulumi up

pulumi stack select prod
pulumi up
```

```python
# Stack-aware configuration in Pulumi
import pulumi

stack = pulumi.get_stack()
config = pulumi.Config()

# Stack-specific defaults
instance_type = config.get("instanceType") or ("t3.large" if stack == "prod" else "t3.micro")
replicas = config.get_int("replicas") or (3 if stack == "prod" else 1)
```

## STEP 7: Drift Detection

### 7.1 Plan/Preview Before Apply

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

### 7.2 Detecting Manual Changes

```bash
# Terraform — detect drift
terraform plan -detailed-exitcode -var-file=environments/prod.tfvars
# Exit code 0 = no changes, 1 = error, 2 = changes detected

# Terraform — refresh state from actual infrastructure
terraform refresh -var-file=environments/prod.tfvars
# Or combined with plan:
terraform plan -refresh-only -var-file=environments/prod.tfvars
```

### 7.3 Reconciliation Strategies

| Scenario | Action |
|----------|--------|
| Manual change aligns with desired state | Update config to match, run `plan` to confirm no diff |
| Manual change is unwanted | Run `apply` to revert infrastructure to declared state |
| Resource was deleted outside IaC | Remove from state with `terraform state rm`, or re-import |
| Resource was created outside IaC | Import into state, add resource block |

### 7.4 Scheduled Drift Detection

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

---

## STEP 8: Security

### 8.1 Credential Management

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

# Pass sensitive values via environment variables
export TF_VAR_db_password="$(aws secretsmanager get-secret-value --secret-id db-password --query SecretString --output text)"
terraform apply
```

### 8.3 Least Privilege IAM

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

### 8.4 Policy as Code

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

**Security rules:**
- NEVER commit credentials, access keys, or secrets to IaC files or tfvars.
- MUST use OIDC federation for CI/CD — no long-lived access keys in GitHub Secrets.
- MUST mark sensitive variables and outputs with `sensitive = true`.
- MUST use scoped IAM policies — no `*` in actions or resources for production.
- MUST run policy-as-code checks (OPA/Conftest/Sentinel) in CI before apply.
- State files contain secrets in plaintext — MUST encrypt the state backend.

---

## STEP 9: CI/CD Integration

> **Reference:** See [references/ci-cd-integration.md](references/ci-cd-integration.md) for GitHub Actions workflow templates (plan on PR, apply on merge), approval gates, pipeline state locking, and CI/CD rules.

---

## STEP 10: Common Resource Patterns, Refactoring, and Anti-Patterns

> **Reference:** See [references/resource-patterns.md](references/resource-patterns.md) for VPC/networking, compute, database, storage, DNS/CDN patterns, refactoring strategies (moved blocks, imports, state operations), and anti-patterns to avoid.

## STEP 11: FinOps — Cost Estimation & Optimization

> **Reference:** See [references/finops.md](references/finops.md) for Infracost integration, CI/CD cost checks, resource right-sizing, cost tagging strategy, budget alerts, and optimization checklist.

## STEP 12: Serverless & Static Site Deployment

> **Reference:** See [references/serverless-static.md](references/serverless-static.md) for Lambda/Cloud Functions, static site deployment (Vercel/Netlify/Cloudflare Pages/Firebase), SSR deployment, preview deployments, and Terraform/Pulumi command cheat sheets.

---

## CRITICAL RULES

- ALWAYS plan/preview before apply — never apply blindly
- ALWAYS use remote state with locking and encryption for shared infrastructure
- NEVER hardcode credentials, regions, account IDs, or resource identifiers
- NEVER apply and refactor state in the same operation
- ALWAYS pin provider and module versions
- ALWAYS tag resources with environment, project, and managed-by
- ALWAYS use separate state per environment
- ALWAYS review destroy/replace actions in plan output before applying
- Mark all sensitive variables and outputs as `sensitive = true`
- Use OIDC federation in CI/CD — no long-lived access keys
- ALWAYS run `infracost diff` on PRs that change infrastructure — cost surprises are deployment blockers
- ALWAYS tag all resources with Environment, Project, Team, and CostCenter
- ALWAYS configure budget alerts before provisioning production infrastructure
- ALWAYS use preview deployments for static sites — every PR gets a reviewable URL
- MUST NOT provision production infrastructure without a monthly cost estimate
- MUST NOT use NAT Gateway in dev environments — use NAT Instance or VPC endpoints instead
