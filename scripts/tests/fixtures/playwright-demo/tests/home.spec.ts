// Scenario: pass (default)
// Expectation: all steps PASS, pipeline verdict PASSED.
import { test, expect } from '@playwright/test';

test.describe('home @pass', () => {
  test('home page renders with scenario indicator', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByRole('heading', { level: 1 })).toHaveText(
      'Demo Fixture — Home',
    );
    await expect(page.getByTestId('scenario')).toHaveText(
      process.env.DEMO_SCENARIO || 'pass',
    );
    await expect(page.getByTestId('go-dashboard')).toBeEnabled();
  });
});
