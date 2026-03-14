---
name: android-run-tests
description: >
  Run Android unit, UI, E2E, or journey tests with class name resolution.
  Auto-detects test type from class name pattern. Suggests /fix-loop on failure.
allowed-tools: "Bash Read Grep Glob Skill"
argument-hint: "<TestClassName> [--unit|--ui|--e2e] [-x]"
version: "1.0.0"
type: workflow
---

# Run Android Tests

Run Android tests with class name resolution and type auto-detection.

**Arguments:** $ARGUMENTS

---

## STEP 1: Resolve Class Name

```bash
cd android && find . -name "*${CLASS}*.kt" -path "*/test/*" -o -name "*${CLASS}*.kt" -path "*/androidTest/*"
```

## STEP 2: Detect Test Type

| Pattern | Type | Command |
|---------|------|---------|
| `*ViewModelTest` | unit | `./gradlew :app:testDebugUnitTest --tests "*.{Class}"` |
| `*ScreenTest` | ui | `./gradlew :app:connectedDebugAndroidTest -P...class={fqcn}` |
| `*FlowTest` | e2e | `./gradlew :app:connectedDebugAndroidTest -P...class={fqcn}` |

## STEP 3: Execute

```bash
cd android && ./gradlew {command}
```

## STEP 4: Report

**On success:**
```
Android Tests: PASSED — {N} passed in {duration}s
```

**On failure:**
```
Android Tests: FAILED
Suggested: /fix-loop with retest_command: cd android && ./gradlew {command}
```

## Notes

- Unit tests don't need emulator
- E2E tests need emulator AND backend running
- Use `./gradlew` from `android/` directory (Unix syntax)
