# STEP 7: Generate Standards Report

### 7.1 Report Format

```
=========================================
  PR STANDARDS CHECK: {PASS / FAIL / WARN}
=========================================

Branch: {current_branch} -> {base_branch}
Files analyzed: {count}
Lines analyzed: {count} (changed lines only)
Rules applied: {count} ({built_in_count} built-in + {custom_count} custom)

-----------------------------------------
  CRITICAL (must fix before merge): {count}
-----------------------------------------

[C1] no-debugger — Debugger statement found
     File: src/routes/users.py, line 45
     Code: `    debugger`
     Fix:  Remove the debugger line (auto-fixable)

[C2] no-hardcoded-secrets — Hardcoded API key detected
     File: src/services/payment.py, line 12
     Code: `    api_key = "sk_live_abc123def456"`
     Fix:  Move to environment variable. Use `os.getenv("STRIPE_API_KEY")`

[C3] rate-limiting-required — API endpoint missing rate limiting
     File: src/routes/users.py, line 30
     Code: `@router.post("/api/users")`
     Fix:  Add `@rate_limit(max=100, per=60)` decorator before route handler

-----------------------------------------
  WARNING (should fix): {count}
-----------------------------------------

[W1] new-function-needs-test — New function has no tests
     File: src/services/user_service.py, line 23
     Code: `def create_user(email: str, role: str) -> User:`
     Fix:  Add test in tests/test_user_service.py for create_user()

[W2] no-swallowed-errors — Error silently swallowed in catch block
     File: src/routes/users.py, line 67
     Code: `    except Exception: pass`
     Fix:  Log the error or re-raise: `except Exception as e: logger.error(f"Failed: {e}"); raise`

[W3] no-todo-without-ticket — TODO without issue reference
     File: src/services/user_service.py, line 45
     Code: `    # TODO: add email validation`
     Fix:  Create an issue and reference it: `# TODO(#123): add email validation`

-----------------------------------------
  INFO (optional improvements): {count}
-----------------------------------------

[I1] no-magic-numbers — Magic number in logic
     File: src/services/user_service.py, line 34
     Code: `    if retry_count > 3:`
     Fix:  Extract to named constant: `MAX_RETRIES = 3`

[I2] docstring-required — Public function missing docstring
     File: src/services/user_service.py, line 23
     Code: `def create_user(email: str, role: str) -> User:`
     Fix:  Add docstring describing parameters and return value

=========================================
  TOTALS
=========================================

| Severity | Count | Auto-fixable |
|----------|-------|-------------|
| Critical | 3     | 1           |
| Warning  | 3     | 0           |
| Info     | 2     | 0           |
| **Total**| **8** | **1**       |

Auto-fixable: 1 of 8 violations
Run with --fix to apply auto-fixes.
```

### 7.2 Per-File Summary

Additionally, provide a per-file violation count for quick scanning:

```
PER-FILE SUMMARY
================

| File | Critical | Warning | Info | Total |
|------|----------|---------|------|-------|
| src/routes/users.py | 2 | 1 | 0 | 3 |
| src/services/user_service.py | 0 | 2 | 2 | 4 |
| src/services/payment.py | 1 | 0 | 0 | 1 |
| tests/test_users.py | 0 | 0 | 0 | 0 |
| **Total** | **3** | **3** | **2** | **8** |
```

---

