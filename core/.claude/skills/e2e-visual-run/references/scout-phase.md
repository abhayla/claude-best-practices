# Scout Phase: Test Execution & Evidence Capture

Detailed guidance for STEP 3 of the e2e-visual-run skill.

## Framework-Specific Screenshot Capture

### Playwright
```typescript
// playwright.config.ts — capture EVERY test (screenshot verdict is authoritative)
use: {
  screenshot: 'on',
  trace: 'on-first-retry',
  video: 'retain-on-failure'
}
```

### Cypress
```javascript
// cypress.config.js — capture every test
screenshotOnRunFailure: true,
// Also add cy.screenshot() in afterEach for passing tests
video: false  // enable only if needed — expensive
```

### Selenium (Python)
```python
# In test teardown
def teardown_method(self, method):
    if self._outcome.errors:
        self.driver.save_screenshot(f"test-evidence/{run_id}/screenshots/{test_name}.fail.png")
```

### Detox (React Native)
```javascript
afterEach(async () => {
  if (jasmine.currentTest.failedExpectations.length > 0) {
    await device.takeScreenshot(testName);
  }
});
```

### Flutter
```dart
// In integration_test
testWidgets('description', (tester) async {
  // ... test logic
  // On failure, capture:
  await tester.pumpAndSettle();
  await expectLater(find.byType(MaterialApp), matchesGoldenFile('failures/$testName.png'));
});
```

## Accessibility Tree Capture

### Playwright (Primary)
```typescript
const snapshot = await page.accessibility.snapshot();
fs.writeFileSync(`test-evidence/${runId}/a11y/${testName}.json`, JSON.stringify(snapshot, null, 2));
```

### DOM Fallback (Other Frameworks)
When native a11y tree access is unavailable, capture DOM structure:
```javascript
const domTree = await page.evaluate(() => {
  function walk(el) {
    return {
      tag: el.tagName,
      role: el.getAttribute('role'),
      ariaLabel: el.getAttribute('aria-label'),
      text: el.textContent?.substring(0, 100),
      children: Array.from(el.children).map(walk)
    };
  }
  return walk(document.body);
});
```

## Single Test Execution Commands

Detect the project's test framework and use the appropriate single-test command:

| Framework | Single Test Command |
|-----------|-------------------|
| Playwright | `npx playwright test <file> --grep "<test_name>" --workers=1` |
| Cypress | `npx cypress run --spec <file>` |
| Jest | `npx jest <file> -t "<test_name>"` |
| Vitest | `npx vitest run <file> -t "<test_name>"` |
| pytest | `python -m pytest <file>::<test_name> -v` |
| Detox | `npx detox test <file> --configuration <config>` |
| Flutter | `flutter test <file> --name "<test_name>"` |

## Evidence Directory Structure

```
test-evidence/{run_id}/
  screenshots/
    test_login.pass.png          # Every test (pass and fail)
    test_checkout.fail.png
  a11y/
    test_login.json              # Every test (pass and fail)
    test_checkout.json
    test_dashboard.json
  manifest.json                  # Index of all evidence
```
