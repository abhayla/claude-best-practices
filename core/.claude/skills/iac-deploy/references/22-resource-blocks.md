# 2.2 Resource Blocks

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

