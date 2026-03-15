---
name: playwright
description: >
  Self-contained Playwright E2E testing skill for web applications. Write, run, and
  debug Playwright tests including browser automation, Page Object Model, visual
  regression, network interception, cross-browser testing, and CI integration.
  Use when building or maintaining end-to-end tests for web UIs.
triggers:
  - playwright
  - playwright-test
  - e2e-web
allowed-tools: "Bash Read Write Edit Grep Glob"
argument-hint: "<user-flow-or-test-description>"
version: "1.1.0"
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

### 2.1 Page Navigation

```typescript
import { test, expect } from '@playwright/test';

test('navigate and verify page', async ({ page }) => {
  // Go to URL (uses baseURL from config)
  await page.goto('/dashboard');

  // Wait for specific load state
  await page.goto('/reports', { waitUntil: 'networkidle' });

  // Navigate with history
  await page.goBack();
  await page.goForward();
  await page.reload();

  // Wait for URL change after action
  await page.waitForURL('**/dashboard');
  await page.waitForURL(/\/users\/\d+/);
});
```

### 2.2 Element Selectors — Priority Order

Use selectors in this order of preference. Higher priority selectors are more
resilient to UI changes:

| Priority | Selector Type | Example | When to Use |
|----------|--------------|---------|-------------|
| 1 | Role | `getByRole('button', { name: 'Submit' })` | Always preferred — mirrors accessibility |
| 2 | Label | `getByLabel('Email address')` | Form inputs with labels |
| 3 | Placeholder | `getByPlaceholder('Enter email')` | Inputs without visible labels |
| 4 | Text | `getByText('Welcome back')` | Static text content |
| 5 | Test ID | `getByTestId('checkout-btn')` | When no semantic selector works |
| 6 | CSS | `page.locator('.nav-item.active')` | Complex structural queries |
| 7 | XPath | `page.locator('xpath=//div[@class="card"]')` | Legacy — avoid in new tests |

```typescript
test('selector examples', async ({ page }) => {
  // Role-based (preferred)
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.getByRole('heading', { name: 'Dashboard', level: 1 });
  await page.getByRole('link', { name: 'Settings' });
  await page.getByRole('checkbox', { name: 'Remember me' });
  await page.getByRole('combobox', { name: 'Country' });
  await page.getByRole('tab', { name: 'Billing' });

  // Label-based (forms)
  await page.getByLabel('Username').fill('testuser');
  await page.getByLabel('Password').fill('secret123');

  // Text-based
  await page.getByText('Welcome back', { exact: true });
  await page.getByText(/total: \$\d+/i);

  // Test ID (when semantics are not available)
  await page.getByTestId('submit-order').click();

  // Locator chaining — narrow scope
  const card = page.locator('.product-card').filter({ hasText: 'Premium Plan' });
  await card.getByRole('button', { name: 'Select' }).click();

  // nth element (when multiple matches)
  await page.getByRole('listitem').nth(2).click();
  await page.getByRole('listitem').first().click();
  await page.getByRole('listitem').last().click();

  // Filter by child element
  await page.getByRole('listitem').filter({
    has: page.getByRole('img', { name: 'Premium' }),
  }).click();
});
```

### 2.3 Actions

```typescript
test('user interactions', async ({ page }) => {
  // Click actions
  await page.getByRole('button', { name: 'Submit' }).click();
  await page.getByRole('button', { name: 'Options' }).dblclick();
  await page.getByRole('button', { name: 'More' }).click({ button: 'right' });
  await page.getByText('Drag me').hover();

  // Form inputs
  await page.getByLabel('Name').fill('John Doe');        // Replaces all content
  await page.getByLabel('Search').type('query', { delay: 100 }); // Types char by char
  await page.getByLabel('Notes').clear();
  await page.getByLabel('Name').pressSequentially('typed slowly', { delay: 50 });

  // Keyboard
  await page.keyboard.press('Enter');
  await page.keyboard.press('Control+A');
  await page.keyboard.press('Escape');

  // Checkboxes and radio buttons
  await page.getByRole('checkbox', { name: 'Agree' }).check();
  await page.getByRole('checkbox', { name: 'Agree' }).uncheck();
  await page.getByRole('radio', { name: 'Express' }).check();

  // Select dropdowns
  await page.getByRole('combobox', { name: 'Country' }).selectOption('US');
  await page.getByRole('combobox', { name: 'Tags' }).selectOption(['tag1', 'tag2']);

  // File upload
  await page.getByLabel('Upload file').setInputFiles('fixtures/document.pdf');
  await page.getByLabel('Upload files').setInputFiles([
    'fixtures/file1.pdf',
    'fixtures/file2.pdf',
  ]);
  // Clear file input
  await page.getByLabel('Upload file').setInputFiles([]);

  // File download
  const [download] = await Promise.all([
    page.waitForEvent('download'),
    page.getByRole('link', { name: 'Export CSV' }).click(),
  ]);
  await download.saveAs('test-results/export.csv');
});
```

### 2.4 Frames and Popups

```typescript
test('handle iframes', async ({ page }) => {
  // Access iframe by name or URL
  const frame = page.frameLocator('#payment-iframe');
  await frame.getByLabel('Card number').fill('4242424242424242');
  await frame.getByRole('button', { name: 'Pay' }).click();

  // Nested frames
  const nested = page.frameLocator('#outer').frameLocator('#inner');
  await nested.getByText('Content').click();
});

test('handle popups and new tabs', async ({ page, context }) => {
  // Wait for popup triggered by click
  const [popup] = await Promise.all([
    context.waitForEvent('page'),
    page.getByRole('link', { name: 'Open in new tab' }).click(),
  ]);
  await popup.waitForLoadState();
  await expect(popup).toHaveTitle('New Page');
  await popup.close();
});

test('handle dialogs', async ({ page }) => {
  // Accept/dismiss dialogs (must set handler BEFORE triggering)
  page.on('dialog', async dialog => {
    expect(dialog.message()).toContain('Are you sure?');
    await dialog.accept();
  });
  await page.getByRole('button', { name: 'Delete' }).click();
});
```

### 2.5 Auto-Wait vs Explicit Waits

Playwright auto-waits for elements to be actionable before performing actions. This
eliminates most explicit waits. Understand what auto-wait covers:

| Auto-waited (no explicit wait needed) | Requires explicit wait |
|---------------------------------------|----------------------|
| `click()` — waits for visible, enabled, stable | Custom animations finishing |
| `fill()` — waits for visible, enabled, editable | Third-party widget initialization |
| `check()` — waits for visible, enabled | Specific network request completion |
| All assertions — retry until timeout | Complex multi-step state transitions |

```typescript
// WRONG — never use arbitrary timeouts
await page.waitForTimeout(3000); // DO NOT DO THIS

// RIGHT — wait for specific conditions
await page.waitForSelector('.loading-spinner', { state: 'hidden' });
await page.waitForLoadState('networkidle');
await page.waitForResponse(resp =>
  resp.url().includes('/api/data') && resp.status() === 200
);
await page.waitForFunction(() =>
  document.querySelectorAll('.item').length > 5
);

// RIGHT — assertions auto-retry
await expect(page.getByText('Saved')).toBeVisible();           // Retries until visible
await expect(page.getByRole('list')).toContainText('Item 1');  // Retries until match
```

---

## STEP 3: E2E Test Generation from User Flows

Given a natural language description of a user flow, generate a complete Playwright test.

### 3.1 Flow-to-Test Process

1. **Parse the flow** — Break the description into discrete steps
2. **Identify assertions** — Determine what to verify at each step
3. **Add setup/teardown** — What state is needed before and after
4. **Write the test** — Follow the structure below

### 3.2 Test Structure Template

```typescript
import { test, expect } from '@playwright/test';

test.describe('Feature: Shopping Cart', () => {
  test.beforeEach(async ({ page }) => {
    // Common setup: navigate to starting point
    await page.goto('/');
    // Login if needed (or use storageState — see Section 12)
  });

  test.afterEach(async ({ page }) => {
    // Cleanup if needed (usually not required with test isolation)
  });

  test('user adds item to cart and completes checkout', async ({ page }) => {
    // Step 1: Browse products
    await page.getByRole('link', { name: 'Products' }).click();
    await expect(page).toHaveURL('/products');

    // Step 2: Add item to cart
    const product = page.locator('.product-card').filter({ hasText: 'Widget Pro' });
    await product.getByRole('button', { name: 'Add to cart' }).click();
    await expect(page.getByTestId('cart-count')).toHaveText('1');

    // Step 3: Go to cart
    await page.getByRole('link', { name: 'Cart' }).click();
    await expect(page.getByRole('heading', { name: 'Your Cart' })).toBeVisible();
    await expect(page.getByText('Widget Pro')).toBeVisible();

    // Step 4: Checkout
    await page.getByRole('button', { name: 'Checkout' }).click();
    await page.getByLabel('Email').fill('buyer@example.com');
    await page.getByLabel('Card number').fill('4242424242424242');
    await page.getByRole('button', { name: 'Place order' }).click();

    // Step 5: Verify confirmation
    await expect(page.getByRole('heading', { name: 'Order Confirmed' })).toBeVisible();
    await expect(page.getByText(/order #\d+/i)).toBeVisible();
  });
});
```

### 3.3 Assertion Reference

| Assertion | Use Case |
|-----------|----------|
| `toBeVisible()` | Element is displayed |
| `toBeHidden()` | Element is not displayed |
| `toBeEnabled()` / `toBeDisabled()` | Button/input state |
| `toBeChecked()` | Checkbox/radio state |
| `toHaveText('exact')` | Exact text content |
| `toContainText('partial')` | Partial text match |
| `toHaveValue('val')` | Input value |
| `toHaveAttribute('href', '/page')` | HTML attribute |
| `toHaveURL('/dashboard')` | Current page URL |
| `toHaveTitle('Page Title')` | Page title |
| `toHaveCount(3)` | Number of matched elements |
| `toHaveClass(/active/)` | CSS class |
| `toHaveCSS('color', 'rgb(0,0,0)')` | Computed CSS value |
| `toHaveScreenshot()` | Visual regression (see Section 6) |

All assertions auto-retry within `expect.timeout` (default 5s). Use `{ timeout: 10_000 }`
for slow operations.

---

## STEP 4: Page Object Model (POM)

Encapsulate page interactions into reusable classes. POM is essential for maintainable
E2E test suites — when the UI changes, you update one class instead of dozens of tests.

### 4.1 POM Structure

```
e2e/
  pages/
    login.page.ts
    dashboard.page.ts
    settings.page.ts
    components/
      navbar.component.ts
      modal.component.ts
  fixtures/
    test-fixtures.ts
  specs/
    auth.spec.ts
    dashboard.spec.ts
```

### 4.2 Page Object Implementation

```typescript
// e2e/pages/login.page.ts
import { type Page, type Locator, expect } from '@playwright/test';

export class LoginPage {
  readonly page: Page;
  readonly emailInput: Locator;
  readonly passwordInput: Locator;
  readonly submitButton: Locator;
  readonly errorMessage: Locator;
  readonly rememberMeCheckbox: Locator;

  constructor(page: Page) {
    this.page = page;
    this.emailInput = page.getByLabel('Email');
    this.passwordInput = page.getByLabel('Password');
    this.submitButton = page.getByRole('button', { name: 'Sign in' });
    this.errorMessage = page.getByRole('alert');
    this.rememberMeCheckbox = page.getByRole('checkbox', { name: 'Remember me' });
  }

  async goto() {
    await this.page.goto('/login');
  }

  async login(email: string, password: string) {
    await this.emailInput.fill(email);
    await this.passwordInput.fill(password);
    await this.submitButton.click();
  }

  async loginAndExpectDashboard(email: string, password: string) {
    await this.login(email, password);
    await expect(this.page).toHaveURL('/dashboard');
  }

  async expectError(message: string) {
    await expect(this.errorMessage).toContainText(message);
  }

  async expectFieldError(field: 'email' | 'password', message: string) {
    const input = field === 'email' ? this.emailInput : this.passwordInput;
    await expect(input).toHaveAttribute('aria-invalid', 'true');
    await expect(this.page.getByText(message)).toBeVisible();
  }
}

// e2e/pages/dashboard.page.ts
import { type Page, type Locator, expect } from '@playwright/test';

export class DashboardPage {
  readonly page: Page;
  readonly heading: Locator;
  readonly statsCards: Locator;
  readonly recentActivity: Locator;
  readonly userMenu: Locator;

  constructor(page: Page) {
    this.page = page;
    this.heading = page.getByRole('heading', { name: 'Dashboard', level: 1 });
    this.statsCards = page.getByTestId('stats-card');
    this.recentActivity = page.getByRole('list', { name: 'Recent activity' });
    this.userMenu = page.getByRole('button', { name: /user menu/i });
  }

  async expectLoaded() {
    await expect(this.heading).toBeVisible();
    await expect(this.statsCards.first()).toBeVisible();
  }

  async getStatValue(statName: string): Promise<string> {
    const card = this.statsCards.filter({ hasText: statName });
    const value = card.locator('.stat-value');
    return (await value.textContent()) ?? '';
  }

  async openUserMenu() {
    await this.userMenu.click();
  }

  async logout() {
    await this.openUserMenu();
    await this.page.getByRole('menuitem', { name: 'Logout' }).click();
    await expect(this.page).toHaveURL('/login');
  }

  async expectActivityCount(count: number) {
    await expect(this.recentActivity.getByRole('listitem')).toHaveCount(count);
  }
}
```

### 4.3 Using Page Objects with Custom Fixtures

```typescript
// e2e/fixtures/test-fixtures.ts
import { test as base } from '@playwright/test';
import { LoginPage } from '../pages/login.page';
import { DashboardPage } from '../pages/dashboard.page';

type TestFixtures = {
  loginPage: LoginPage;
  dashboardPage: DashboardPage;
};

export const test = base.extend<TestFixtures>({
  loginPage: async ({ page }, use) => {
    await use(new LoginPage(page));
  },
  dashboardPage: async ({ page }, use) => {
    await use(new DashboardPage(page));
  },
});

export { expect } from '@playwright/test';

// e2e/specs/auth.spec.ts
import { test, expect } from '../fixtures/test-fixtures';

test.describe('Authentication', () => {
  test('successful login redirects to dashboard', async ({ loginPage, dashboardPage }) => {
    await loginPage.goto();
    await loginPage.loginAndExpectDashboard('user@example.com', 'password123');
    await dashboardPage.expectLoaded();
  });

  test('invalid credentials show error', async ({ loginPage }) => {
    await loginPage.goto();
    await loginPage.login('user@example.com', 'wrongpassword');
    await loginPage.expectError('Invalid email or password');
  });

  test('empty form shows validation errors', async ({ loginPage }) => {
    await loginPage.goto();
    await loginPage.submitButton.click();
    await loginPage.expectFieldError('email', 'Email is required');
  });
});
```

---

## STEP 5: API + UI Combined Testing

Use API calls to set up test preconditions instead of clicking through the UI. This
is 10x faster and more reliable for complex state setup.

### 5.1 API Setup with UI Verification

```typescript
import { test, expect } from '@playwright/test';

test('admin views user list after creating users via API', async ({ page, request }) => {
  // ARRANGE: Create test data via API (fast, reliable)
  const users = ['alice', 'bob', 'charlie'];
  for (const name of users) {
    await request.post('/api/users', {
      data: { name, email: `${name}@test.com`, role: 'member' },
    });
  }

  // ACT: Navigate to admin panel via UI
  await page.goto('/admin/users');

  // ASSERT: Verify UI reflects API-created data
  for (const name of users) {
    await expect(page.getByRole('cell', { name })).toBeVisible();
  }
  await expect(page.getByRole('row')).toHaveCount(users.length + 1); // +1 for header
});
```

### 5.2 Authenticated API Requests

```typescript
import { test, expect } from '@playwright/test';

// Share authentication between API and browser
test('authenticated API and UI combined', async ({ page, request }) => {
  // Login via API to get auth token
  const loginResponse = await request.post('/api/auth/login', {
    data: { email: 'admin@example.com', password: 'admin123' },
  });
  const { token } = await loginResponse.json();

  // Use token for API setup
  const createResponse = await request.post('/api/projects', {
    headers: { Authorization: `Bearer ${token}` },
    data: { name: 'Test Project', description: 'E2E test' },
  });
  const project = await createResponse.json();

  // Set auth in browser context
  await page.goto('/login');
  await page.evaluate((t) => localStorage.setItem('auth_token', t), token);

  // Verify via UI
  await page.goto(`/projects/${project.id}`);
  await expect(page.getByRole('heading', { name: 'Test Project' })).toBeVisible();
});
```

### 5.3 API Cleanup in Teardown

```typescript
test.describe('Order management', () => {
  let orderId: string;

  test.afterEach(async ({ request }) => {
    // Clean up test data via API
    if (orderId) {
      await request.delete(`/api/orders/${orderId}`);
    }
  });

  test('create order and verify in UI', async ({ page, request }) => {
    const response = await request.post('/api/orders', {
      data: { product: 'Widget', quantity: 3 },
    });
    const order = await response.json();
    orderId = order.id;

    await page.goto(`/orders/${orderId}`);
    await expect(page.getByText('Widget')).toBeVisible();
    await expect(page.getByText('Quantity: 3')).toBeVisible();
  });
});
```

---

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

### Data Presence

```typescript
// Verify data containers are populated — not just rendered
test('dashboard shows data', async ({ page }) => {
  await page.goto('/dashboard');
  await page.waitForLoadState('networkidle');

  // Visual check
  await expect(page).toHaveScreenshot('dashboard.png');

  // Content checks — catch empty-but-rendered states
  const tableRows = page.locator('table tbody tr');
  await expect(tableRows).not.toHaveCount(0);  // Table is not empty

  const chartDataPoints = page.locator('[data-testid="chart"] .data-point');
  await expect(chartDataPoints).not.toHaveCount(0);  // Chart has data

  // No empty-state messages visible when data is expected
  await expect(page.locator('text=No results found')).not.toBeVisible();
  await expect(page.locator('text=No data available')).not.toBeVisible();
});
```

### Data Validity

```typescript
// Catch placeholder, garbled, or invalid data
test('table shows valid data', async ({ page }) => {
  await page.goto('/data-table');
  await page.waitForLoadState('networkidle');

  // Get all cell values
  const cells = await page.locator('table tbody td').allTextContents();

  for (const cell of cells) {
    // No placeholder data
    expect(cell).not.toMatch(/^(undefined|null|NaN|Lorem ipsum|TODO|FIXME|test\d*)$/i);
    // No empty cells (unless explicitly allowed)
    expect(cell.trim()).not.toBe('');
  }
});
```

### Data Freshness

```typescript
// Verify timestamps are within expected recency
test('feed shows recent data', async ({ page }) => {
  await page.goto('/feed');
  await page.waitForLoadState('networkidle');

  const timestamps = await page.locator('[data-testid="timestamp"]').allTextContents();
  expect(timestamps.length).toBeGreaterThan(0);

  // At least one entry should be from today (or within expected window)
  // Adjust the recency window based on your data update interval
});
```

### Anti-Pattern: Screenshot-Only Testing

```typescript
// BAD: Only visual check — passes even if data is empty
test('dashboard renders', async ({ page }) => {
  await page.goto('/dashboard');
  await expect(page).toHaveScreenshot('dashboard.png');
  // This passes if the screen matches baseline — even if baseline was ALSO empty
});

// GOOD: Visual + content checks
test('dashboard shows data', async ({ page }) => {
  await page.goto('/dashboard');
  await expect(page).toHaveScreenshot('dashboard.png');         // Layout correct
  await expect(page.locator('table tbody tr')).not.toHaveCount(0); // Data present
  await expect(page.locator('text=No data')).not.toBeVisible();    // No empty state
});
```

---

## STEP 8: Debugging — MCP Execution Debugger

### 8.1 Interactive Debugging

```typescript
test('debug this flow', async ({ page }) => {
  await page.goto('/checkout');

  // Pause execution — opens Playwright Inspector
  await page.pause();

  // Continue stepping through the test in the Inspector UI
  await page.getByRole('button', { name: 'Pay' }).click();
});
```

Run with headed mode for visual debugging:

```bash
# Run with browser visible
npx playwright test --headed

# Run with Playwright Inspector (step-through debugger)
npx playwright test --debug

# Debug a specific test
npx playwright test auth.spec.ts:15 --debug
```

### 8.2 Trace Viewer

```bash
# Enable trace collection
npx playwright test --trace on

# View traces after test run
npx playwright show-trace test-results/auth-spec-ts/trace.zip
```

The trace viewer shows:
- Step-by-step action log with timestamps
- DOM snapshots before and after each action
- Network requests and responses
- Console logs and errors
- Source code location for each step

### 8.3 Capture Diagnostics on Failure

```typescript
test.afterEach(async ({ page }, testInfo) => {
  if (testInfo.status !== 'passed') {
    // Capture console errors
    const consoleLogs: string[] = [];
    page.on('console', msg => consoleLogs.push(`${msg.type()}: ${msg.text()}`));

    // Attach screenshot with annotations
    const screenshot = await page.screenshot({ fullPage: true });
    await testInfo.attach('failure-screenshot', {
      body: screenshot,
      contentType: 'image/png',
    });

    // Attach DOM snapshot
    const html = await page.content();
    await testInfo.attach('page-html', {
      body: html,
      contentType: 'text/html',
    });

    // Attach console logs
    await testInfo.attach('console-logs', {
      body: consoleLogs.join('\n'),
      contentType: 'text/plain',
    });
  }
});
```

### 8.4 Network Request Logging

```typescript
test('debug network issues', async ({ page }) => {
  const requests: string[] = [];
  const failures: string[] = [];

  page.on('request', req => requests.push(`${req.method()} ${req.url()}`));
  page.on('requestfailed', req =>
    failures.push(`FAILED: ${req.method()} ${req.url()} - ${req.failure()?.errorText}`)
  );
  page.on('response', resp => {
    if (resp.status() >= 400) {
      failures.push(`${resp.status()} ${resp.url()}`);
    }
  });

  await page.goto('/dashboard');
  // ... test actions ...

  // Log for debugging
  console.log('All requests:', requests);
  if (failures.length) {
    console.log('Failed requests:', failures);
  }
});
```

---

## STEP 9: Cross-Browser Testing

### 9.1 Browser Projects in Config

```typescript
// playwright.config.ts — projects section
projects: [
  // Desktop browsers
  { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
  { name: 'webkit', use: { ...devices['Desktop Safari'] } },

  // Mobile viewports
  { name: 'mobile-chrome', use: { ...devices['Pixel 5'] } },
  { name: 'mobile-safari', use: { ...devices['iPhone 13'] } },

  // Tablet
  { name: 'tablet', use: { ...devices['iPad (gen 7)'] } },

  // Custom device
  {
    name: 'custom-mobile',
    use: {
      viewport: { width: 390, height: 844 },
      userAgent: 'Custom Mobile Agent',
      isMobile: true,
      hasTouch: true,
      deviceScaleFactor: 3,
    },
  },
],
```

### 9.2 Running Specific Browsers

```bash
# Run all browsers
npx playwright test

# Run specific browser
npx playwright test --project=chromium
npx playwright test --project=firefox

# Run only mobile
npx playwright test --project=mobile-chrome --project=mobile-safari
```

### 9.3 Browser-Specific Test Logic

```typescript
test('responsive menu behavior', async ({ page, isMobile }) => {
  await page.goto('/');

  if (isMobile) {
    // Mobile: hamburger menu
    await page.getByRole('button', { name: 'Menu' }).click();
    await expect(page.getByRole('navigation')).toBeVisible();
  } else {
    // Desktop: navigation always visible
    await expect(page.getByRole('navigation')).toBeVisible();
  }
});
```

---

## STEP 10: Network Interception

### 10.1 Mock API Responses

```typescript
test('display mocked product data', async ({ page }) => {
  // Mock API response
  await page.route('**/api/products', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        { id: 1, name: 'Mock Widget', price: 9.99 },
        { id: 2, name: 'Mock Gadget', price: 19.99 },
      ]),
    });
  });

  await page.goto('/products');
  await expect(page.getByText('Mock Widget')).toBeVisible();
  await expect(page.getByText('$9.99')).toBeVisible();
});
```

### 10.2 Simulate Error Responses

```typescript
test('handle API errors gracefully', async ({ page }) => {
  await page.route('**/api/products', route =>
    route.fulfill({ status: 500, body: 'Internal Server Error' })
  );

  await page.goto('/products');
  await expect(page.getByText('Something went wrong')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Retry' })).toBeVisible();
});
```

### 10.3 Simulate Slow Networks

```typescript
test('loading state during slow response', async ({ page }) => {
  await page.route('**/api/data', async route => {
    // Delay response by 3 seconds
    await new Promise(resolve => setTimeout(resolve, 3000));
    await route.fulfill({
      status: 200,
      body: JSON.stringify({ items: [] }),
    });
  });

  await page.goto('/data');
  // Verify loading indicator appears
  await expect(page.getByRole('progressbar')).toBeVisible();
  // Then verify it disappears when data loads
  await expect(page.getByRole('progressbar')).toBeHidden({ timeout: 10_000 });
});
```

### 10.4 Block Resources

```typescript
test('page loads without external resources', async ({ page }) => {
  // Block images, ads, analytics
  await page.route('**/*.{png,jpg,jpeg,gif,svg}', route => route.abort());
  await page.route('**/analytics/**', route => route.abort());
  await page.route('**/ads/**', route => route.abort());

  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Welcome' })).toBeVisible();
});
```

### 10.5 Test Offline Behavior

```typescript
test('offline fallback page', async ({ page, context }) => {
  await page.goto('/');
  // Cache the page, then go offline
  await context.setOffline(true);

  await page.goto('/dashboard');
  await expect(page.getByText('You are offline')).toBeVisible();

  // Come back online
  await context.setOffline(false);
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
});
```

### 10.6 HAR Recording and Replay

```bash
# Record network traffic to HAR file
npx playwright test --save-har=e2e/fixtures/network.har
```

```typescript
// Replay recorded network traffic
test('replay from HAR', async ({ page }) => {
  await page.routeFromHAR('e2e/fixtures/network.har', {
    url: '**/api/**',
    update: false,  // Set to true to re-record
  });

  await page.goto('/dashboard');
  await expect(page.getByText('Recorded Data')).toBeVisible();
});
```

---

## STEP 11: Test Artifacts & Reporting

### 11.1 Reporter Configuration

```typescript
// playwright.config.ts
reporter: [
  // HTML report — interactive, best for local dev
  ['html', { open: 'on-failure', outputFolder: 'playwright-report' }],

  // JUnit — for CI systems (Jenkins, GitHub Actions)
  ['junit', { outputFile: 'test-results/junit.xml' }],

  // JSON — for custom dashboards
  ['json', { outputFile: 'test-results/results.json' }],

  // List — console output during run
  ['list'],

  // Dot — minimal console output
  // ['dot'],
],
```

### 11.2 Video Recording

```typescript
// playwright.config.ts
use: {
  // Record video on failure only (saves disk space)
  video: 'retain-on-failure',

  // Or always record (useful during initial test development)
  // video: 'on',

  // Video size
  video: {
    mode: 'retain-on-failure',
    size: { width: 1280, height: 720 },
  },
},
```

### 11.3 CI Artifact Upload — GitHub Actions

```yaml
# .github/workflows/e2e.yml
name: E2E Tests
on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright browsers
        run: npx playwright install --with-deps

      - name: Run E2E tests
        run: npx playwright test
        env:
          CI: true

      - name: Upload HTML report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 14

      - name: Upload test results (traces, screenshots, videos)
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: test-results
          path: test-results/
          retention-days: 7
```

### 11.4 Custom Annotations for Failure Context

```typescript
test('annotated test with failure context', async ({ page }, testInfo) => {
  testInfo.annotations.push(
    { type: 'feature', description: 'Checkout Flow' },
    { type: 'severity', description: 'critical' },
  );

  await page.goto('/checkout');

  // On failure, attach the current URL and local storage
  try {
    await page.getByRole('button', { name: 'Pay' }).click();
    await expect(page).toHaveURL('/confirmation');
  } catch (error) {
    await testInfo.attach('current-url', {
      body: page.url(),
      contentType: 'text/plain',
    });
    const storage = await page.evaluate(() => JSON.stringify(localStorage));
    await testInfo.attach('localStorage', {
      body: storage,
      contentType: 'application/json',
    });
    throw error;
  }
});
```

---

## STEP 12: Common Patterns

### 12.1 Authentication State Reuse (storageState)

Logging in via UI for every test is slow. Store auth state and reuse it:

```typescript
// e2e/global-setup.ts — runs once before all tests
import { chromium, type FullConfig } from '@playwright/test';

async function globalSetup(config: FullConfig) {
  const browser = await chromium.launch();
  const page = await browser.newPage();

  // Login via UI once
  await page.goto('http://localhost:3000/login');
  await page.getByLabel('Email').fill('admin@example.com');
  await page.getByLabel('Password').fill('admin123');
  await page.getByRole('button', { name: 'Sign in' }).click();
  await page.waitForURL('**/dashboard');

  // Save auth state (cookies + localStorage)
  await page.context().storageState({ path: 'e2e/.auth/admin.json' });

  await browser.close();
}

export default globalSetup;

// playwright.config.ts — use saved state
projects: [
  // Setup project — runs first, produces auth state
  {
    name: 'setup',
    testMatch: /global-setup\.ts/,
  },
  // Tests use the saved auth state
  {
    name: 'chromium',
    use: {
      ...devices['Desktop Chrome'],
      storageState: 'e2e/.auth/admin.json',
    },
    dependencies: ['setup'],
  },
],
```

Add `e2e/.auth/` to `.gitignore` — auth state files contain session tokens.

### 12.2 Testing Forms with Validation

```typescript
test('form validation flow', async ({ page }) => {
  await page.goto('/register');

  // Submit empty form
  await page.getByRole('button', { name: 'Register' }).click();

  // Verify all validation errors appear
  await expect(page.getByText('Name is required')).toBeVisible();
  await expect(page.getByText('Email is required')).toBeVisible();
  await expect(page.getByText('Password is required')).toBeVisible();

  // Fill partially and check remaining errors
  await page.getByLabel('Name').fill('John');
  await page.getByRole('button', { name: 'Register' }).click();
  await expect(page.getByText('Name is required')).toBeHidden();
  await expect(page.getByText('Email is required')).toBeVisible();

  // Fill invalid email
  await page.getByLabel('Email').fill('not-an-email');
  await page.getByRole('button', { name: 'Register' }).click();
  await expect(page.getByText('Enter a valid email')).toBeVisible();

  // Fill valid data
  await page.getByLabel('Email').fill('john@example.com');
  await page.getByLabel('Password').fill('StrongP@ss1');
  await page.getByRole('button', { name: 'Register' }).click();
  await expect(page).toHaveURL('/welcome');
});
```

### 12.3 Testing Navigation and Routing

```typescript
test('breadcrumb navigation', async ({ page }) => {
  await page.goto('/products/electronics/laptops');

  const breadcrumbs = page.getByRole('navigation', { name: 'Breadcrumb' });
  await expect(breadcrumbs.getByRole('link', { name: 'Home' })).toBeVisible();
  await expect(breadcrumbs.getByRole('link', { name: 'Electronics' })).toBeVisible();
  await expect(breadcrumbs.getByText('Laptops')).toBeVisible();

  // Navigate via breadcrumb
  await breadcrumbs.getByRole('link', { name: 'Electronics' }).click();
  await expect(page).toHaveURL('/products/electronics');
});

test('404 page for unknown routes', async ({ page }) => {
  const response = await page.goto('/this-does-not-exist');
  expect(response?.status()).toBe(404);
  await expect(page.getByRole('heading', { name: 'Page Not Found' })).toBeVisible();
  await expect(page.getByRole('link', { name: 'Go home' })).toBeVisible();
});
```

### 12.4 Testing Responsive Layouts

```typescript
test.describe('responsive layout', () => {
  test('desktop shows sidebar navigation', async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto('/');
    await expect(page.getByRole('complementary', { name: 'Sidebar' })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Menu' })).toBeHidden();
  });

  test('mobile shows hamburger menu', async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto('/');
    await expect(page.getByRole('complementary', { name: 'Sidebar' })).toBeHidden();
    await expect(page.getByRole('button', { name: 'Menu' })).toBeVisible();

    // Open mobile menu
    await page.getByRole('button', { name: 'Menu' }).click();
    await expect(page.getByRole('navigation', { name: 'Mobile menu' })).toBeVisible();
  });
});
```

### 12.5 Accessibility Testing with axe

```typescript
import { test, expect } from '@playwright/test';
import AxeBuilder from '@axe-core/playwright';

test('homepage has no accessibility violations', async ({ page }) => {
  await page.goto('/');

  const results = await new AxeBuilder({ page })
    .withTags(['wcag2a', 'wcag2aa'])  // WCAG 2.0 Level A and AA
    .exclude('.third-party-widget')    // Exclude elements you don't control
    .analyze();

  expect(results.violations).toEqual([]);
});

test('form accessibility', async ({ page }) => {
  await page.goto('/contact');

  const results = await new AxeBuilder({ page })
    .include('form')  // Only check the form
    .analyze();

  // Report violations with details
  for (const violation of results.violations) {
    console.log(`${violation.id}: ${violation.description}`);
    for (const node of violation.nodes) {
      console.log(`  ${node.html}`);
    }
  }

  expect(results.violations).toEqual([]);
});
```

Install with: `npm install -D @axe-core/playwright`

---

## RUNNING TESTS

```bash
# Run all tests
npx playwright test

# Run specific file
npx playwright test e2e/specs/auth.spec.ts

# Run tests matching name pattern
npx playwright test -g "login"

# Run in headed mode (see the browser)
npx playwright test --headed

# Run with debugger
npx playwright test --debug

# Run specific browser only
npx playwright test --project=chromium

# Run with trace enabled
npx playwright test --trace on

# Update visual snapshots
npx playwright test --update-snapshots

# Show HTML report
npx playwright show-report

# View trace file
npx playwright show-trace test-results/trace.zip

# Run in UI mode (interactive test runner)
npx playwright test --ui
```

---

## Server Lifecycle Management

When testing a web app, the dev server must be running before tests execute. Playwright's built-in `webServer` config handles this automatically:

### Config-Based (Recommended)

```typescript
// playwright.config.ts
export default defineConfig({
  webServer: {
    command: 'npm run dev',           // Command to start the dev server
    url: 'http://localhost:3000',      // URL to wait for before running tests
    reuseExistingServer: !process.env.CI,  // Reuse in dev, fresh in CI
    timeout: 30_000,                   // Max wait for server to start (ms)
    stdout: 'pipe',                    // Capture output for debugging
    stderr: 'pipe',
  },
  use: {
    baseURL: 'http://localhost:3000',
  },
});
```

For **multiple servers** (e.g., frontend + API backend):

```typescript
webServer: [
  {
    command: 'npm run dev:api',
    url: 'http://localhost:8080/health',
    reuseExistingServer: !process.env.CI,
  },
  {
    command: 'npm run dev:web',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
],
```

### Script-Based (For Complex Setups)

When you need more control (database seeding, environment setup), use a helper script:

```python
# e2e/with_server.py — Start server, run tests, clean up
import subprocess, time, sys, signal, requests

def wait_for_server(url, timeout=30):
    """Poll until the server responds or timeout."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(url, timeout=2)
            if resp.status_code < 500:
                return True
        except requests.ConnectionError:
            pass
        time.sleep(1)
    return False

# 1. Setup (seed DB, etc.)
subprocess.run(["python", "scripts/seed_test_db.py"], check=True)

# 2. Start server
server = subprocess.Popen(["npm", "run", "dev"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

try:
    # 3. Wait for ready
    if not wait_for_server("http://localhost:3000"):
        print("Server failed to start within 30s")
        sys.exit(1)

    # 4. Run tests
    result = subprocess.run(["npx", "playwright", "test"] + sys.argv[1:])
    sys.exit(result.returncode)
finally:
    # 5. Cleanup
    server.send_signal(signal.SIGTERM)
    server.wait(timeout=10)
```

Usage: `python e2e/with_server.py --project=chromium`

---

## Reconnaissance-First Testing

For dynamic web apps (SPAs, apps with conditional rendering, A/B tests), scan the page structure before writing assertions. This prevents brittle tests that break when the UI changes.

### The Recon Pattern

```typescript
test('checkout flow adapts to user type', async ({ page }) => {
  await page.goto('/checkout');

  // RECON: Discover what's actually on the page
  const hasGuestCheckout = await page.getByRole('button', { name: 'Guest Checkout' }).isVisible();
  const hasExpressCheckout = await page.getByRole('button', { name: 'Express Checkout' }).isVisible();
  const paymentMethods = await page.locator('[data-testid="payment-method"]').allTextContents();

  // ACT: Branch based on what's rendered
  if (hasExpressCheckout) {
    await page.getByRole('button', { name: 'Express Checkout' }).click();
    await expect(page).toHaveURL(/\/checkout\/express/);
  } else if (hasGuestCheckout) {
    await page.getByRole('button', { name: 'Guest Checkout' }).click();
    await expect(page.getByLabel('Email')).toBeVisible();
  }

  // ASSERT: Verify based on discovered state
  expect(paymentMethods.length).toBeGreaterThan(0);
});
```

### When to Use Recon-First

- Pages with feature flags or A/B tests (UI varies per session)
- Dynamic dashboards where widgets load conditionally
- Apps with role-based UI (admin sees different controls than user)
- Third-party embedded content (may load differently each time)

### When NOT to Use Recon-First

- Static pages with predictable structure — just assert directly
- Tests validating that specific elements MUST exist — recon would hide failures

---

## STEP 13: Advanced Browser Capabilities

### 13.1 Shadow DOM

Web components encapsulate DOM inside shadow roots. Use the `>> shadow=` piercing selector
to reach elements inside shadow DOM:

```typescript
// Pierce a single shadow root
const inner = page.locator('my-component >> shadow=.inner-class');
await expect(inner).toBeVisible();

// Chain through nested shadow roots
const deepElement = page.locator('outer-host >> shadow=inner-host >> shadow=.target');
await expect(deepElement).toHaveText('Expected content');

// Combine with role-based selectors inside shadow DOM
const button = page.locator('my-toolbar >> shadow=button[aria-label="Save"]');
await button.click();
```

### 13.2 WebSocket Testing

Intercept and mock WebSocket connections to test real-time features without a live server:

```typescript
test('receives real-time notifications', async ({ page }) => {
  // Intercept WebSocket connections matching a URL pattern
  await page.routeWebSocket('**/ws/notifications', (ws) => {
    ws.onMessage((message) => {
      // Echo back or respond with mock data
      if (message === 'ping') {
        ws.send('pong');
      }
    });

    // Simulate a server-sent message after connection
    setTimeout(() => {
      ws.send(JSON.stringify({ type: 'alert', text: 'New message' }));
    }, 500);
  });

  await page.goto('/dashboard');
  await expect(page.getByText('New message')).toBeVisible();
});
```

### 13.3 Geolocation and Permissions

Override geolocation and grant browser permissions to test location-aware features:

```typescript
test('shows nearby stores based on location', async ({ browser }) => {
  const context = await browser.newContext({
    geolocation: { latitude: 40.7128, longitude: -74.0060 },
    permissions: ['geolocation'],
  });
  const page = await context.newPage();

  await page.goto('/store-finder');
  await page.getByRole('button', { name: 'Use my location' }).click();
  await expect(page.getByText('Stores near New York')).toBeVisible();

  // Change location mid-test
  await context.setGeolocation({ latitude: 34.0522, longitude: -118.2437 });
  await page.getByRole('button', { name: 'Refresh' }).click();
  await expect(page.getByText('Stores near Los Angeles')).toBeVisible();

  await context.close();
});

// Grant other permissions (camera, microphone, notifications)
const context = await browser.newContext({
  permissions: ['geolocation', 'notifications'],
});
```

### 13.4 Cookie Management

Manipulate cookies directly for testing auth flows, consent banners, or session handling:

```typescript
test('respects cookie consent preferences', async ({ browser }) => {
  const context = await browser.newContext();
  const page = await context.newPage();

  // Pre-set cookies before navigation
  await context.addCookies([
    { name: 'consent', value: 'accepted', domain: 'localhost', path: '/' },
    { name: 'session_id', value: 'test-session-abc', domain: 'localhost', path: '/' },
  ]);

  await page.goto('/');
  // Consent banner should not appear since cookie is set
  await expect(page.getByRole('dialog', { name: 'Cookie consent' })).toBeHidden();

  // Read cookies to verify application behavior
  const cookies = await context.cookies();
  const trackingCookie = cookies.find(c => c.name === 'analytics_id');
  expect(trackingCookie).toBeDefined();

  // Clear cookies to simulate logged-out state
  await context.clearCookies();
  await page.reload();
  await expect(page.getByRole('link', { name: 'Sign in' })).toBeVisible();

  await context.close();
});
```

### 13.5 Drag and Drop

Test drag-and-drop interactions using the built-in `dragTo` method or manual mouse control:

```typescript
test('reorder items via drag and drop', async ({ page }) => {
  await page.goto('/kanban');

  // Simple drag-to-target
  const card = page.getByText('Task A');
  const targetColumn = page.getByTestId('column-done');
  await card.dragTo(targetColumn);
  await expect(targetColumn.getByText('Task A')).toBeVisible();
});

test('precise drag with mouse control', async ({ page }) => {
  await page.goto('/canvas-editor');

  // Manual drag for pixel-level precision or custom drag behavior
  const source = page.getByTestId('draggable-widget');
  const box = await source.boundingBox();
  if (box) {
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    await page.mouse.down();
    await page.mouse.move(box.x + 200, box.y + 100, { steps: 10 });
    await page.mouse.up();
  }

  await expect(page.getByTestId('draggable-widget')).toHaveCSS('transform', /translate/);
});
```

### 13.6 Performance Metrics

Collect JavaScript heap size, DOM node counts, and code coverage for performance budgets:

```typescript
test('page meets performance budget', async ({ page }) => {
  await page.goto('/');

  // Collect CDP metrics (Chromium only)
  const client = await page.context().newCDPSession(page);
  await client.send('Performance.enable');
  const { metrics } = await client.send('Performance.getMetrics');

  const jsHeap = metrics.find(m => m.name === 'JSHeapUsedSize');
  const domNodes = metrics.find(m => m.name === 'Nodes');

  // Assert against performance budgets
  expect(jsHeap?.value).toBeLessThan(50 * 1024 * 1024); // < 50MB JS heap
  expect(domNodes?.value).toBeLessThan(1500);            // < 1500 DOM nodes
});

test('measure JS coverage', async ({ page }) => {
  // Start JS coverage collection
  await page.coverage.startJSCoverage();
  await page.goto('/');
  await page.getByRole('link', { name: 'Features' }).click();

  const coverage = await page.coverage.stopJSCoverage();

  // Calculate total bytes vs used bytes
  let totalBytes = 0;
  let usedBytes = 0;
  for (const entry of coverage) {
    totalBytes += entry.text.length;
    for (const range of entry.ranges) {
      usedBytes += range.end - range.start;
    }
  }

  const usagePercent = (usedBytes / totalBytes) * 100;
  console.log(`JS coverage: ${usagePercent.toFixed(1)}% of ${(totalBytes / 1024).toFixed(0)}KB used`);
  expect(usagePercent).toBeGreaterThan(50); // At least 50% of loaded JS is used
});
```

Note: `page.coverage` and CDP sessions are **Chromium-only** features. Gate these tests to run
only against the Chromium project in your Playwright config.

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
