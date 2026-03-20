# Since Last Handover ({previous_date})

### Next Steps Progress
| # | Item | Status | Notes |
|---|------|--------|-------|
| 1 | Complete token refresh endpoint | DONE | Implemented in commit `abc1234` |
| 2 | Fix failing test | DONE | Auto-resolved by #1 |
| 3 | Add edge case tests | PARTIAL | 2/4 cases covered |
| 4 | Refactor auth middleware | NOT STARTED | Deferred — user wants to ship first |

### New Items This Session
- 2 new decisions added
- 3 new pitfalls discovered
- 1 workaround added (API timeout)

### Carried Forward
- Edge case tests (2 remaining)
- Auth middleware refactor
- SMTP mock configuration (from 2 sessions ago)
```

### 11.2 Decision Evolution

Track how decisions evolved across sessions:

```markdown
### Decision Updates
- **Decision #3 (Auth approach):** Previously "use JWT only" →
  Updated to "JWT + session fallback for legacy clients" (reason: legacy
  mobile app cannot handle JWT refresh flow)
```

### 11.3 Pitfall Resolution

Track which pitfalls from previous sessions have been resolved:

```markdown
### Pitfall Status
- **RESOLVED:** "Docker must be running for tests" → Added Docker health
  check to test setup (`conftest.py:5`) with helpful error message
- **STILL ACTIVE:** "API rate limit is 100/min not 1000/min"
- **NEW:** "Don't run `make clean` in CI — deletes cached test fixtures"
```

---

