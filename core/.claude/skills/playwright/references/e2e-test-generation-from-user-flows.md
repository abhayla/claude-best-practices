# STEP 3: E2E Test Generation from User Flows

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

