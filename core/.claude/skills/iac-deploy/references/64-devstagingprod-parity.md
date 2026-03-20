# 6.4 Dev/Staging/Prod Parity

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

