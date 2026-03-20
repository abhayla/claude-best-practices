# DAST Security Report

### Summary

| Severity | Count | Action |
|----------|-------|--------|
| CRITICAL | 0 | — |
| HIGH | 1 | ❌ Must fix |
| MEDIUM | 3 | ⚠️ Review |
| LOW | 5 | 📝 Noted |

### Findings

#### [HIGH] Missing Content-Security-Policy
- **URL:** All responses
- **Risk:** XSS attacks not mitigated by CSP
- **Fix:** Add CSP header in middleware:
  ```python
  response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'"
  ```
- **Ref:** OWASP A05:2021 Security Misconfiguration

#### [MEDIUM] Session cookie without SameSite
- **URL:** POST /login
- **Risk:** CSRF attacks possible
- **Fix:** Set `SameSite=Lax` on session cookie
- **Ref:** OWASP A07:2021 Identification and Authentication Failures

### Gate Decision
- **PASS** — No CRITICAL/HIGH findings (or all accepted with documented risk)
- **BLOCK** — N CRITICAL/HIGH findings must be resolved
```

---

