# 8.2 Sensitive Variables

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
