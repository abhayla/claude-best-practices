// Scenario: broken-locator
// Expectation: classification = SELECTOR (deterministic regex gate),
// healed via live ARIA snapshot → new getByRole('button', { name: 'Reload Users' }).
import { test, expect } from '@playwright/test';

test.describe('dashboard @broken-locator', () => {
  test('refresh users', async ({ page }) => {
    await page.goto('/dashboard');

    // This locator is intentionally brittle for the broken-locator scenario:
    // the server swaps the button text from "Refresh" to "Reload Users" when
    // DEMO_SCENARIO=broken-locator, so this locator resolves to 0 elements
    // and Playwright emits "Locator: ... waiting for getByRole('button',
    // { name: 'Refresh' })" — the deterministic regex rule in
    // test-failure-analyzer-agent will short-circuit to SELECTOR @ 0.93
    // without invoking the LLM.
    const refresh = page.getByRole('button', { name: 'Refresh' });
    await refresh.click();

    await expect(page.getByRole('table', { name: 'Users' })).toBeVisible();
    const rows = page.getByRole('row');
    await expect(rows).toHaveCount(3); // header + 2 users
  });
});
