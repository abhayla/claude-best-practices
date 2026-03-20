# 0.2 Determine Branch Name

### 0.2 Determine Branch Name

Apply naming conventions based on the task type:

| Task Type | Prefix | Example |
|-----------|--------|---------|
| New feature | `feat/` | `feat/user-registration` |
| Bug fix | `fix/` | `fix/login-crash-empty-email` |
| Refactoring | `refactor/` | `refactor/extract-auth-service` |
| Documentation | `docs/` | `docs/api-reference-update` |
| Chore/maintenance | `chore/` | `chore/upgrade-dependencies` |
| Hotfix (production) | `hotfix/` | `hotfix/payment-timeout` |

Rules for branch names:
- Lowercase, kebab-case
- Include ticket/issue number if available: `feat/PROJ-123-user-registration`
- Max 50 characters
- Descriptive but concise

