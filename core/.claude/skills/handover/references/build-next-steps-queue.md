# STEP 6: Build Next Steps Queue

### 6.1 Priority Framework

| Priority | Criteria | Examples |
|----------|----------|---------|
| **P0 — Blocking** | Must be done before anything else works | Fix broken build, resolve merge conflict |
| **P1 — Critical** | Core functionality, test failures | Complete the feature, fix failing tests |
| **P2 — Important** | Quality, robustness, edge cases | Add error handling, write missing tests |
| **P3 — Nice to Have** | Cleanup, optimization, documentation | Refactor, update docs, optimize query |

### 6.2 Next Step Format

Each item must include:

```markdown
1. **[P1] Complete token refresh endpoint** [medium]
   - **Context:** Handler is implemented in `src/auth/handler.py:45-80` but
     missing error handling for expired refresh tokens.
   - **What to do:** Add try/catch around `jwt.decode()` call. Return 401 with
     `{"error": "refresh_token_expired"}` body. See existing pattern in
     `src/auth/login.py:30`.
   - **Test:** `pytest tests/test_auth.py::test_token_refresh -v`
   - **Dependencies:** None
   - **Blockers:** None

2. **[P1] Fix failing test `test_auth_token_refresh`** [quick]
   - **Context:** Test expects 200 but gets 401 because refresh endpoint
     is not yet handling the happy path correctly.
   - **What to do:** This will auto-resolve when item #1 is completed.
   - **Dependencies:** Depends on #1

3. **[P2] Add edge case tests for token expiry** [medium]
   - **Context:** Current tests only cover happy path. Need tests for:
     expired token, malformed token, missing token, revoked token.
   - **What to do:** Add 4 test cases in `tests/test_auth.py`. Use the
     `expired_token_fixture` in `tests/conftest.py:15`.
   - **Dependencies:** Complete after #1

4. **[P3] Refactor auth middleware to use dependency injection** [complex]
   - **Context:** Currently hardcoded to use `JWTValidator`. Should accept
     any validator implementing `AuthValidator` protocol.
   - **What to do:** Define protocol in `src/auth/protocols.py`, update
     middleware constructor, update all call sites.
   - **Dependencies:** Complete after #1-3
   - **Blockers:** Need user input on whether to use Protocol or ABC
```

### 6.3 Complexity Estimates

| Estimate | Meaning | Typical Time |
|----------|---------|-------------|
| **quick** | Single file change, clear path | < 15 minutes |
| **medium** | Multiple files, some investigation needed | 15-60 minutes |
| **complex** | Architecture decisions, multiple components | 1+ hours |

### 6.4 Dependency Graph

If next steps have dependencies, make them explicit:

```
Dependency Graph:
  #1 (token refresh) ──→ #2 (fix test) ──→ #3 (edge case tests)
                                                    │
  #4 (DI refactor) ←────────────────────────────────┘

  Independent: #5, #6 can be done in any order
```

---

