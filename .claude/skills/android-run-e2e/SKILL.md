---
name: android-run-e2e
description: >
  Run Android E2E tests sequentially by feature group with auto-fix.
  Auto-delegates to /fix-loop on failure. Use for E2E regression testing.
allowed-tools: "Bash Read Grep Glob Skill"
argument-hint: "[feature-group|all]"
---

# Run Android E2E Tests by Feature Group

Run E2E tests organized by feature group with automatic fix delegation.

**Arguments:** $ARGUMENTS

---

## Feature Groups

Organize your E2E tests by feature area. Example groups:
- `auth` — Authentication and onboarding flows
- `home` — Main screen functionality
- `settings` — Settings and preferences
- `navigation` — Cross-screen navigation flows

## Execution

For each group:

1. Run the group's test class(es)
2. If failure → delegate to `/fix-loop` (max 3 retries per group)
3. If still failing → mark as FAILED, continue to next group
4. Track pass/fail per group

```bash
cd android && ./gradlew :app:connectedDebugAndroidTest \
  -Pandroid.testInstrumentationRunnerArguments.class={test_class}
```

## Report

```
E2E Test Results:
  Groups: N total | X passed | Y failed
  Per group:
    auth: PASSED
    home: PASSED
    settings: FAILED (3 retries exhausted)
```

## Notes

- Requires running emulator and backend
- Each group gets up to 3 fix-loop retries
- Failed groups don't block other groups from running
