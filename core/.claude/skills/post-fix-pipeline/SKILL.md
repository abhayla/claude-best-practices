---
name: post-fix-pipeline
description: >
  Post-fix verification pipeline: regression tests, full test suite with auto-fix,
  documentation updates, and git commit. Use after fix-loop succeeds to verify
  no regressions before committing.
allowed-tools: "Bash Read Grep Glob Write Edit Skill"
argument-hint: "[fixes_applied] [test_suite_commands] [commit_format]"
version: "1.0.0"
type: workflow
---

# Post-Fix Pipeline

Verify fixes don't cause regressions, update docs, and commit.

**Input:** $ARGUMENTS

---

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `fixes_applied` | — | Summary of fixes that were applied |
| `test_suite_commands` | — | Commands to run for full test suite verification |
| `commit_format` | `fix(scope): description` | Commit message format |
| `push` | false | Whether to push after commit |

---

## STEP 1: Regression Testing

Run targeted tests on the areas where fixes were applied:

1. Identify test files related to changed files
2. Run targeted tests first
3. Report any regressions introduced by the fix

## STEP 2: Full Test Suite Verification

If test suite commands are provided, run them:

1. Execute each test suite command
2. If failures found:
   - Attempt auto-fix (max 2 attempts via `/fix-loop`)
   - If still failing, report and block commit
3. Gate: PASSED / PASSED_AFTER_FIX / FAILED

## STEP 3: Documentation Updates

Delegate to docs-manager agent if documentation needs updating:
- Update continuation/handoff documents
- Record test results

## STEP 4: Git Commit

If all gates pass:

1. Delegate to git-manager agent for secure commit
2. Use conventional commit format
3. Include summary of fixes in commit body

If gates fail:
- Report blocking issues
- Do NOT commit

## STEP 5: Learning Capture

Invoke `/learn-n-improve session` to record the fix for future reference.

## Report

```
Post-Fix Pipeline:
  Regression tests: PASSED/FAILED
  Test suite: PASSED/PASSED_AFTER_FIX/FAILED
  Documentation: UPDATED/SKIPPED
  Commit: [hash] — [message] / BLOCKED
```
