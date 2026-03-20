# Review Readiness Summary

## Review Readiness Summary

After completing all steps, produce a final summary:

```
PR REVIEW READINESS REPORT
============================

PR: feat(auth): add role-based access control with token binding
Branch: feature/rbac-token-binding -> main

Size: 342 lines changed (Medium)
Risk: HIGH (auth changes, schema migration)

Files by risk:
  HIGH:   3 files (src/auth/*, migrations/*)
  MEDIUM: 2 files (src/services/*)
  LOW:    4 files (tests/*, docs/*)

Breaking changes: 2 detected (API response shape, new env var)
Review questions: 3 targeted questions for specific reviewers
Pre-review checks: ALL PASSED
  [PASS] No debug code
  [PASS] No untracked TODOs
  [PASS] No commented-out code
  [PASS] No merge conflicts
  [PASS] No sensitive data
  [PASS] Branch rebased on latest main

Suggested reviewers:
  Required: @alice (CODEOWNERS: src/auth/)
  Recommended: @bob (recent context), @carol (original author)
  Optional: @dave (DBA for migration review)

Estimated review time: 25-35 minutes

PR created: https://github.com/org/repo/pull/456
```

---

