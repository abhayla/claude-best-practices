---
name: mobile-a11y-test
description: >
  Run mobile accessibility tests for Android (Compose/XML) and Flutter projects.
  Detects platform, runs automated checks, audits content labels, validates touch
  targets, checks color contrast, and produces a structured severity report.
  CRITICAL: every interactive element MUST have an accessibility label and meet
  48dp minimum touch target.
triggers:
  - mobile accessibility
  - android a11y
  - flutter accessibility
  - talkback
  - semantics test
  - accessibility scanner
allowed-tools: "Bash Read Grep Glob"
argument-hint: "[--platform android|flutter] [--scope screen|app] [--dark-mode]"
version: "1.0.0"
type: workflow
---

# Mobile Accessibility Testing

Run automated and semi-automated accessibility checks for Android and Flutter projects.

**Arguments:** $ARGUMENTS

CRITICAL: Every interactive element (buttons, links, inputs, toggles) MUST have an accessibility label AND a touch target of at least 48dp.

---

## STEP 1: Detect Platform

| Indicator | Platform | Test Approach |
|-----------|----------|---------------|
| `build.gradle.kts` / `build.gradle` with `com.android.*` | Android | Espresso + Compose semantics |
| `pubspec.yaml` with `flutter` dependency | Flutter | Semantics tree + flutter test |
| Both present | Hybrid | Run both pipelines |

```bash
# Detect Android
for dir in android app .; do
  [ -f "$dir/build.gradle.kts" ] || [ -f "$dir/build.gradle" ] && echo "Android: $dir" && break
done
# Detect Flutter
[ -f "pubspec.yaml" ] && grep -q "flutter:" pubspec.yaml && echo "Flutter detected"
# Compose vs XML
grep -rl "@Composable" --include="*.kt" src/ app/src/ 2>/dev/null | head -3
find . -path "*/res/layout/*.xml" -type f 2>/dev/null | head -3
```

If `--platform` is provided, skip detection. Record `PLATFORM` and `ANDROID_DIR` for subsequent steps.

---

## STEP 2: Automated Checks

### Android: Espresso AccessibilityChecks

```kotlin
@Before
fun setUp() {
    AccessibilityChecks.enable().apply { setRunChecksFromRootView(true) }
}

@Test
fun screen_passesAccessibilityChecks() {
    onView(withId(R.id.action_button)).perform(click())
    // Test FAILS automatically if any a11y violation is detected
}
```

```bash
cd $ANDROID_DIR && ./gradlew :app:connectedDebugAndroidTest \
  -Pandroid.testInstrumentationRunnerArguments.class=com.example.<YourA11yTest>
```

### Android: Compose Semantics Assertions

```kotlin
@get:Rule val composeTestRule = createComposeRule()

@Test
fun interactiveElements_haveContentDescriptions() {
    composeTestRule.setContent { YourScreen() }
    composeTestRule.onNodeWithContentDescription("Submit form")
        .assertExists().assertIsDisplayed()
    composeTestRule.onNode(hasClickAction()).assert(hasContentDescription())
}

@Test
fun buttons_meetTouchTargetSize() {
    composeTestRule.setContent { YourScreen() }
    composeTestRule.onNode(hasClickAction())
        .assertTouchHeightIsAtLeast(48.dp)
        .assertTouchWidthIsAtLeast(48.dp)
}
```

### Android: Accessibility Scanner (ADB)

```bash
adb shell uiautomator dump /sdcard/a11y_tree.xml && adb pull /sdcard/a11y_tree.xml
grep -E 'clickable="true"' a11y_tree.xml | grep -E 'content-desc=""'
rm -f a11y_tree.xml && adb shell rm -f /sdcard/a11y_tree.xml
```

### Flutter: Semantics Tree Validation

```dart
testWidgets('interactive widgets have semantics labels', (tester) async {
  await tester.pumpWidget(const MyApp());
  expect(find.bySemanticsLabel('Submit'), findsOneWidget);
  final tappable = find.byWidgetPredicate(
    (w) => w is GestureDetector || w is InkWell,
  );
  for (final element in tappable.evaluate()) {
    final semantics = element.renderObject?.debugSemantics;
    expect(semantics?.label, isNotEmpty,
        reason: '${element.widget.runtimeType} missing semantics label');
  }
});
```

### Flutter: Golden Accessibility Tests

```dart
testWidgets('screen meets a11y guidelines', (tester) async {
  final handle = tester.ensureSemantics();
  await tester.pumpWidget(const MyApp());
  await expectLater(tester, meetsGuideline(textContrastGuideline));
  await expectLater(tester, meetsGuideline(labeledTapTargetGuideline));
  await expectLater(tester, meetsGuideline(androidTapTargetGuideline));
  handle.dispose();
});
```

```bash
flutter test --tags accessibility
```

---

## STEP 3: Content Description Audit

### Android: Scan for Missing Labels

```bash
# Compose: clickable without semantics
grep -rn "\.clickable\|\.toggleable\|\.selectable" --include="*.kt" src/ app/src/ \
  | grep -v "contentDescription\|semantics\|clearAndSetSemantics"
# XML: clickable without contentDescription
grep -rn 'android:clickable="true"\|android:onClick=' --include="*.xml" src/ app/src/ res/ \
  | grep -v "android:contentDescription"
# Images without contentDescription
grep -rn "ImageView\|ImageButton\|Icon(" --include="*.xml" --include="*.kt" src/ app/src/ \
  | grep -v "contentDescription\|importantForAccessibility.*no"
```

**Compose patterns** -- CORRECT: `Icon(Icons.Default.Delete, contentDescription = "Delete item")`. Decorative: `contentDescription = null`. Custom: `Modifier.semantics { contentDescription = "action" }`. WRONG: `Modifier.clickable { }` without any semantics.

### Flutter: Scan for Missing Labels

```bash
# GestureDetector/InkWell without Semantics
grep -rn "GestureDetector\|InkWell" --include="*.dart" lib/ | grep -v "Semantics\|semanticsLabel\|Tooltip"
# Images without semanticLabel
grep -rn "Image\.asset\|Image\.network" --include="*.dart" lib/ | grep -v "semanticLabel\|excludeFromSemantics"
# IconButton without tooltip
grep -rn "IconButton(" --include="*.dart" lib/ | grep -v "tooltip:"
```

**Flutter patterns** -- CORRECT: `Semantics(label: 'Delete', button: true, child: GestureDetector(...))`. Decorative: `Image.asset('bg.png', excludeFromSemantics: true)`. WRONG: bare `GestureDetector` without `Semantics` wrapper.

---

## STEP 4: Touch Target Validation

Minimum 48dp touch target (WCAG 2.5.8, Material Design guideline).

### Android

```bash
# XML: small sizes on clickable elements
grep -rn "layout_width=\"[0-3][0-9]dp\"\|layout_height=\"[0-3][0-9]dp\"" \
  --include="*.xml" src/ app/src/ res/ | grep -i "button\|click\|image"
# Compose: clickable without minimumInteractiveComponentSize
grep -rn "\.clickable\|\.toggleable" --include="*.kt" src/ app/src/ \
  | grep -v "minimumInteractiveComponentSize"
```

CORRECT: `Modifier.minimumInteractiveComponentSize().clickable { }`. Material3 `Button`, `IconButton` auto-apply 48dp. WRONG: `Modifier.size(24.dp).clickable { }`.

### Flutter

```bash
grep -rn "SizedBox(\|Container(" --include="*.dart" lib/ -A 3 \
  | grep -E "height: [0-3][0-9]|width: [0-3][0-9]"
```

CORRECT: `ConstrainedBox(constraints: BoxConstraints(minWidth: 48, minHeight: 48), child: GestureDetector(...))`. Material `IconButton` has 48dp built-in. WRONG: `SizedBox(width: 24, height: 24)` wrapping a `GestureDetector`.

---

## STEP 5: Color Contrast Check

| Content Type | Minimum Ratio (WCAG AA) |
|-------------|------------------------|
| Normal text (< 18sp / 14sp bold) | 4.5:1 |
| Large text (>= 18sp / 14sp bold) | 3:1 |
| UI components and graphics | 3:1 |

### Android

```bash
# Extract theme colors
grep -rn "colorPrimary\|colorOnPrimary\|textColor\|background" \
  --include="*.xml" --include="*.kt" src/ app/src/ res/ | grep -E "#[0-9A-Fa-f]{6,8}"
# Hardcoded colors bypassing theme
grep -rn "Color.White\|Color.Black\|Color(0xFF" --include="*.kt" src/ app/src/ \
  | grep -v "MaterialTheme\|Theme\|// theme-ok"
# Dark theme exists?
grep -rn "darkColorScheme\|DarkColorPalette\|night/colors" --include="*.kt" --include="*.xml" src/ app/src/ res/
```

Verify `on*` colors contrast against their paired surface: `onPrimary/primary`, `onSurface/surface`, `onBackground/background` -- all must meet 4.5:1.

### Flutter

```bash
grep -rn "Color(0x\|Colors\.\|Color\.fromRGBO" --include="*.dart" lib/ \
  | grep -v "ThemeData\|colorScheme\|// contrast-ok"
grep -rn "darkTheme\|brightness: Brightness.dark" --include="*.dart" lib/
```

Use `textContrastGuideline` from Flutter test framework (Step 2) for programmatic validation.

---

## STEP 6: Screen Reader Testing

### TalkBack (Android) / VoiceOver (Flutter iOS)

| Check | How to Verify | Pass Criteria |
|-------|--------------|---------------|
| Focus order | Swipe right through screen | Logical reading order |
| Element labels | Listen to announcements | Every interactive element has meaningful label |
| State changes | Toggle switches, expand sections | State announced ("checked", "expanded") |
| Headings | Navigate by headings | Sections reachable via heading navigation |
| Custom actions | Long-press (TalkBack) / swipe up-down (VO) | Actions available |

### Compose: Focus Order and Custom Actions

```kotlin
Text("Title", modifier = Modifier.semantics { heading() })
Button(onClick = { }, modifier = Modifier.semantics {
    stateDescription = if (isExpanded) "Expanded" else "Collapsed"
    customActions = listOf(
        CustomAccessibilityAction("Expand") { onExpand(); true }
    )
}) { Text("Details") }
// Merge semantics for compound components
Row(modifier = Modifier.semantics(mergeDescendants = true) {
    contentDescription = "Item: $name, price: $$price"
}) { Text(name); Text("$$price") }
```

### Espresso: Focus Assertions

```kotlin
onView(withId(R.id.title)).check(matches(isAccessibilityFocused()))
onView(withId(R.id.action_button))
    .check(matches(withContentDescription(not(isEmptyString()))))
```

### Flutter: Semantics Assertions

```dart
expect(find.bySemanticsLabel('Section Title'), matchesSemantics(isHeader: true));
expect(find.bySemanticsLabel('Submit'), matchesSemantics(
  isButton: true, isFocusable: true, hasEnabledState: true, isEnabled: true,
));
Semantics(label: 'Product card', value: '\$$price', hint: 'Double tap to view', child: card)
```

---

## STEP 7: Report

```
MOBILE ACCESSIBILITY REPORT
==============================
Platform: <Android (Compose/XML) | Flutter | Hybrid>
Scope: <screen name or "full app">
Date: <date>
Dark Mode Tested: <Yes | No>

CRITICAL (blocks screen reader users)
| # | Issue | Location | WCAG | Fix |
|---|-------|----------|------|-----|

MAJOR (significant barriers)
| # | Issue | Location | WCAG | Fix |
|---|-------|----------|------|-----|

MINOR (improvements)
| # | Issue | Location | WCAG | Fix |
|---|-------|----------|------|-----|

SUMMARY: Critical: N | Major: N | Minor: N
VERDICT: <PASS | FAIL>
  PASS = zero critical AND zero major
  FAIL = any critical OR major findings
```

| Severity | Criteria | Action |
|----------|----------|--------|
| Critical | Blocks screen readers (no label, unreachable element) | MUST fix before release |
| Major | Significant barrier (low contrast, wrong focus order) | MUST fix before release |
| Minor | Improvement (missing hints, decorative images not excluded) | SHOULD fix, can defer |

---

## MUST DO

- Detect the platform before running checks -- do not assume Android or Flutter
- Check BOTH content labels AND touch target sizes -- the two most common failures
- Verify dark mode contrast if the project has a dark theme
- Map every finding to a specific WCAG success criterion
- Provide a concrete fix (code snippet or modifier) for every finding
- Check Compose `semantics {}` blocks, not just `contentDescription`
- Run `meetsGuideline(labeledTapTargetGuideline)` in Flutter golden tests
- Verify screen reader focus order matches visual reading order
- Mark decorative images explicitly (`contentDescription = null` / `excludeFromSemantics: true`)

## MUST NOT DO

- MUST NOT treat missing `contentDescription` as the only issue -- touch targets, contrast, and focus order are equally critical
- MUST NOT skip dark mode testing -- contrast issues frequently appear only in dark themes
- MUST NOT assume Material components are automatically accessible -- custom styling can break built-in a11y
- MUST NOT use generic labels like "button" or "image" -- labels must describe the action or content
- MUST NOT merge semantics on elements that should be individually focusable
- MUST NOT hardcode colors outside the theme system -- use `MaterialTheme.colorScheme` (Compose) or `Theme.of(context)` (Flutter)
- MUST NOT ignore `importantForAccessibility` / `excludeFromSemantics` -- decorative elements must be explicitly excluded
- MUST NOT report PASS if any critical or major findings remain unresolved
