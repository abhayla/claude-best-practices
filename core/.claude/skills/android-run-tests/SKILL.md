---
name: android-run-tests
description: >
  Run Android unit, UI, E2E, or journey tests with class name resolution.
  Auto-detects test type from class name pattern. Suggests /fix-loop on failure.
allowed-tools: "Bash Read Write Grep Glob"
argument-hint: "<TestClassName> [--unit|--ui|--e2e] [-x]"
version: "1.2.0"
type: workflow
---

# Run Android Tests

Run Android tests with class name resolution and type auto-detection.

**Arguments:** $ARGUMENTS

---

## STEP 1: Detect Android Directory

Locate the project's Android directory by scanning for `build.gradle.kts` or `build.gradle`:

```bash
# Check common locations
for dir in android app .; do
  if [ -f "$dir/build.gradle.kts" ] || [ -f "$dir/build.gradle" ]; then
    echo "Android root: $dir"
    break
  fi
done
```

---

## STEP 2: Resolve Class Name

Find the fully qualified class name from the short name:

```bash
# Search in unit test sources
find {android_dir} -name "*${CLASS}*.kt" -path "*/test/*" -type f

# Search in instrumented test sources
find {android_dir} -name "*${CLASS}*.kt" -path "*/androidTest/*" -type f
```

Extract the fully qualified class name (FQCN) from the `package` declaration in the matched file:

```bash
grep "^package " {matched_file} | awk '{print $2}'
# Result: com.example.feature.FeatureViewModelTest
```

If multiple matches are found, list them and ask the user to select.

---

## STEP 3: Detect Test Type

Auto-detect from class name pattern, or use explicit `--unit`/`--ui`/`--e2e` flag:

| Pattern | Type | Location | Requires Emulator |
|---------|------|----------|-------------------|
| `*ViewModelTest` | unit | `test/` | No |
| `*UseCaseTest` | unit | `test/` | No |
| `*RepositoryTest` | unit/integration | `test/` | No |
| `*DaoTest` | integration | `test/` or `androidTest/` | Depends |
| `*ScreenTest` | ui | `androidTest/` | Yes (or Robolectric) |
| `*FlowTest` | e2e | `androidTest/` | Yes |
| `*JourneyTest` | e2e | `androidTest/` | Yes |
| `*IntegrationTest` | integration | `androidTest/` | Yes |

Detection logic:
1. If `--unit`, `--ui`, or `--e2e` flag is provided → use that type
2. If file is under `test/` → unit test
3. If file is under `androidTest/` → instrumented test (UI or E2E)
4. If ambiguous → check class annotations (`@RunWith`, `@HiltAndroidTest`, `@get:Rule`)

---

## STEP 4: Verify Prerequisites

| Test Type | Prerequisites | Check Command |
|-----------|--------------|---------------|
| Unit | None | — |
| UI (Compose) | Emulator or Robolectric | `adb devices` |
| E2E | Emulator + app installed + backend running | `adb devices && adb shell pm list packages \| grep {package}` |

If emulator is required but not running:
```
⚠ No connected device found. Start an emulator:
  emulator -avd {avd_name}
```

---

## STEP 5: Execute Tests

### Unit Tests

```bash
cd {android_dir} && ./gradlew :app:testDebugUnitTest --tests "*.{ClassName}"
```

### Specific Module Unit Tests

```bash
cd {android_dir} && ./gradlew :{module}:testDebugUnitTest --tests "*.{ClassName}"
```

### Instrumented Tests (UI / E2E)

```bash
cd {android_dir} && ./gradlew :app:connectedDebugAndroidTest \
  -Pandroid.testInstrumentationRunnerArguments.class={fqcn}
```

### All Unit Tests

```bash
cd {android_dir} && ./gradlew testDebugUnitTest
```

### All Instrumented Tests

```bash
cd {android_dir} && ./gradlew connectedDebugAndroidTest
```

### With Coverage (JaCoCo)

```bash
cd {android_dir} && ./gradlew :app:testDebugUnitTest :app:jacocoTestReport
# Report: app/build/reports/jacoco/
```

---

## STEP 6: Analyze Results

### Parse Gradle Test Output

Test reports are generated at:
- Unit: `{module}/build/reports/tests/testDebugUnitTest/`
- Instrumented: `{module}/build/reports/androidTests/connected/`

### On Success

```
Android Tests: PASSED — {N} passed in {duration}s
  Type: {unit|ui|e2e}
  Class: {ClassName}
  Module: {module}
```

### On Failure

```
Android Tests: FAILED — {N} passed, {M} failed
  Type: {unit|ui|e2e}
  Class: {ClassName}

Failed Tests:
  {fqcn}#test_method_name — {error message}

Report: {module}/build/reports/tests/testDebugUnitTest/index.html

Suggested: /fix-loop with retest_command:
  cd {android_dir} && ./gradlew :app:testDebugUnitTest --tests "*.{ClassName}"
```

### Common Failure Patterns

| Error | Likely Cause | Fix |
|-------|-------------|-----|
| `No tests found` | Wrong class name or missing `@Test` annotation | Verify FQCN and annotations |
| `Hilt_*` not generated | Missing `kapt` or KSP processing | Run `./gradlew kaptDebugUnitTestKotlin` |
| `No connected devices` | Emulator not running | Start emulator |
| `INSTALL_FAILED_*` | APK installation issue | `adb uninstall {package}` and retry |
| `Dispatchers.Main` crash | Missing `TestDispatcherRule` | Add `@get:Rule val dispatcherRule = TestDispatcherRule()` |

---

## STEP 7: Suggest Next Actions

| Result | Action |
|--------|--------|
| All passed | Report success |
| Failures found | Suggest `/fix-loop` with exact retest command |
| Compilation error | Suggest fixing build errors first |
| Flaky (passes on re-run) | Flag as flaky, suggest `@RepeatedTest(3)` |

---

## STEP 8: Structured JSON Output

Write machine-readable results to `test-results/android-run-tests.json`:

```json
{
  "skill": "android-run-tests",
  "result": "PASSED|FAILED",
  "timestamp": "<ISO-8601>",
  "tests_run": "<total_count>",
  "tests_failed": "<failed_count>",
  "failures": [
    {
      "test": "<fqcn>#<method_name>",
      "category": "ASSERTION_FAILURE|RUNTIME_EXCEPTION|COMPILATION_ERROR|TIMEOUT",
      "file": "<test_file_path>",
      "message": "<error_message>"
    }
  ]
}
```

Create `test-results/` directory if it doesn't exist. This JSON is consumed by downstream stage gates.

```bash
mkdir -p test-results
python3 -c "
import json, datetime
result = {
    'skill': 'android-run-tests',
    'result': '<PASSED_or_FAILED>',
    'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'tests_run': '<N>',
    'tests_failed': '<N>',
    'failures': []
}
with open('test-results/android-run-tests.json', 'w') as f:
    json.dump(result, f, indent=2)
"
```

---

## MUST DO

- Always resolve the full class name before running — short names can match multiple files
- Always detect the correct Gradle module (`:app`, `:feature:auth`, etc.)
- Always check emulator status before running instrumented tests
- Always include the exact retest command in failure reports
- Always use `./gradlew` (Unix) not `gradlew.bat` — bash syntax even on Windows

## MUST NOT DO

- MUST NOT assume the Android root is `android/` — detect it
- MUST NOT run instrumented tests without verifying a device is connected
- MUST NOT use `-i` (interactive) flag with Gradle
- MUST NOT ignore compilation errors — report them before test results
