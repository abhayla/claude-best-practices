---
name: auto-verify
description: >
  Post-change verification loop: identifies changed files, maps to targeted tests,
  runs tests with smart priority, analyzes failures, applies fixes with approval.
  Use after making code changes to verify correctness.
allowed-tools: "Bash Read Grep Glob Write Edit Skill"
argument-hint: "[--files <paths>] [--full-suite]"
---

# Auto-Verify — Post-Change Verification

Automatically verify code changes by running targeted tests and analyzing results.

**Arguments:** $ARGUMENTS

---

## STEP 1: Identify Changes

```bash
git diff --name-only HEAD
git diff --name-only --cached
```

If `--files` provided, use those instead.

## STEP 2: Map Changes to Tests

For each changed file, find related test files:
- Source `src/foo.py` → Test `tests/test_foo.py`
- Source `app/services/bar.py` → Test `tests/services/test_bar.py`
- Use project conventions for test file naming

## STEP 3: Run Targeted Tests

Run only the tests related to changed files first:

1. Execute mapped test files
2. If all pass and `--full-suite` not specified → report success
3. If any fail → analyze and attempt fix

## STEP 4: Analyze Failures

For each failure:
1. Read the test and source code
2. Determine if the failure is from our change or pre-existing
3. If from our change → suggest fix
4. If pre-existing → note it but don't block

## STEP 5: Apply Fixes (with approval)

For each identified fix:
1. Describe the fix to the user
2. Apply only if approved or if running autonomously
3. Re-run affected tests after fix

## STEP 6: Regression Check

If fixes were applied, run broader test suite to check for regressions.

## STEP 7: Report

```
Auto-Verify: [PASSED / FIXED / FAILED]
  Changed files: N
  Tests run: M
  Passed: P | Failed: F
  Fixes applied: X
  Regressions: Y
```
