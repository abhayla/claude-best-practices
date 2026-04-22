// Scenario: timing
// Expectation: classification = TIMEOUT/TIMING (deterministic regex gate),
// healed by replacing the brittle 500ms fixed-delay assumption with an
// event-driven `await expect(list).toHaveCount(2)` assertion that auto-waits.
import { test, expect } from '@playwright/test';

test.describe('checkout @timing', () => {
  test('orders load and submit button enables', async ({ page }) => {
    await page.goto('/checkout');

    // Intentionally brittle fixed wait: server delays 3s under the timing
    // scenario, so this 500ms sleep is too short and the subsequent
    // assertions will time out with Playwright's "waiting for selector"
    // signature — the regex rule routes this to TIMEOUT and the healer
    // replaces the fixed wait with an auto-waiting assertion.
    await page.waitForTimeout(500);

    const orders = page.getByTestId('orders-list').locator('li');
    await expect(orders).toHaveCount(2);
    await expect(page.getByTestId('submit')).toBeEnabled();
  });
});
