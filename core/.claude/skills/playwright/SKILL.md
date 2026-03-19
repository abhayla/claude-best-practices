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
version: "1.1.1"
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
