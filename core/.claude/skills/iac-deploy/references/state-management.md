# State Management

## Remote Backends — Terraform

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

## Remote Backends — Pulumi

```bash
# Pulumi Cloud (default, managed)
pulumi login

# S3-compatible backend
pulumi login s3://mycompany-pulumi-state

# Local filesystem (development only)
pulumi login --local
```

## State Locking (Terraform)

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

## State Migration

```bash
# Terraform — migrate from local to S3
# 1. Add backend config to backend.tf
# 2. Run init with migration flag
terraform init -migrate-state

# Force unlock if state is stuck (use with extreme caution)
terraform force-unlock <LOCK_ID>
```

## Import Existing Resources

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

## State Management Rules

- MUST use remote state with locking for any shared or production infrastructure.
- MUST enable encryption on the state backend (state contains secrets in plaintext).
- NEVER manually edit state files — use `terraform state mv`, `terraform state rm`, or `pulumi state delete`.
- MUST back up state before any migration or import operation.
- Use separate state files per environment (separate backends or key paths).
