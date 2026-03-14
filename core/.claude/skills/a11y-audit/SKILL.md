---
name: a11y-audit
description: >
  Run automated WCAG 2.1 AA compliance checks using axe-core (via Playwright)
  and Lighthouse accessibility scoring. Produces a structured report with
  severity, WCAG criterion, affected element, and fix suggestion for each
  violation. Use for prototype demos, staging reviews, or production page audits.
triggers:
  - a11y-audit
  - accessibility audit
  - wcag check
  - accessibility check
allowed-tools: "Bash Read Write Edit Grep Glob"
argument-hint: "<URL or path/to/file.html> [--scope page|site] [--threshold 90]"
---

# Accessibility Audit (WCAG 2.1 AA)

Run automated WCAG 2.1 AA compliance checks combining axe-core, Lighthouse, and a manual checklist.

**Target:** $ARGUMENTS

---

## STEP 1: Detect Target

| Input | Action |
|-------|--------|
| `http://` or `https://` URL | Use directly |
| `.html` / `.htm` file | Serve locally: `npx serve . -l 3000 &` then use `http://localhost:3000` |
| Directory path | Serve directory, scan each `.html` file |
| None provided | Look for `index.html`, `dist/`, `build/`, or running dev server |

Record `TARGET_URL=<resolved URL>` for subsequent steps.

---

## STEP 2: Run axe-core via Playwright

```bash
npm ls @axe-core/playwright 2>/dev/null || npm install --save-dev @axe-core/playwright @playwright/test
npx playwright install chromium --with-deps 2>/dev/null || npx playwright install chromium
```

Create `a11y-axe-audit.mjs`:

```javascript
import { chromium } from 'playwright';
import AxeBuilder from '@axe-core/playwright';
const url = process.argv[2] || 'http://localhost:3000';
(async () => {
  const browser = await chromium.launch();
  const page = await (await browser.newContext()).newPage();
  await page.goto(url, { waitUntil: 'networkidle' });
  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa'])
    .analyze();
  console.log(JSON.stringify(results, null, 2));
  await browser.close();
})();
```

```bash
node a11y-axe-audit.mjs "$TARGET_URL" > axe-results.json
```

Parse violations from `axe-results.json`: extract each violation's `impact`, `id`, `description`, WCAG tags, and affected `nodes[].html`.

---

## STEP 3: Run Lighthouse Accessibility Audit

```bash
npx lighthouse "$TARGET_URL" \
  --only-categories=accessibility \
  --output=json --output-path=./lighthouse-a11y.json \
  --chrome-flags="--headless --no-sandbox" --quiet
```

Extract the accessibility score (`categories.accessibility.score * 100`) and all failing audits (`score === 0`) with their affected elements.

Record `LIGHTHOUSE_SCORE=<score>`.

---

## STEP 4: Manual WCAG 2.1 AA Checklist

Automated tools catch ~30-40% of issues. Manually verify these key criteria:

### Color & Visual

| Criterion | Check |
|-----------|-------|
| 1.4.3 Contrast (Minimum) | Text: 4.5:1 ratio; large text: 3:1 ratio |
| 1.4.11 Non-text Contrast | UI components and graphics: 3:1 ratio |
| 1.4.4 Resize Text | Usable at 200% zoom, no `overflow: hidden` clipping |

### Keyboard & Focus

| Criterion | Check |
|-----------|-------|
| 2.1.1 Keyboard | All interactive elements reachable via Tab |
| 2.1.2 No Keyboard Trap | Focus can leave every component (modals, dropdowns) |
| 2.4.3 Focus Order | Tab order matches visual reading order |
| 2.4.7 Focus Visible | Visible `:focus` indicator on all interactive elements |

### Text Alternatives & Structure

| Criterion | Check |
|-----------|-------|
| 1.1.1 Non-text Content | Images have meaningful `alt` (or `alt=""` for decorative) |
| 1.3.1 Info and Relationships | Headings use `<h1>`-`<h6>`, lists use `<ul>`/`<ol>`, tables use `<th>` |
| 1.3.1 Heading Structure | Heading levels do not skip (no `<h1>` to `<h3>`) |

### ARIA & Forms

| Criterion | Check |
|-----------|-------|
| 4.1.2 Name, Role, Value | Custom widgets expose name, role, state via ARIA |
| 3.3.2 Labels or Instructions | Every input has a visible `<label>`, not just placeholder |
| 3.3.1 Error Identification | Errors described in text, not color alone |
| 1.3.5 Identify Input Purpose | Login/address forms use `autocomplete` attributes |

Mark each: PASS, FAIL (with element/location), or N/A.

---

## STEP 5: Generate Compliance Report

```
ACCESSIBILITY AUDIT REPORT
============================
Target: <URL or file path>
Date: <date>
Standard: WCAG 2.1 Level AA
Lighthouse Score: <score>/100
axe-core Violations: <count>
Manual Checklist: <pass>/<total> passed

AUTOMATED FINDINGS (axe-core + Lighthouse)
| # | Severity | WCAG Criterion | Rule | Element | Fix |
|---|----------|---------------|------|---------|-----|
| 1 | Critical | 1.1.1 | image-alt | <img src="hero.jpg"> | Add descriptive alt |
| 2 | Serious  | 1.4.3 | color-contrast | <p class="muted"> | Meet 4.5:1 ratio |

MANUAL FINDINGS
| # | Severity | WCAG Criterion | Issue | Location | Fix |
|---|----------|---------------|-------|----------|-----|
| M1 | Serious | 2.4.7 | No focus indicator | nav > a | Add :focus-visible outline |

SUMMARY: Critical: N | Serious: N | Moderate: N | Minor: N
VERDICT: <PASS | PARTIAL | FAIL>
  PASS = score >= threshold AND zero critical/serious
  PARTIAL = score >= threshold but serious violations remain
  FAIL = score < threshold OR critical violations present
```

### Severity Mapping

| axe-core Impact | Severity | Action |
|-----------------|----------|--------|
| critical | Critical | MUST fix — blocks release |
| serious | Serious | MUST fix — blocks release |
| moderate | Moderate | SHOULD fix — defer only with tracking |
| minor | Minor | NICE TO FIX — can defer |

---

## STEP 6: Suggest Fixes

| Violation | Fix Pattern |
|-----------|-------------|
| Missing `alt` on `<img>` | `alt="description"` for informative; `alt=""` for decorative |
| Low color contrast | Increase foreground darkness or background lightness to 4.5:1 |
| Missing form label | Add `<label for="id">` or `aria-label` |
| No focus indicator | `:focus-visible { outline: 2px solid #005fcc; outline-offset: 2px; }` |
| Missing button name | Add text content, `aria-label`, or `aria-labelledby` |
| Heading level skip | Restructure to sequential order (`h1` > `h2` > `h3`) |
| Missing landmarks | Wrap in `<main>`, `<nav>`, `<header>`, `<footer>` |
| Missing `lang` | Add `lang="en"` to `<html>` |
| Non-keyboard widget | Add `tabindex="0"`, keyboard handlers, and ARIA role |
| ARIA misuse | Remove invalid `aria-*`; match `role` to actual behavior |

After the audit, clean up: `rm -f a11y-axe-audit.mjs axe-results.json lighthouse-a11y.json`

---

## MOBILE ACCESSIBILITY TESTING

### Android — Espresso AccessibilityChecks

Enable automated accessibility checks in Espresso instrumented tests:

```kotlin
// In test setup — enables a11y checks on every ViewAction
@Before
fun setUp() {
    AccessibilityChecks.enable().apply {
        setRunChecksFromRootView(true)  // Check entire view hierarchy
        // Optional: suppress known issues during migration
        // setSuppressingResultMatcher(
        //     anyOf(
        //         matchesCheck(SpeakableTextPresentCheck::class.java),
        //         matchesCheck(TouchTargetSizeCheck::class.java)
        //     )
        // )
    }
}

@Test
fun loginScreen_passesAccessibilityChecks() {
    // Every Espresso ViewAction now automatically runs a11y checks
    onView(withId(R.id.email_field)).perform(typeText("test@example.com"))
    onView(withId(R.id.login_button)).perform(click())
    // If any a11y violation found → test FAILS automatically
}
```

```bash
# Run with accessibility checks enabled
cd android && ./gradlew :app:connectedDebugAndroidTest \
  -Pandroid.testInstrumentationRunnerArguments.class=com.example.LoginA11yTest
```

### Android — Accessibility Scanner CLI

```bash
# Dump accessibility node tree for analysis
adb shell uiautomator dump /sdcard/a11y_tree.xml
adb pull /sdcard/a11y_tree.xml

# Check for common violations in the dump
grep -E 'content-desc=""' a11y_tree.xml  # Missing content descriptions
grep -E 'clickable="true".*content-desc=""' a11y_tree.xml  # Clickable without label
```

### iOS — XCTest Accessibility Audits (iOS 17+)

```swift
// Built-in accessibility auditing in XCTest
func testHomeScreen_passesAccessibilityAudit() throws {
    let app = XCUIApplication()
    app.launch()

    // Runs Apple's full accessibility audit — fails on violations
    try app.performAccessibilityAudit()
}

// Audit with specific categories
func testLoginScreen_passesAudit() throws {
    let app = XCUIApplication()
    app.launch()

    try app.performAccessibilityAudit(for: [
        .dynamicType,      // Text scales properly
        .contrast,         // Color contrast meets WCAG
        .hitRegion,        // Touch targets ≥ 44pt
        .sufficientElementDescription  // Elements have labels
    ])
}

// Audit with known issue suppression
func testSettings_passesAudit() throws {
    let app = XCUIApplication()
    app.launch()
    app.buttons["Settings"].tap()

    try app.performAccessibilityAudit { issue in
        // Suppress known third-party SDK issues
        issue.element?.identifier == "third_party_banner"
    }
}
```

### Mobile A11y Checklist (WCAG 2.2)

| Check | Android | iOS | Automated |
|-------|---------|-----|-----------|
| Touch target ≥ 48dp / 44pt | `AccessibilityChecks` | `.hitRegion` audit | Yes |
| Content descriptions on images | `SpeakableTextPresentCheck` | `.sufficientElementDescription` | Yes |
| Color contrast ≥ 4.5:1 | Manual or Accessibility Scanner | `.contrast` audit | Partial |
| Text scales with system settings | Manual test with large font | `.dynamicType` audit | iOS only |
| Screen reader navigation order | TalkBack manual test | VoiceOver manual test | No |
| Focus management after navigation | Espresso focus assertions | XCTest focus assertions | Yes |
| Error messages announced | TalkBack announcements | VoiceOver announcements | Manual |

### CI Integration

```yaml
# GitHub Actions: Android a11y checks
a11y-android:
  runs-on: ubuntu-latest
  steps:
    - uses: reactivecircus/android-emulator-runner@v2
      with:
        api-level: 34
        script: |
          ./gradlew :app:connectedDebugAndroidTest \
            -Pandroid.testInstrumentationRunnerArguments.annotation=com.example.A11yTest

# iOS a11y checks (requires macOS runner)
a11y-ios:
  runs-on: macos-latest
  steps:
    - run: |
        xcodebuild test \
          -project MyApp.xcodeproj \
          -scheme MyApp \
          -destination 'platform=iOS Simulator,name=iPhone 15' \
          -only-testing:MyAppUITests/AccessibilityTests
```

---

## MUST DO

- Run BOTH axe-core AND Lighthouse — they catch different issue classes
- Use `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa` tags in axe-core for WCAG 2.1 AA scope
- Include the manual checklist — automated tools miss keyboard, focus order, and reading order issues
- Map every finding to a specific WCAG success criterion
- Provide a concrete fix for every violation, not just a description
- Wait for `networkidle` before running axe-core to capture dynamic content
- Distinguish informative images (`alt="desc"`) from decorative (`alt=""`)

## MUST NOT DO

- Report Lighthouse score alone as proof of compliance — 100 score does not guarantee WCAG conformance
- Skip the manual checklist — automated tools catch only 30-40% of WCAG criteria
- Run axe-core before page is fully loaded — SPAs need `networkidle` or explicit waits
- Treat `aria-label` as a universal fix — prefer visible text and native HTML semantics over ARIA
- Mark PASS with unresolved critical or serious violations regardless of score
- Use `tabindex` values > 0 in fix suggestions — positive tabindex breaks natural tab order
- Suggest color-only fixes for errors — color must be paired with text or icons (WCAG 1.4.1)
