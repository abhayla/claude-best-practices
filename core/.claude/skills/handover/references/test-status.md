# Test Status

### Test Status
- **Suite:** `pytest tests/ -v`
- **Result:** 47 passed, 2 failed, 3 skipped
- **Failing tests:**
  - `test_auth_token_refresh` — expects 200, gets 401 (known issue, in progress)
  - `test_email_notification` — SMTP mock not configured (pre-existing)
- **Skipped tests:**
  - `test_integration_db` — requires Docker (skipped in local dev)
```

