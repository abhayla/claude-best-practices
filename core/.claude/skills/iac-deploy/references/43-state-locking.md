# 4.3 State Locking

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
