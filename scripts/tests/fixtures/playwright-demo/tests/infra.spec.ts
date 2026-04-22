// Scenario: infra
// Expectation: /api/orders returns 503 under DEMO_SCENARIO=infra, causing
// the page to render 'Failed to load orders'. The healer classifies this
// as INFRASTRUCTURE (regex rule matches on 503), attempts a single
// environment reset (restart the dev server), and retries once. If the
// upstream stays down, the test is moved to known_issues with a clear
// root-cause annotation — the healer MUST NOT rewrite test or app code
// to paper over an infrastructure failure.
import { test, expect } from '@playwright/test';

test.describe('orders availability @infra', () => {
  test('orders list populates from upstream', async ({ page }) => {
    await page.goto('/checkout');
    const orders = page.getByTestId('orders-list').locator('li');
    await expect(orders).toHaveCount(2);
  });
});
