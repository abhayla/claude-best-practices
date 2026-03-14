---
name: cross-platform-visual
description: >
  Cross-platform visual consistency checking. Captures the same screen/feature across
  Android, Web, and Flutter, compares them for visual parity, and flags divergence.
  Use to verify design consistency across platforms.
allowed-tools: "Bash Read Grep Glob"
triggers:
  - cross platform visual
  - visual consistency
  - platform comparison
  - design parity
argument-hint: "<feature-name|screen-name> [--platforms android,web,flutter] [--threshold=N]"
---

# Cross-Platform Visual Consistency

Compare the same UI feature across Android, Web, and Flutter to ensure design parity.

**Arguments:** $ARGUMENTS

---

## STEP 1: Identify Target Screens

Determine which screens/features to compare:

1. Parse the feature name from arguments
2. Map to platform-specific test paths:
   - Android: `e2e/maestro/{feature}/` or Espresso test class
   - Web: `e2e/tests/{feature}.spec.ts` (Playwright)
   - Flutter: `integration_test/{feature}_test.dart`

## STEP 2: Capture Screenshots Per Platform

### Android (Maestro)

```bash
# Run the feature flow and capture screenshot
maestro test e2e/maestro/{feature}/ --debug-output=e2e/output/{feature}
# Screenshot saved to: e2e/output/{feature}/screenshots/
```

### Web (Playwright)

```bash
# Run the feature test with screenshot capture
npx playwright test e2e/tests/{feature}.spec.ts --update-snapshots
# Screenshots saved to: e2e/__screenshots__/{browser}/{feature}/
```

### Flutter

```bash
# Run golden test for the feature
flutter test integration_test/{feature}_test.dart --update-goldens
# Screenshots saved to: test/goldens/{feature}/
```

## STEP 3: Normalize Screenshots

Before comparison, normalize screenshots to account for expected platform differences:

1. **Resize** — Scale all screenshots to the same logical resolution (e.g., 375x812 logical pixels)
2. **Crop** — Remove platform-specific chrome (status bar, navigation bar, browser toolbar)
3. **Note inherent differences** — Platform-native widgets (date pickers, dropdowns, toggles) will always differ; focus comparison on custom UI elements

### Expected Platform Differences (NOT flagged)

| Element | Why It Differs | Action |
|---------|---------------|--------|
| Status bar (time, battery, signal) | OS-level rendering | Crop from comparison |
| Navigation bar / back button | Platform convention | Crop from comparison |
| Native form controls | Platform-native styling | Mask or skip |
| Font rendering / anti-aliasing | OS font engine | Use tolerant threshold |
| Scrollbar appearance | Platform convention | Mask scrollbar region |

## STEP 4: Visual Comparison

Use multimodal Read to compare screenshots across platforms:

1. Read all platform screenshots for the same screen
2. Compare layout, spacing, colors, typography, and component placement
3. Flag significant divergences:

### Comparison Criteria

| Criterion | Weight | Description |
|-----------|--------|-------------|
| Layout structure | HIGH | Same arrangement of elements, same grid/flex layout |
| Color palette | HIGH | Same brand colors, same contrast ratios |
| Typography | MEDIUM | Same font sizes, weights, line heights (font family may differ) |
| Spacing / padding | MEDIUM | Consistent margins and padding across platforms |
| Component presence | HIGH | All platforms show the same UI components |
| Interactive states | LOW | Hover/pressed states may differ by platform convention |

### Divergence Levels

| Level | Description | Action |
|-------|-------------|--------|
| **MATCH** | Screens are visually consistent across platforms | Pass |
| **MINOR** | Small differences in font rendering, sub-pixel alignment | Pass with note |
| **MODERATE** | Noticeable spacing, color, or sizing differences | Flag for design review |
| **MAJOR** | Missing components, wrong layout, broken design | Fail — file issue |

## STEP 5: Report

```
Cross-Platform Visual Consistency: [CONSISTENT / DIVERGENT]
  Feature: {feature-name}
  Platforms compared: Android, Web, Flutter

  Per-screen results:
    login_screen:
      Android ↔ Web: MATCH
      Android ↔ Flutter: MINOR (font rendering difference)
      Web ↔ Flutter: MATCH

    dashboard:
      Android ↔ Web: MAJOR — sidebar missing on Android
      Android ↔ Flutter: MODERATE — spacing differs in card grid
      Web ↔ Flutter: MATCH

  Action items:
    - [MAJOR] dashboard: Android missing sidebar — file issue
    - [MODERATE] dashboard: Android card grid spacing — flag for design review
```

## STEP 6: Baseline Storage

Store cross-platform comparison baselines:

```
tests/visual/
  cross-platform/
    {feature}/
      android.png
      web.png
      flutter.png
      comparison-report.json
```

```json
// comparison-report.json
{
  "feature": "login_screen",
  "timestamp": "2026-03-14T10:00:00Z",
  "comparisons": [
    {"a": "android", "b": "web", "result": "MATCH"},
    {"a": "android", "b": "flutter", "result": "MINOR", "note": "font rendering"},
    {"a": "web", "b": "flutter", "result": "MATCH"}
  ]
}
```

## RULES

- Compare custom UI elements only — platform-native controls are expected to differ
- Always crop platform chrome (status bar, nav bar) before comparison
- Use MAJOR divergence only for missing components or broken layouts
- Font rendering and sub-pixel differences are MINOR at most
- Run after any design system change that affects multiple platforms
- This skill complements per-platform visual regression (Playwright, Maestro, Flutter goldens) — it checks cross-platform parity, not within-platform regression
