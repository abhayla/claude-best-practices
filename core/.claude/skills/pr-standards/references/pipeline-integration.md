# STEP 9: Pipeline Integration

### 9.1 Input: From /implement or /executing-plans

This skill expects a completed implementation — code is written, tests pass, branch is committed. The input is the branch diff against main.

Prerequisites:
- All implementation work is committed
- Tests pass (verified by /implement Step 6)
- Branch is ready for review

### 9.2 Output: Standards Report + Next Step

Based on the verdict, provide a clear next action:

| Verdict | Critical | Warnings | Action |
|---------|----------|----------|--------|
| **FAIL** | > 0 | any | "Fix {N} critical violations before proceeding. Run `/pr-standards` again after fixing." |
| **FAIL (strict)** | 0 | > 0 | "Strict mode: fix {N} warnings before proceeding. Run `/pr-standards` again after fixing." |
| **WARN** | 0 | > 5 | "Consider addressing {N} warnings before review. Proceed with `/request-code-review`? Warnings will be included in the PR description." |
| **PASS** | 0 | <= 5 | "Standards check passed. Proceed with `/request-code-review`." |

### 9.3 Handoff to /request-code-review

When the standards check passes (or the user chooses to proceed with warnings), include the standards report in the PR review workflow:

```
Standards Check: PASS (2 warnings, 1 info)
Warnings:
  [W1] New function create_user() has no tests
  [W2] TODO without ticket reference on line 45

These will be noted in the PR description for reviewer awareness.
Proceed with /request-code-review.
```

### 9.4 Feedback Loop: Fix and Re-Check

If the standards check fails:

1. Fix all critical violations (manually or via auto-fix)
2. Commit the fixes
3. Re-run `/pr-standards` to verify
4. Repeat until the check passes
5. Then proceed to `/request-code-review`

```
Standards check FAILED. 3 critical violations found.

After fixing, run:
  /pr-standards

Or apply auto-fixes and re-check:
  /pr-standards --fix
```

---

