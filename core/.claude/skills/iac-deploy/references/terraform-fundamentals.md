# Terraform Fundamentals

## Provider Configuration

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

## Data Sources

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

## Variables, Outputs, and Locals

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
