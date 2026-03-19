# Common Patterns

Reference material for common Playwright testing patterns including authentication
state reuse, form testing, navigation, responsive layouts, accessibility testing,
running tests, server lifecycle management, reconnaissance-first testing, and
capture proof mode.

---

## Common Patterns

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

## CAPTURE PROOF MODE

When invoked with `--capture-proof` (from `/auto-verify` or `test-pipeline-agent`),
override the default screenshot behavior to capture on every test:

### Configuration Override

```typescript
// playwright.config.ts — capture-proof mode
use: {
  screenshot: 'on',  // Changed from 'only-on-failure'
},
```

Or via CLI:
```bash
npx playwright test --screenshot on
```

### Evidence Output

With capture-proof enabled, Playwright stores screenshots at:
```
test-results/          # Playwright's native output
  test-name-chromium/
    test-name-1.png    # Every test, pass or fail
```

The `tester-agent` copies these to the evidence archive:
```
test-evidence/{run_id}/screenshots/
  test_login_success.pass.png
  test_dashboard_loads.pass.png
  test_checkout_flow.fail.png
```

Naming convention: `{test_name}.{pass|fail}.png`
If multi-browser: `{test_name}.{browser}.{pass|fail}.png`

---