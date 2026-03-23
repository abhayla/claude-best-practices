---
name: flutter-e2e-test
description: >
  Run Flutter E2E tests across Android, Web, and desktop platforms with MCP-based semantic
  element recognition, integration_test package workflows, self-healing selectors,
  visual regression, monkey testing, and CI/CD integration. Use when writing, running,
  or debugging end-to-end tests for Flutter apps.
triggers: "flutter test, e2e, integration test, end-to-end, widget test, UI test"
allowed-tools: "Bash Read Write Edit Grep Glob Skill"
argument-hint: "<test-scope: 'all' | feature-name | 'setup' | 'visual' | 'monkey'>"
version: "1.2.0"
type: workflow
---

# Flutter E2E Testing

Run and author end-to-end tests for Flutter apps across Android, Web, and desktop platforms using semantic element recognition and the `integration_test` package.

**Request:** $ARGUMENTS

---

## STEP 1: Project Setup

Ensure the `integration_test` package and test infrastructure are configured.

### Dependencies (pubspec.yaml)

```yaml
dev_dependencies:
  integration_test:
    sdk: flutter
  flutter_test:
    sdk: flutter
  flutter_driver:
    sdk: flutter
  patrol: ^3.6.0            # Advanced native interaction testing
  golden_toolkit: ^0.15.0    # Visual regression / golden tests
```

### Directory Structure

```
integration_test/
  app_test.dart              # Main test entry point
  robots/                    # Page-object / robot pattern classes
    login_robot.dart
    home_robot.dart
    navigation_robot.dart
  fixtures/
    test_data.dart           # Shared test constants and factories
  utils/
    test_helpers.dart        # Pump helpers, custom matchers
    screenshot_utils.dart    # Screenshot capture and comparison
test_driver/
  integration_test.dart      # Driver entry for flutter drive
```

### Test Driver Entry Point

```dart
// test_driver/integration_test.dart
import 'package:integration_test/integration_test_driver_extended.dart';

Future<void> main() => integrationDriver();
```

### Verify Setup

```bash
flutter pub get
# Confirm integration_test is resolvable
flutter test integration_test/ --no-pub 2>&1 | head -5
```

---

## STEP 2: Writing E2E Tests


**Read:** `references/writing-e2e-tests.md` for detailed step 2: writing e2e tests reference material.

## STEP 3: Test Patterns


**Read:** `references/test-patterns.md` for detailed step 3: test patterns reference material.

## STEP 4: Visual Regression Testing

Capture golden screenshots and compare against baselines.

### Screenshot Capture

```dart
testWidgets('home screen matches golden', (tester) async {
  final binding = IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  await tester.pumpWidget(const ProviderScope(child: MyApp()));
  await tester.pumpAndSettle();

  // Capture screenshot (integration_test native)
  await binding.convertFlutterSurfaceToImage();
  await tester.pumpAndSettle();
  await binding.takeScreenshot('home_screen_golden');
});
```

### Golden Toolkit Approach

```dart
testGoldens('login screen golden', (tester) async {
  await loadAppFonts();
  await tester.pumpWidgetBuilder(
    const LoginScreen(),
    wrapper: materialAppWrapper(theme: AppTheme.light()),
    surfaceSize: const Size(375, 812), // iPhone dimensions
  );
  await screenMatchesGolden(tester, 'login_screen');
});
```

### Updating Goldens

```bash
# Regenerate golden files after intentional UI changes
flutter test --update-goldens test/goldens/
```

### Autonomous Pass/Fail Determination

Golden file tests AUTOMATICALLY fail when the rendered widget differs from the stored baseline.
The test framework performs pixel-by-pixel comparison:

- If baseline exists and matches → TEST PASSES
- If baseline exists and differs → TEST FAILS with diff output
- If baseline does not exist → TEST FAILS with "Golden file not found"

No human intervention needed for pass/fail — the framework handles it.

### Threshold Configuration

```dart
// Configure comparison tolerance in flutter_test_config.dart
import 'package:flutter_test/flutter_test.dart';

Future<void> testExecutable(FutureOr<void> Function() testMain) async {
  // Allow 0.5% pixel difference (anti-aliasing, font rendering)
  goldenFileComparator = LocalFileComparator.forDirectory(
    Uri.parse('test/goldens'),
  )..threshold = 0.005; // 0.5% tolerance
  await testMain();
}
```

Threshold guidelines:

| Mode | Threshold | Use Case |
|------|-----------|----------|
| Strict | 0.0 | Design system components, icons |
| Standard | 0.005 | General UI screens |
| Tolerant | 0.02 | Screens with minor rendering variance |

### Masking Dynamic Content

```dart
// Mask timestamps, avatars, and other dynamic content before golden comparison
testGoldens('dashboard with masked dynamic content', (tester) async {
  await loadAppFonts();
  await tester.pumpWidgetBuilder(
    const DashboardScreen(),
    wrapper: materialAppWrapper(theme: AppTheme.light()),
    surfaceSize: const Size(375, 812),
  );

  // Replace dynamic elements with placeholders before capture
  // Option 1: Use a test-mode flag to show static content
  // Option 2: Use golden_toolkit's customPump to freeze animations
  await screenMatchesGolden(tester, 'dashboard_masked');
});
```

Common items to mask:
- Timestamps and relative dates → use frozen clock (`clock` package)
- User avatars → use deterministic test data with fixed URLs
- Animations → use `tester.binding.setSurfaceSize()` and disable animations in test mode
- Random content → use seeded random generators

### CI Golden Comparison

```yaml
# In the GitHub Actions workflow, add golden comparison step:
      - name: Run golden tests
        run: flutter test test/goldens/ --reporter github

      - name: Upload golden diffs on failure
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: golden-diffs
          path: test/goldens/failures/
          retention-days: 14
```

```bash
# Update goldens after intentional UI changes (review before committing)
flutter test --update-goldens test/goldens/
git diff test/goldens/  # Review changes visually
git add test/goldens/
git commit -m "chore(visual): update golden files — new dashboard layout"
```

---

## STEP 5: Monkey / Fuzz Testing

**Read:** `references/monkey-fuzz-testing.md` for detailed step 5: monkey / fuzz testing reference material.

## STEP 6: Platform-Specific Execution

### Flutter (Default)

```bash
# Run all integration tests
flutter test integration_test/

# Run specific test file
flutter test integration_test/app_test.dart

# Run with verbose output
flutter test integration_test/ --reporter expanded

# Using flutter drive (supports screenshots, performance tracing)
flutter drive \
  --driver=test_driver/integration_test.dart \
  --target=integration_test/app_test.dart
```

### Android (Emulator/Device)

```bash
# Start emulator
flutter emulators --launch <emulator_id>

# Verify device connected
flutter devices
adb devices

# Run on connected Android device
flutter test integration_test/ -d <device_id>

# Run via Gradle for CI (generates JUnit XML reports)
pushd android
./gradlew app:connectedAndroidTest \
  -Ptarget=integration_test/app_test.dart
popd

# ADB: capture logcat during test
adb logcat -c && adb logcat > test_logcat.txt &
flutter test integration_test/
kill %1
```

### Web (ChromeDriver)

```bash
# Start ChromeDriver (required before test)
chromedriver --port=4444 &

# Run web integration tests
flutter drive \
  --driver=test_driver/integration_test.dart \
  --target=integration_test/app_test.dart \
  -d web-server \
  --browser-name=chrome \
  --release

# Headless Chrome (for CI)
flutter drive \
  --driver=test_driver/integration_test.dart \
  --target=integration_test/app_test.dart \
  -d web-server \
  --browser-name=chrome \
  --chrome-binary=$(which google-chrome) \
  --headless
```

---

## STEP 7: CI/CD Integration


**Read:** `references/cicd-integration.md` for detailed step 7: ci/cd integration reference material.

# JUnit XML (Android Gradle)
pushd android && ./gradlew app:connectedAndroidTest \
  -Ptarget=integration_test/app_test.dart && popd
# Output: android/app/build/outputs/androidTest-results/

# JSON report
flutter test integration_test/ --reporter json > test_results.json

# Machine-readable for CI dashboards
flutter test integration_test/ --reporter github
```

---

## Troubleshooting

| Symptom | Likely Cause | Recovery |
|---------|-------------|----------|
| `No connected devices` | Emulator not running or USB debugging off | Run `flutter devices`; start emulator or enable USB debugging |
| `pumpAndSettle` times out | Infinite animation (spinner, shimmer) running | Use `pump(Duration)` instead; or wrap animations with a test flag to disable |
| `Finder returned zero widgets` | Widget not rendered yet or wrong key/label | Add `await tester.pumpAndSettle()` before finder; verify key string matches |
| `MissingPluginException` | Native plugin not registered in test harness | Use `setMockMethodCallHandler` for the channel or add the plugin to `integration_test/` |
| Screenshot mismatch (golden) | Font rendering differs across platforms | Use `loadAppFonts()` from `golden_toolkit`; pin OS version in CI |
| ChromeDriver connection refused | ChromeDriver not started or wrong port | Start `chromedriver --port=4444` before test run |
| Test passes locally, fails in CI | Timing differences, missing env setup | Increase `pumpAndSettle` timeout; ensure emulator/browser setup steps in CI |
| `setState() called after dispose()` | Async callback fires after screen transition | Guard with `mounted` check; use Riverpod for async state |
| Flaky scroll tests | Scroll delta too small or list length varies | Increase delta; use `maxScrolls` parameter; assert item count before scrolling |
| Android `INSTALL_FAILED_INSUFFICIENT_STORAGE` | Emulator disk full | Wipe emulator data: `emulator -avd <name> -wipe-data` |

---

## STEP 8: Structured JSON Output

Write machine-readable results to `test-results/flutter-e2e-test.json`:

```json
{
  "skill": "flutter-e2e-test",
  "result": "PASSED|FAILED",
  "timestamp": "<ISO-8601>",
  "tests_run": "<total_count>",
  "tests_failed": "<failed_count>",
  "failures": [
    {
      "test": "<test_description>",
      "category": "ASSERTION_FAILURE|WIDGET_NOT_FOUND|TIMEOUT|GOLDEN_MISMATCH|RUNTIME_ERROR",
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
    'skill': 'flutter-e2e-test',
    'result': '<PASSED_or_FAILED>',
    'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'tests_run': '<N>',
    'tests_failed': '<N>',
    'failures': []
}
with open('test-results/flutter-e2e-test.json', 'w') as f:
    json.dump(result, f, indent=2)
"
```

---

## CAPTURE PROOF MODE

When invoked with `--capture-proof`, capture a screenshot after every test
function, not just tests with explicit `matchesGoldenFile()` calls.

### Integration Test Pattern

```dart
// The tester-agent wraps each test's tearDown to capture:
tearDown(() async {
  final binding = IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  await binding.takeScreenshot('${testName}_${passed ? "pass" : "fail"}');
});
```

### Evidence Output

Screenshots stored in `test-evidence/{run_id}/screenshots/`:
`{test_name}.{pass|fail}.png`

Platform suffix added for multi-platform runs:
`{test_name}.{android|ios|web}.{pass|fail}.png`

---

## STEP 9: Auto-Fix and Learn (On Failure Only)

If tests failed in STEP 6, automatically invoke the fix-and-learn pipeline. Do NOT just report failures — fix them.

### 9a. Diagnose First (E2E-Specific)

Per Rule 15, E2E failures go through `/systematic-debugging` first because environment issues masquerade as code bugs:

```
Skill("systematic-debugging", args="Flutter E2E test failed: <failure_output>")
```

### 9b. Invoke Fix-Loop

Once root cause is isolated by systematic debugging:

```
Skill("fix-loop", args="<diagnosed_failure>\n\nretest_command: flutter test integration_test/{test_file}")
```

### 9c. Capture Learnings (On Fix Success)

If `/fix-loop` reports `result: PASSED` or `result: FIXED`:

```
Skill("learn-n-improve", args="session")
```

### 9d. Escalation (On Fix Failure)

If `/fix-loop` exhausts iterations without success:
- Report the failure to the user
- Do NOT silently continue

### Skip Conditions

Do NOT auto-invoke fix pipeline if:
- No connected device (`flutter devices` shows none)
- Build failed before tests ran (`flutter build` errors)
- ChromeDriver not started (web tests)

---

## Anti-Patterns

### MUST NOT DO

- **Brittle selectors**: Use `find.byType(ElevatedButton)` or `find.text('Submit')` as primary locators. Use `find.byKey()` or `find.bySemanticsLabel()` instead -- they survive widget type changes and text edits.
- **Hardcoded waits**: Use `await Future.delayed(Duration(seconds: 3))` to wait for UI. Use `await tester.pumpAndSettle()` or `pump(Duration)` instead -- they respond to actual frame rendering.
- **Test interdependence**: Rely on test A's state for test B to pass. Use `setUp` / `tearDown` to reset state -- each test MUST start from a clean app launch.
- **Coordinate-based taps**: Use `tester.tapAt(Offset(150, 300))` for element interaction. Use semantic finders instead -- coordinates break across screen sizes.
- **Ignoring error states**: Only test the happy path. Test error states, empty states, and edge cases -- these are where production crashes hide.
- **Giant monolithic tests**: Write one test that covers the entire app flow. Split into focused feature tests -- failures pinpoint the broken feature.
- **Skipping CI integration**: Run E2E tests only locally. Configure headless execution in CI -- tests that don't run automatically are tests that rot.

### MUST DO

- Invoke `/fix-loop` on test failure — do not just report failures
- Annotate interactive widgets with `Semantics` labels and `Key` values at development time
- Use the robot/page-object pattern to encapsulate screen interactions
- Batch 5+ sequential actions into helper methods for token efficiency
- Run with `--reporter expanded` locally for readable output
- Capture screenshots on failure for debugging
- Use deterministic seeds for any randomized testing (monkey tests)
- Pin Flutter and emulator versions in CI for reproducibility
