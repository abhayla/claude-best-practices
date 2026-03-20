# STEP 2: Browser Automation Fundamentals

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

