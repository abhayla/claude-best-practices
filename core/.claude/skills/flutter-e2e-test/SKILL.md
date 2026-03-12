---
name: flutter-e2e-test
description: >
  Flutter E2E testing across Android, Web, and desktop platforms. MCP-based semantic
  element recognition, integration_test package workflows, self-healing selectors,
  visual regression, monkey testing, and CI/CD integration. Based on ai-dashboad/flutter-skill.
triggers: "flutter test, e2e, integration test, end-to-end, widget test, UI test"
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "<test-scope: 'all' | feature-name | 'setup' | 'visual' | 'monkey'>"
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

### Finding Elements by Semantics (Self-Healing)

Use semantic labels and keys instead of text or widget type. Semantic finders survive UI refactors because they bind to meaning, not structure.

```dart
// GOOD: Semantic-based — survives widget type changes
find.bySemanticsLabel('Email input');
find.bySemanticsLabel(RegExp(r'Submit'));
find.byKey(const Key('login_button'));

// BAD: Brittle — breaks when text or widget type changes
find.text('Submit');
find.byType(ElevatedButton);
```

### Annotating Widgets for Testability

```dart
Semantics(
  label: 'Email input',
  child: TextField(
    key: const Key('email_field'),
    decoration: const InputDecoration(labelText: 'Email'),
  ),
)
```

### Core Interactions

```dart
// Tap
await tester.tap(find.byKey(const Key('login_button')));
await tester.pumpAndSettle();

// Enter text
await tester.enterText(find.byKey(const Key('email_field')), 'user@test.com');

// Scroll until visible
await tester.scrollUntilVisible(
  find.byKey(const Key('item_42')),
  200.0,  // scroll delta
  scrollable: find.byType(Scrollable),
);

// Swipe / drag
await tester.drag(find.byKey(const Key('dismissible_card')), const Offset(-300, 0));
await tester.pumpAndSettle();

// Long press
await tester.longPress(find.bySemanticsLabel('Context menu target'));
await tester.pumpAndSettle();
```

### Batch Operations (Token Efficiency)

Group 5+ sequential actions into helper methods to reduce token usage and improve readability.

```dart
/// Robot pattern: batch login actions into a single call
class LoginRobot {
  final WidgetTester tester;
  const LoginRobot(this.tester);

  Future<void> login({
    required String email,
    required String password,
  }) async {
    await tester.enterText(find.byKey(const Key('email_field')), email);
    await tester.enterText(find.byKey(const Key('password_field')), password);
    await tester.tap(find.byKey(const Key('login_button')));
    await tester.pumpAndSettle(const Duration(seconds: 3));
    expect(find.byKey(const Key('home_screen')), findsOneWidget);
  }
}
```

### MCP-Based Semantic Element Recognition

When using MCP tools that expose the accessibility tree, query elements by their semantic role rather than coordinates or indices.

```dart
// Accessibility tree approach: query by role + label
// The MCP server exposes the Flutter accessibility tree as a structured object.
// Use SemanticsNode queries to locate elements by role, label, and value.

import 'package:flutter/rendering.dart';

SemanticsNode findNodeByLabel(SemanticsNode root, String label) {
  if (root.label == label) return root;
  for (final child in root.debugListChildrenInOrder(DebugSemanticsDumpOrder.traversalOrder)) {
    final result = findNodeByLabel(child, label);
    if (result.label == label) return result;
  }
  throw StateError('No SemanticsNode with label "$label"');
}
```

---

## STEP 3: Test Patterns

### Login Flow

```dart
testWidgets('complete login flow', (tester) async {
  final binding = IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  await tester.pumpWidget(const ProviderScope(child: MyApp()));
  await tester.pumpAndSettle();

  final loginRobot = LoginRobot(tester);
  await loginRobot.login(email: 'test@example.com', password: 'Passw0rd!');

  // Verify landed on home
  expect(find.bySemanticsLabel('Home screen'), findsOneWidget);
});
```

### Navigation Flow

```dart
testWidgets('bottom nav switches screens', (tester) async {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  await tester.pumpWidget(const ProviderScope(child: MyApp()));
  await tester.pumpAndSettle();

  // Navigate to settings
  await tester.tap(find.byKey(const Key('nav_settings')));
  await tester.pumpAndSettle();
  expect(find.byKey(const Key('settings_screen')), findsOneWidget);

  // Navigate back to home
  await tester.tap(find.byKey(const Key('nav_home')));
  await tester.pumpAndSettle();
  expect(find.byKey(const Key('home_screen')), findsOneWidget);
});
```

### Form Submission with Validation

```dart
testWidgets('form shows validation errors then submits', (tester) async {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  await tester.pumpWidget(const ProviderScope(child: MyApp()));
  await tester.pumpAndSettle();

  // Submit empty form — expect errors
  await tester.tap(find.byKey(const Key('submit_button')));
  await tester.pumpAndSettle();
  expect(find.text('Required field'), findsWidgets);

  // Fill valid data and submit
  await tester.enterText(find.byKey(const Key('name_field')), 'Jane Doe');
  await tester.enterText(find.byKey(const Key('email_field')), 'jane@test.com');
  await tester.tap(find.byKey(const Key('submit_button')));
  await tester.pumpAndSettle();
  expect(find.text('Success'), findsOneWidget);
});
```

### List Scrolling

```dart
testWidgets('scrolls to item and taps it', (tester) async {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  await tester.pumpWidget(const ProviderScope(child: MyApp()));
  await tester.pumpAndSettle();

  await tester.scrollUntilVisible(
    find.byKey(const Key('list_item_25')),
    300.0,
    scrollable: find.byType(Scrollable).first,
    maxScrolls: 50,
  );
  await tester.tap(find.byKey(const Key('list_item_25')));
  await tester.pumpAndSettle();
  expect(find.byKey(const Key('detail_screen')), findsOneWidget);
});
```

### Error State Handling

```dart
testWidgets('displays error state and retries', (tester) async {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  // Set up mock to fail first, succeed on retry
  await tester.pumpWidget(const ProviderScope(child: MyApp()));
  await tester.pumpAndSettle();

  // Verify error state is shown
  expect(find.bySemanticsLabel('Error message'), findsOneWidget);
  expect(find.byKey(const Key('retry_button')), findsOneWidget);

  // Tap retry
  await tester.tap(find.byKey(const Key('retry_button')));
  await tester.pumpAndSettle(const Duration(seconds: 5));
  expect(find.byKey(const Key('content_loaded')), findsOneWidget);
});
```

---

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

---

## STEP 5: Monkey / Fuzz Testing

Randomly interact with the app to discover crashes and unhandled exceptions.

```dart
testWidgets('monkey test — random interactions for 60s', (tester) async {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  await tester.pumpWidget(const ProviderScope(child: MyApp()));
  await tester.pumpAndSettle();

  final random = Random(42); // Deterministic seed for reproducibility
  final stopwatch = Stopwatch()..start();
  var actions = 0;

  while (stopwatch.elapsed < const Duration(seconds: 60)) {
    try {
      final size = tester.view.physicalSize / tester.view.devicePixelRatio;
      final x = random.nextDouble() * size.width;
      final y = random.nextDouble() * size.height;

      switch (random.nextInt(4)) {
        case 0: // Tap at random location
          await tester.tapAt(Offset(x, y));
          break;
        case 1: // Drag gesture
          await tester.dragFrom(Offset(x, y), Offset(
            (random.nextDouble() - 0.5) * 200,
            (random.nextDouble() - 0.5) * 200,
          ));
          break;
        case 2: // Enter text if text field focused
          await tester.enterText(find.byType(EditableText).first, 'fuzz${random.nextInt(999)}');
          break;
        case 3: // Back navigation
          final backButton = find.byTooltip('Back');
          if (backButton.evaluate().isNotEmpty) {
            await tester.tap(backButton);
          }
          break;
      }
      await tester.pumpAndSettle(const Duration(milliseconds: 100));
      actions++;
    } catch (e) {
      // Log but continue — monkey testing should be resilient
      debugPrint('Monkey action $actions failed: $e');
      await tester.pumpAndSettle();
    }
  }

  debugPrint('Monkey test completed: $actions actions in ${stopwatch.elapsed}');
});
```

---

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

### GitHub Actions Example

```yaml
name: Flutter E2E Tests

on: [push, pull_request]

jobs:
  e2e-android:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: subosito/flutter-action@v2
        with:
          flutter-version: '3.24.x'
          channel: stable

      - name: Install dependencies
        run: flutter pub get

      - name: Enable KVM
        run: |
          echo 'KERNEL=="kvm", GROUP="kvm", MODE="0666"' | sudo tee /etc/udev/rules.d/99-kvm4all.rules
          sudo udevadm control --reload-rules
          sudo udevadm trigger --name-match=kvm

      - name: Run E2E tests on Android
        uses: reactivecircus/android-emulator-runner@v2
        with:
          api-level: 34
          arch: x86_64
          script: flutter test integration_test/ --reporter github

      - name: Upload screenshots
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: e2e-screenshots
          path: build/screenshots/

  e2e-web:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: subosito/flutter-action@v2
        with:
          flutter-version: '3.24.x'
      - uses: browser-actions/setup-chrome@v1
      - uses: nanasess/setup-chromedriver@v2

      - run: flutter pub get

      - name: Run E2E tests on Web
        run: |
          chromedriver --port=4444 &
          flutter drive \
            --driver=test_driver/integration_test.dart \
            --target=integration_test/app_test.dart \
            -d web-server \
            --browser-name=chrome \
            --headless
```

### Generating Reports

```bash
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

- Annotate interactive widgets with `Semantics` labels and `Key` values at development time
- Use the robot/page-object pattern to encapsulate screen interactions
- Batch 5+ sequential actions into helper methods for token efficiency
- Run with `--reporter expanded` locally for readable output
- Capture screenshots on failure for debugging
- Use deterministic seeds for any randomized testing (monkey tests)
- Pin Flutter and emulator versions in CI for reproducibility
