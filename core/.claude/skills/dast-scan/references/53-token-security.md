# 5.3 Token Security

### 5.3 Token Security

For JWT/API token authentication:

| Check | Pass Criteria |
|-------|--------------|
| Token expiry | Expires within reasonable time (≤1h for access, ≤7d for refresh) |
| Token revocation | Logout invalidates token server-side |
| Token storage | Not in URL params, not in localStorage for sensitive apps |
| CORS policy | `Access-Control-Allow-Origin` not `*` for auth endpoints |
| Rate limiting | Login endpoint rate-limited (≤10 attempts/min) |

---

