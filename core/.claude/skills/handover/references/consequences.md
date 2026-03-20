# Consequences

### 3.4 Workaround Registry

Workarounds deserve special attention because they are technical debt with context:

```markdown
### Active Workarounds

1. **What:** Hardcoded timeout to 30s in API client
   **Why:** Upstream service has undocumented rate limiting at ~100 req/min
   **Proper fix:** Implement exponential backoff with retry
   **Tracked in:** Issue #789
   **Risk if forgotten:** Silent failures when request volume increases

2. **What:** Disabled SSL verification for staging environment
   **Why:** Staging cert expired, renewal blocked on ops team
   **Proper fix:** Renew the staging certificate
   **Tracked in:** Ops ticket INFRA-234
   **Risk if forgotten:** Security vulnerability if accidentally enabled in production
```

---

