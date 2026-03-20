# STEP 7: Secret Rotation Strategy

### 7.1 Rotation Schedule

| Secret Type | Rotation Period | Method |
|-------------|----------------|--------|
| API keys (third-party) | 90 days | Regenerate in provider dashboard, update vault |
| Database credentials | 30 days | Automated via vault or cloud secrets manager |
| JWT signing keys | 7 days (access), 30 days (refresh) | Dual-key rotation (accept old+new during transition) |
| TLS certificates | Auto (Let's Encrypt) or 365 days | cert-manager (K8s) or ACM (AWS) auto-renewal |
| Service-to-service tokens | 90 days | OIDC federation preferred (no static tokens) |
| Encryption keys (KMS) | 365 days | Cloud KMS auto-rotation (AWS/GCP/Azure) |

### 7.2 Vault Integration Patterns

| Provider | Tool | Config |
|----------|------|--------|
| HashiCorp Vault | Vault Agent / CSI Provider | Dynamic secrets with TTL, auto-renewal |
| AWS | Secrets Manager | `rotation_lambda_arn` + `rotation_rules { automatically_after_days = 30 }` |
| GCP | Secret Manager | Version-based, `replication { automatic {} }` |
| Azure | Key Vault | `rotation_policy` block with auto-rotation |

```hcl
