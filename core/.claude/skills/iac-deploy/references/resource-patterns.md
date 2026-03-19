# Resource Patterns, Refactoring, and Anti-Patterns

Common IaC resource patterns for cloud infrastructure, refactoring strategies, and anti-patterns to avoid.

---

## Common Resource Patterns

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

## Refactoring

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

## Anti-Patterns to Avoid

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
