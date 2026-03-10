---
name: run-android-tests
description: >
  Run Android unit, UI, E2E, or journey tests with class name resolution.
  Use when running Android tests, verifying UI changes, or checking specific test classes.
  Auto-detects test type from class name pattern. Suggests /fix-loop on failure.
allowed-tools: "Bash Read Grep Glob Skill"
argument-hint: "<TestClassName> [--unit|--ui|--e2e|--journey] [-x]"
---

# Run Android Tests

Run Android tests with class name resolution and type auto-detection.

**Arguments:** $ARGUMENTS

---

## Input Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `test_class` | positional | (required) | Test class name (partial OK: `HomeViewModel` -> `HomeViewModelTest`) |
| `--unit` | flag | — | Force unit test (src/test) |
| `--ui` | flag | — | Force UI/instrumented test (src/androidTest/presentation) |
| `--e2e` | flag | — | Force E2E flow test (src/androidTest/e2e) |
| `--journey` | flag | — | Force journey suite (src/androidTest/e2e/journeys) |
| `-x` | flag | false | Stop on first failure (unit tests only) |

**Auto-detection rules** (when no flag given):

| Pattern | Detected Type |
|---------|--------------|
| `*ViewModelTest` | unit |
| `*ScreenTest` | ui |
| `*FlowTest` | e2e |
| `J\d\d_*Suite` | journey |
| `*Test` in `e2e/` | e2e |
| `*Test` in `presentation/` | ui |

**Common patterns:**

| Command | What it does |
|---------|-------------|
| `/run-android-tests HomeViewModelTest` | Unit test for HomeViewModel |
| `/run-android-tests HomeScreenTest` | UI test for HomeScreen |
| `/run-android-tests AuthFlowTest` | E2E auth flow |
| `/run-android-tests J01` | Journey suite J01 |
| `/run-android-tests ChatScreenTest --ui` | Force UI type |

---

## STEP 1: Resolve Class Name

Find the exact test file:

```bash
cd android && find . -name "*${CLASS_NAME}*.kt" -path "*/test/*" -o -name "*${CLASS_NAME}*.kt" -path "*/androidTest/*" 2>/dev/null
```

Extract the fully qualified class name from the file's package declaration:

```bash
head -1 ${FOUND_FILE} | grep -oP 'package \K[^\s]+'
```

Combine: `{package}.{ClassName}`

If no match found, list similar test files and report error.

---

## STEP 2: Determine Test Type

If explicit flag given, use it. Otherwise auto-detect from file path:

| Path contains | Type | Gradle command |
|--------------|------|---------------|
| `src/test/` | unit | `./gradlew :app:testDebugUnitTest --tests "*.{ClassName}"` |
| `src/androidTest/java/*/presentation/` | ui | `./gradlew :app:connectedDebugAndroidTest -P...class={fqcn}` |
| `src/androidTest/java/*/e2e/` | e2e | `./gradlew :app:connectedDebugAndroidTest -P...class={fqcn}` |
| `src/androidTest/java/*/e2e/journeys/` | journey | `./gradlew :app:connectedDebugAndroidTest -P...class={fqcn}` |

---

## STEP 3: Pre-flight (Instrumented Tests Only)

For UI, E2E, and journey tests:

```bash
# Check emulator
adb devices 2>/dev/null | grep -w "device" | head -1
```

If no emulator connected, report error and suggest starting one.

Quick build check:

```bash
cd android && ./gradlew assembleDebug assembleDebugAndroidTest 2>&1 | tail -5
```

---

## STEP 4: Execute

**Unit tests:**
```bash
cd android && ./gradlew :app:testDebugUnitTest --tests "*.${CLASS_NAME}" --console=plain 2>&1
```
Timeout: 300 seconds.

**Instrumented tests (UI/E2E/Journey):**
```bash
cd android && ./gradlew :app:connectedDebugAndroidTest \
  -Pandroid.testInstrumentationRunnerArguments.class=${FQCN} 2>&1
```
Timeout: 600 seconds (single class), 900 seconds (journey suite).

---

## STEP 5: Report

**On success:**
```
Android Tests: PASSED
  Type: {unit|ui|e2e|journey}
  Class: {ClassName}
  Result: {N} passed in {duration}s
```

**On failure:**
```
Android Tests: FAILED
  Type: {unit|ui|e2e|journey}
  Class: {ClassName}
  Result: {N} passed, {N} failed

  Failed tests:
    - {test_method}: {brief error}

  Suggested: /fix-loop with retest_command:
    cd android && ./gradlew :app:{command} {args}
```

---

## CRITICAL NOTES

- Use API 34 emulator (not API 36 — Espresso compatibility issues)
- Unit tests do NOT need emulator or backend
- E2E tests need both emulator AND backend running at localhost:8000
- For E2E backend URL: `http://10.0.2.2:8000` (emulator -> host mapping)
- If Gradle daemon hangs on Windows: `./gradlew --stop`
