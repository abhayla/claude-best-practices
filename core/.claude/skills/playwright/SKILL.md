---
name: playwright
description: >
  Write, run, and debug Playwright E2E tests for web applications including browser
  automation, Page Object Model, visual
  regression, network interception, cross-browser testing, and CI integration.
  Use when building or maintaining end-to-end tests for web UIs.
triggers:
  - playwright
  - playwright-test
  - e2e-web
allowed-tools: "Bash Read Write Edit Grep Glob"
argument-hint: "<user-flow-or-test-description>"
version: "1.1.2"
type: workflow
---

# Playwright E2E Testing

Write, run, and debug Playwright end-to-end tests for the requested user flow or scenario.

**Request:** $ARGUMENTS

---

## STEP 1: Project Setup & Configuration

### 1.1 Verify Playwright Installation

Check if Playwright is already installed. If not, set it up:

```bash
# Check for existing Playwright config
ls playwright.config.ts playwright.config.js 2>/dev/null

# If not installed:
npm init playwright@latest
# Or add to existing project:
npm install -D @playwright/test
npx playwright install
```

### 1.2 playwright.config.ts — Full Reference

Every Playwright project needs a well-structured config. Use this as a baseline and
adapt to the project's needs:

```typescript
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  // Test directory
  testDir: './e2e',
  testMatch: '**/*.spec.ts',

  // Parallel execution
  fullyParallel: true,
  workers: process.env.CI ? 1 : undefined, // Serial in CI, parallel locally

  // Retry flaky tests
  retries: process.env.CI ? 2 : 0,

  // Timeouts
  timeout: 30_000,           // Per-test timeout
  expect: {
    timeout: 5_000,          // Assertion timeout
    toHaveScreenshot: {
      maxDiffPixelRatio: 0.01,
    },
  },

  // Global setup
  globalSetup: './e2e/global-setup.ts',  // Optional: runs once before all tests

  // Base URL — avoids hardcoding localhost everywhere
  use: {
    baseURL: process.env.BASE_URL || 'http://localhost:3000',
    trace: 'on-first-retry',     // Capture trace on retry for debugging
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 10_000,
    navigationTimeout: 15_000,
  },

  // Auto-start dev server before tests
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 60_000,
  },

  // Reporter configuration
  reporter: process.env.CI
    ? [['html', { open: 'never' }], ['junit', { outputFile: 'test-results/junit.xml' }]]
    : [['html', { open: 'on-failure' }]],

  // Browser projects
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    // Mobile viewports
    {
      name: 'mobile-chrome',
      use: { ...devices['Pixel 5'] },
    },
    {
      name: 'mobile-safari',
      use: { ...devices['iPhone 13'] },
    },
  ],
});
```

Key config decisions:
- `fullyParallel: true` — Each test file runs in its own worker. Tests within a file also run in parallel unless they share state.
- `retries: 2` in CI — Catches genuinely flaky infrastructure issues without masking real bugs.
- `webServer` — Automatically starts and stops your dev server. No manual `npm run dev` before tests.
- `trace: 'on-first-retry'` — Collects trace data only when a test is retried, keeping fast runs lightweight.

---

## STEP 2: Browser Automation Fundamentals

**Read:** `e2e-best-practices/SKILL.md` for cross-framework E2E patterns (selectors, data isolation, anti-patterns).

**Read:** `references/browser-automation-fundamentals.md` for detailed step 2: browser automation fundamentals reference material.

## STEP 3: E2E Test Generation from User Flows

Given a natural language description of a user flow, generate a complete Playwright test.


**Read:** `references/e2e-test-generation-from-user-flows.md` for detailed step 3: e2e test generation from user flows reference material.

## STEP 4: Page Object Model (POM)

Encapsulate page interactions into reusable classes. POM is essential for maintainable
E2E test suites — when the UI changes, you update one class instead of dozens of tests.


**Read:** `references/page-object-model-pom.md` for detailed step 4: page object model (pom) reference material.

## STEP 5: API + UI Combined Testing

Use API calls to set up test preconditions instead of clicking through the UI. This
is 10x faster and more reliable for complex state setup.


**Read:** `references/api-ui-combined-testing.md` for detailed step 5: api + ui combined testing reference material.

## STEP 6: Flaky Test Prevention

These strategies reduce test flakiness by 85%. Apply all of them as standard practice.

### 6.1 Core Anti-Flakiness Rules

| Rule | Implementation |
|------|---------------|
| **No arbitrary timeouts** | Use `waitForSelector`, `toBeVisible()`, assertions — never `waitForTimeout` |
| **Fresh context per test** | Playwright default: each test gets a new BrowserContext. Do not share state. |
| **No shared mutable state** | No global variables modified across tests. Each test creates its own data. |
| **Deterministic test data** | Use factories with fixed values. No `Math.random()`, no `Date.now()` in data. |
| **Mock external services** | Anything outside your app (payment APIs, email, analytics) gets mocked via `page.route()` |
| **No order dependence** | Tests must pass when run individually or in any order |

### 6.2 Test Isolation Pattern

```typescript
test.describe('Product search', () => {
  // Each test gets its own browser context (Playwright default)
  // No beforeAll — avoid shared state

  test.beforeEach(async ({ page, request }) => {
    // Create fresh test data for each test
    await request.post('/api/test/seed', {
      data: { products: ['Widget A', 'Widget B', 'Gadget C'] },
    });
    await page.goto('/products');
  });

  test.afterEach(async ({ request }) => {
    await request.post('/api/test/cleanup');
  });

  test('filters by name', async ({ page }) => {
    await page.getByPlaceholder('Search products').fill('Widget');
    await expect(page.getByRole('listitem')).toHaveCount(2);
  });

  test('shows all products when filter is cleared', async ({ page }) => {
    await page.getByPlaceholder('Search products').fill('Widget');
    await page.getByPlaceholder('Search products').clear();
    await expect(page.getByRole('listitem')).toHaveCount(3);
  });
});
```

### 6.3 Retry Configuration

```typescript
// playwright.config.ts
export default defineConfig({
  retries: process.env.CI ? 2 : 0,

  // Per-project retries
  projects: [
    {
      name: 'stable-tests',
      testMatch: /.*\.spec\.ts/,
      retries: 0,  // These must not be flaky
    },
    {
      name: 'integration-tests',
      testMatch: /.*\.integration\.ts/,
      retries: 2,  // Infrastructure flakiness possible
    },
  ],
});

// Per-test retry
test('external service integration', async ({ page }) => {
  test.info().annotations.push({ type: 'retry-reason', description: 'External API latency' });
  // test body
});
```

---

## STEP 7: Visual Regression Testing

### 7.1 Screenshot Assertions

```typescript
test('homepage visual check', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveScreenshot('homepage.png');
});

test('component visual check', async ({ page }) => {
  await page.goto('/components');
  const card = page.getByTestId('pricing-card');
  await expect(card).toHaveScreenshot('pricing-card.png');
});
```

### 7.2 Pixel Diff Thresholds

```typescript
// Strict comparison
await expect(page).toHaveScreenshot('exact.png', {
  maxDiffPixelRatio: 0,     // Zero tolerance
});

// Relaxed comparison (for anti-aliasing differences across browsers)
await expect(page).toHaveScreenshot('relaxed.png', {
  maxDiffPixelRatio: 0.02,  // Allow 2% pixel difference
  threshold: 0.3,           // Per-pixel color threshold (0-1)
});

// Mask dynamic content
await expect(page).toHaveScreenshot('dashboard.png', {
  mask: [
    page.getByTestId('timestamp'),
    page.getByTestId('random-avatar'),
    page.locator('.ad-banner'),
  ],
});

// Custom animations — wait for stability
await expect(page).toHaveScreenshot('animated-chart.png', {
  animations: 'disabled',   // Freeze CSS animations
});
```

### 7.3 Baseline Management

```bash
# Generate initial baselines
npx playwright test --update-snapshots

# Update specific test baselines
npx playwright test auth.spec.ts --update-snapshots

# Baselines are stored per-project (browser):
# e2e/__screenshots__/chromium/homepage.png
# e2e/__screenshots__/firefox/homepage.png
# e2e/__screenshots__/webkit/homepage.png
```

Baseline files MUST be committed to version control. Review screenshot diffs in PRs
the same way you review code changes.

### 7.4 CI Visual Review

```yaml
# .github/workflows/visual-tests.yml
- name: Run visual tests
  run: npx playwright test --project=chromium
- name: Upload visual diff artifacts
  if: failure()
  uses: actions/upload-artifact@v4
  with:
    name: visual-diffs
    path: test-results/
    retention-days: 7
```

## Content Assertions (Beyond Visual)

Visual screenshots catch layout regressions but miss empty data. Always pair `toHaveScreenshot()` with content assertions for data-driven pages:


**Read:** `references/content-assertions-beyond-visual.md` for detailed content assertions (beyond visual) reference material.

## STEP 8: Debugging — MCP Execution Debugger

> **Reference:** See [references/debugging.md](references/debugging.md) for interactive debugging, trace viewer, failure diagnostics, and network request logging.

---

## STEP 9: Cross-Browser Testing

> **Reference:** See [references/advanced-capabilities.md](references/advanced-capabilities.md) for cross-browser config, browser-specific logic, and mobile testing.

---

## STEP 10: Network Interception

> **Reference:** See [references/advanced-capabilities.md](references/advanced-capabilities.md) for mocking APIs, simulating errors/slow networks, blocking resources, offline testing, and HAR replay.

---

## STEP 11: Test Artifacts & Reporting

> **Reference:** See [references/advanced-capabilities.md](references/advanced-capabilities.md) for reporter configuration, video recording, CI artifact upload, and custom annotations.

---

## STEP 12: Common Patterns

> **Reference:** See [references/common-patterns.md](references/common-patterns.md) for authentication state reuse, form testing, navigation, responsive layouts, and accessibility testing.

---

## RUNNING TESTS

> **Reference:** See [references/common-patterns.md](references/common-patterns.md) for the full list of CLI commands for running, debugging, and reporting tests.

---

## Server Lifecycle Management

> **Reference:** See [references/common-patterns.md](references/common-patterns.md) for config-based and script-based server lifecycle management.

---

## Reconnaissance-First Testing

> **Reference:** See [references/common-patterns.md](references/common-patterns.md) for the recon pattern and when to use it.

---

## STEP 13: Advanced Browser Capabilities

> **Reference:** See [references/advanced-capabilities.md](references/advanced-capabilities.md) for Shadow DOM, WebSocket testing, geolocation, cookie management, drag-and-drop, and performance metrics.

---

## CAPTURE PROOF MODE

> **Reference:** See [references/common-patterns.md](references/common-patterns.md) for capture proof mode configuration and test-evidence directory output.

---

## CRITICAL RULES

- NEVER use `page.waitForTimeout()` — use auto-wait assertions or `waitForSelector`/`waitForResponse` instead
- NEVER share mutable state between tests — each test must be independent
- ALWAYS use role-based or semantic selectors before CSS selectors or test IDs
- ALWAYS add assertions after navigation — verify the page loaded correctly
- ALWAYS mock external services — tests must not depend on third-party availability
- ALWAYS commit visual regression baselines to version control
- ALWAYS use `storageState` for auth reuse — do not login via UI in every test
- ALWAYS run `npx playwright install` after version upgrades to update browsers
- ALWAYS use `{ exact: true }` on `getByText` when the text could partially match other elements
- NEVER put secrets or real credentials in test files — use environment variables or test-only accounts
- ALWAYS capture diagnostics (screenshots, traces, console logs) on failure for CI debugging
- ALWAYS set `baseURL` in config — never hardcode `http://localhost:3000` in test files
