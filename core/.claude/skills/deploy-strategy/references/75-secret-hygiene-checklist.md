# 7.5 Secret Hygiene Checklist

### 7.5 Secret Hygiene Checklist

- [ ] No secrets in environment variables visible via `/proc` or `docker inspect`
- [ ] No secrets in Docker image layers (use multi-stage builds or runtime injection)
- [ ] No secrets in git history (use `git-secrets` or `trufflehog` pre-commit hook)
- [ ] All secrets have an owner and rotation schedule documented
- [ ] Rotation can be performed without application downtime
- [ ] Secret access is logged and auditable
- [ ] Break-glass procedure exists for emergency secret revocation

---

