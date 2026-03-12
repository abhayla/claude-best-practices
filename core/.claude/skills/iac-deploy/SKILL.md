---
name: iac-deploy
description: >
  Infrastructure as Code deployment skill covering Terraform and Pulumi.
  Handles provider configuration, resource management, state backends,
  module composition, environment management, drift detection, security
  hardening, CI/CD integration, and common cloud resource patterns.
  Use for any IaC planning, writing, reviewing, or troubleshooting.
allowed-tools: "Bash Read Write Edit Grep Glob"
triggers: "iac, terraform, pulumi, infrastructure, infrastructure as code, tf plan, tf apply, cloud provisioning"
argument-hint: "<'plan' or 'write <resource>' or 'review' or 'migrate-state' or 'modularize' or 'drift-check'>"
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

### 2.2 Resource Blocks

```hcl
resource "aws_s3_bucket" "data_lake" {
  bucket = "${var.project_name}-${var.environment}-data-lake"

  tags = {
    Purpose = "Data lake storage"
  }
}

resource "aws_s3_bucket_versioning" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "aws:kms"
    }
  }
}
```

**Key rules:**
- Use separate resource blocks for bucket sub-resources (versioning, encryption, lifecycle) — inline configuration is deprecated for many resources.
- Reference other resources via `resource_type.name.attribute`, never by hardcoded IDs.
- Use `${var.project}-${var.env}-<purpose>` naming convention for uniqueness.

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

### 3.1 Project Structure

```
my-infra/
  Pulumi.yaml           # Project metadata
  Pulumi.dev.yaml       # Dev stack config
  Pulumi.staging.yaml   # Staging stack config
  Pulumi.prod.yaml      # Prod stack config
  __main__.py           # Python entry point (or index.ts for TypeScript)
  requirements.txt      # Python deps (or package.json for TypeScript)
```

```yaml
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

### 3.3 Resource Creation — Python

```python
import pulumi
import pulumi_aws as aws

config = pulumi.Config()
environment = pulumi.get_stack()
project_name = pulumi.get_project()

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

### 3.4 Resource Creation — TypeScript

```typescript
import * as pulumi from "@pulumi/pulumi";
import * as aws from "@pulumi/aws";

const config = new pulumi.Config();
const environment = pulumi.getStack();
const projectName = pulumi.getProject();

const commonTags = {
    Environment: environment,
    ManagedBy: "pulumi",
    Project: projectName,
};

const dataBucket = new aws.s3.Bucket("data-lake", {
    bucket: `${projectName}-${environment}-data-lake`,
    versioning: { enabled: true },
    serverSideEncryptionConfiguration: {
        rule: {
            applyServerSideEncryptionByDefault: {
                sseAlgorithm: "aws:kms",
            },
        },
    },
    tags: { ...commonTags, Purpose: "Data lake storage" },
});

export const bucketName = dataBucket.bucket;
export const bucketArn = dataBucket.arn;
```

### 3.5 Resource Creation — Go

```go
package main

import (
    "fmt"
    "github.com/pulumi/pulumi-aws/sdk/v6/go/aws/s3"
    "github.com/pulumi/pulumi/sdk/v3/go/pulumi"
    "github.com/pulumi/pulumi/sdk/v3/go/pulumi/config"
)

func main() {
    pulumi.Run(func(ctx *pulumi.Context) error {
        env := ctx.Stack()
        project := ctx.Project()
        cfg := config.New(ctx, "")

        bucket, err := s3.NewBucket(ctx, "data-lake", &s3.BucketArgs{
            Bucket: pulumi.Sprintf("%s-%s-data-lake", project, env),
            Tags: pulumi.StringMap{
                "Environment": pulumi.String(env),
                "ManagedBy":   pulumi.String("pulumi"),
            },
        })
        if err != nil {
            return err
        }

        ctx.Export("bucketName", bucket.Bucket)
        return nil
    })
}
```

**Pulumi key rules:**
- MUST use `pulumi.get_stack()` / `getStack()` for environment differentiation — never hardcode.
- MUST use `pulumi config set --secret` for any sensitive values.
- MUST export critical resource attributes (IDs, ARNs, endpoints) for cross-stack references.
- Use component resources (classes extending `pulumi.ComponentResource`) for reusable abstractions.

---

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

### 4.3 State Locking

State locking prevents concurrent modifications that corrupt state.

| Tool | Lock Mechanism | Setup |
|------|----------------|-------|
| Terraform + S3 | DynamoDB table | Create table with `LockID` partition key |
| Terraform + GCS | Built-in | Automatic with GCS backend |
| Terraform + Azure | Built-in | Automatic with blob lease |
| Pulumi Cloud | Built-in | Automatic |
| Pulumi + S3 | Not built-in | Use CI/CD pipeline locks instead |

```hcl
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

### 5.1 Terraform Module Structure

```
modules/
  vpc/
    main.tf          # Resource definitions
    variables.tf     # Input variables
    outputs.tf       # Output values
    versions.tf      # Provider requirements
    README.md        # Usage documentation
  database/
    main.tf
    variables.tf
    outputs.tf
    versions.tf
```

### 5.2 Module Input/Output Contract

```hcl
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

### 6.2 Variable Files Per Environment (Preferred Approach)

```
environments/
  dev.tfvars
  staging.tfvars
  prod.tfvars
```

```hcl
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

### 6.4 Dev/Staging/Prod Parity

| Aspect | Dev | Staging | Prod |
|--------|-----|---------|------|
| Instance size | t3.micro | t3.small | t3.large |
| Replicas | 1 | 2 | 3 |
| Multi-AZ DB | No | No | Yes |
| WAF/DDoS | No | No | Yes |
| Monitoring | Basic | Standard | Full |
| Backup retention | 1 day | 7 days | 30 days |
| State locking | Optional | Required | Required |

**Environment rules:**
- MUST use the same Terraform/Pulumi code across all environments — only variable values differ.
- MUST NOT use `count` or `for_each` to conditionally create entire environment topologies — use variables to control sizing and features.
- MUST protect prod state with additional access controls (IAM policies, separate credentials).
- Use tfvars files (Terraform) or stack configs (Pulumi) per environment — never inline environment checks in resource blocks.

---

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

### 8.2 Sensitive Variables

```hcl
variable "db_password" {
  type      = string
  sensitive = true  # Suppresses value in plan output
}

output "db_connection_string" {
  value     = "postgresql://${var.db_user}:${var.db_password}@${aws_db_instance.main.endpoint}/mydb"
  sensitive = true
}
```

```bash
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

### 9.1 Plan on Pull Request

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

### 9.2 Apply on Merge

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

### 9.3 Approval Gates

| Gate | Implementation |
|------|---------------|
| Plan review | PR comment with plan output |
| Manual approval | GitHub environment protection rules |
| Policy check | OPA/Conftest step before apply |
| Cost estimate | Infracost integration |
| Security scan | tfsec or checkov step |

### 9.4 Pipeline State Locking

```yaml
# Use concurrency to prevent parallel applies
concurrency:
  group: terraform-${{ github.ref }}
  cancel-in-progress: false  # Don't cancel running applies
```

**CI/CD rules:**
- MUST run `terraform plan` on every PR that touches infrastructure code.
- MUST post plan output as a PR comment for human review.
- MUST use GitHub environment protection rules for production applies.
- MUST use `concurrency` groups to prevent parallel applies to the same environment.
- NEVER use `-auto-approve` without environment protection gates.
- MUST run `terraform validate` and `terraform fmt -check` in CI.

---

## STEP 10: Common Resource Patterns

### 10.1 VPC / Networking

```hcl
# VPC with public and private subnets
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = { Name = "${local.name_prefix}-vpc" }
}

resource "aws_subnet" "public" {
  count                   = length(var.availability_zones)
  vpc_id                  = aws_vpc.main.id
  cidr_block              = cidrsubnet(var.vpc_cidr, 4, count.index)
  availability_zone       = var.availability_zones[count.index]
  map_public_ip_on_launch = true
  tags = { Name = "${local.name_prefix}-public-${count.index}" }
}

resource "aws_subnet" "private" {
  count             = length(var.availability_zones)
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 4, count.index + length(var.availability_zones))
  availability_zone = var.availability_zones[count.index]
  tags = { Name = "${local.name_prefix}-private-${count.index}" }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
}

resource "aws_nat_gateway" "main" {
  count         = local.is_production ? length(var.availability_zones) : 1
  allocation_id = aws_eip.nat[count.index].id
  subnet_id     = aws_subnet.public[count.index].id
}
```

### 10.2 Compute (EC2 / GCE)

```hcl
resource "aws_instance" "app" {
  count                  = var.instance_count
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.instance_type
  subnet_id              = aws_subnet.private[count.index % length(aws_subnet.private)].id
  vpc_security_group_ids = [aws_security_group.app.id]
  iam_instance_profile   = aws_iam_instance_profile.app.name

  root_block_device {
    volume_type = "gp3"
    volume_size = 20
    encrypted   = true
  }

  metadata_options {
    http_tokens   = "required"  # IMDSv2 only
    http_endpoint = "enabled"
  }

  tags = { Name = "${local.name_prefix}-app-${count.index}" }
}
```

### 10.3 Database (RDS / CloudSQL)

```hcl
resource "aws_db_instance" "main" {
  identifier     = "${local.name_prefix}-db"
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = var.db_instance_class

  allocated_storage     = 20
  max_allocated_storage = 100  # Auto-scaling
  storage_encrypted     = true

  db_name  = var.db_name
  username = var.db_username
  password = var.db_password

  multi_az               = local.is_production
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.db.id]

  backup_retention_period = local.is_production ? 30 : 1
  skip_final_snapshot     = !local.is_production
  deletion_protection     = local.is_production

  performance_insights_enabled = local.is_production

  tags = local.common_tags
}
```

### 10.4 Storage (S3 / GCS)

```hcl
resource "aws_s3_bucket" "assets" {
  bucket = "${local.name_prefix}-assets"
}

resource "aws_s3_bucket_public_access_block" "assets" {
  bucket                  = aws_s3_bucket.assets.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "assets" {
  bucket = aws_s3_bucket.assets.id

  rule {
    id     = "transition-to-ia"
    status = "Enabled"

    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 365
      storage_class = "GLACIER"
    }
  }
}
```

### 10.5 DNS and CDN

```hcl
resource "aws_route53_zone" "main" {
  name = var.domain_name
}

resource "aws_route53_record" "app" {
  zone_id = aws_route53_zone.main.zone_id
  name    = var.environment == "prod" ? var.domain_name : "${var.environment}.${var.domain_name}"
  type    = "A"

  alias {
    name                   = aws_lb.app.dns_name
    zone_id                = aws_lb.app.zone_id
    evaluate_target_health = true
  }
}

resource "aws_cloudfront_distribution" "cdn" {
  enabled             = true
  default_root_object = "index.html"

  origin {
    domain_name = aws_s3_bucket.assets.bucket_regional_domain_name
    origin_id   = "S3-${aws_s3_bucket.assets.id}"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.main.cloudfront_access_identity_path
    }
  }

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-${aws_s3_bucket.assets.id}"
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      cookies { forward = "none" }
    }
  }

  restrictions {
    geo_restriction { restriction_type = "none" }
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate.main.arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }
}
```

---

## STEP 11: Refactoring

### 11.1 Moving Resources (Terraform)

```hcl
# Terraform 1.1+ — moved blocks (preferred, declarative)
moved {
  from = aws_instance.app
  to   = module.compute.aws_instance.app
}

moved {
  from = aws_s3_bucket.data
  to   = aws_s3_bucket.data_lake
}
```

```bash
# CLI approach (older)
terraform state mv aws_instance.app module.compute.aws_instance.app
```

### 11.2 Import Blocks (Terraform 1.5+)

```hcl
import {
  to = aws_iam_role.existing_role
  id = "my-existing-role"
}

# Then run:
# terraform plan -generate-config-out=generated.tf
# Review and clean up generated.tf, merge into your config
```

### 11.3 Replacing Resources Without Downtime

```bash
# Force replacement of a specific resource
terraform apply -replace="aws_instance.app[0]"

# Create-before-destroy lifecycle
resource "aws_instance" "app" {
  # ...
  lifecycle {
    create_before_destroy = true
  }
}
```

### 11.4 Removing Resources from State

```bash
# Remove from state without destroying the actual resource
terraform state rm aws_s3_bucket.legacy

# Pulumi equivalent
pulumi state delete urn:pulumi:prod::project::aws:s3/bucket:Bucket::legacy
```

**Refactoring rules:**
- MUST use `moved` blocks instead of `terraform state mv` for tracked, reviewable refactors.
- MUST run `terraform plan` after any state operation to confirm no unintended changes.
- MUST use `create_before_destroy` for resources that cannot tolerate downtime.
- MUST use `import` blocks (Terraform 1.5+) instead of `terraform import` CLI for reproducibility.
- NEVER refactor state and change resource configuration in the same apply — split into two operations.

---

## STEP 12: Anti-Patterns to Avoid

### 12.1 No Remote State

**Problem:** Local `terraform.tfstate` on one developer's machine. Lost laptop = lost infrastructure knowledge. Concurrent applies = corrupted state.

**Fix:** Configure remote backend immediately (Step 4).

### 12.2 Hardcoded Values

**Problem:** Region, account IDs, instance sizes, CIDR blocks embedded in resource definitions.

**Fix:** Extract to variables with defaults. Use locals for computed values.

### 12.3 Monolithic Configuration

**Problem:** Single `main.tf` with 2000+ lines covering VPC, compute, database, DNS, CDN.

**Fix:** Split into modules by concern. Use file-per-resource-group naming (`vpc.tf`, `database.tf`, `compute.tf`).

### 12.4 No State Locking

**Problem:** Two CI pipelines run `terraform apply` simultaneously, corrupting state.

**Fix:** Enable DynamoDB locking (S3 backend) or use backends with built-in locking. Use CI concurrency groups.

### 12.5 Apply Without Plan

**Problem:** Running `terraform apply` directly, accepting changes without review.

**Fix:** Always run `terraform plan -out=tfplan` first, review, then `terraform apply tfplan`.

### 12.6 Secrets in Version Control

**Problem:** Database passwords, API keys, access credentials in `.tfvars` or resource definitions committed to Git.

**Fix:** Use `sensitive = true`, env vars (`TF_VAR_*`), secrets managers, or `pulumi config --secret`.

### 12.7 Provider Version Unpinned

**Problem:** `terraform init` pulls latest provider version, breaking existing config.

**Fix:** Pin with `version = "~> 5.0"` in `required_providers`. Commit `.terraform.lock.hcl`.

### 12.8 Ignoring Plan Output

**Problem:** Seeing "3 to add, 1 to change, 2 to destroy" and applying without reading what is being destroyed.

**Fix:** Always read the full plan. Pay special attention to `destroy` and `replace` actions. Use `-target` for incremental applies if the plan is too large to review safely.

### 12.9 No Tagging Strategy

**Problem:** Resources created without tags — impossible to track ownership, cost allocation, or environment.

**Fix:** Use `default_tags` in provider config. Enforce required tags via policy-as-code.

### 12.10 State File as Documentation

**Problem:** Relying on `terraform state list` to understand infrastructure instead of maintaining readable config.

**Fix:** Keep config files well-organized and documented. Use `terraform-docs` to auto-generate module documentation.

---

## Quick Reference

### Terraform Command Cheat Sheet

```bash
terraform init                          # Initialize, download providers
terraform validate                      # Syntax and config validation
terraform fmt -recursive                # Format all .tf files
terraform plan -var-file=env.tfvars     # Preview changes
terraform plan -out=tfplan              # Save plan to file
terraform apply tfplan                  # Apply saved plan
terraform apply -target=module.vpc      # Apply specific resource/module
terraform destroy                       # Destroy all managed resources
terraform state list                    # List resources in state
terraform state show aws_vpc.main       # Show resource details
terraform output                        # Show all outputs
terraform import TYPE.NAME ID           # Import existing resource
terraform force-unlock LOCK_ID          # Release stuck lock
terraform providers                     # List required providers
```

### Pulumi Command Cheat Sheet

```bash
pulumi new aws-python                   # Create new project
pulumi stack init dev                   # Create new stack
pulumi stack select prod                # Switch stack
pulumi config set key value             # Set config
pulumi config set --secret key value    # Set secret config
pulumi preview                          # Preview changes
pulumi up                               # Deploy changes
pulumi destroy                          # Tear down stack
pulumi stack export                     # Export stack state
pulumi import TYPE NAME ID              # Import existing resource
pulumi refresh                          # Sync state with cloud
```

### File Organization Convention

```
infrastructure/
  main.tf              # Root module — module calls
  variables.tf         # Root input variables
  outputs.tf           # Root outputs
  versions.tf          # Terraform and provider versions
  backend.tf           # Remote state configuration
  locals.tf            # Computed values and common tags
  environments/
    dev.tfvars
    staging.tfvars
    prod.tfvars
  modules/
    vpc/
    compute/
    database/
    storage/
    dns/
```

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
