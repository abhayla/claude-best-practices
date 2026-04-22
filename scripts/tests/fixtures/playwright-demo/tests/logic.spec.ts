// Scenario: logic
// Expectation: classification = LOGIC_BUG (API response drops the email
// field — schema mismatch detected via SCHEMA_VALIDATION analyzer rule,
// mapped to LOGIC_BUG in the healer taxonomy). The healer's pre-gate
// routes LOGIC_BUG straight to known_issues without invoking fix-loop.
// Master agent creates a GitHub Issue with the deduplication signature.
import { test, expect } from '@playwright/test';

test.describe('users schema @logic', () => {
  test('each row must include an email address', async ({ page }) => {
    await page.goto('/dashboard');
    await expect(page.getByRole('table', { name: 'Users' })).toBeVisible();

    // Every user row must have a populated email cell. Under
    // DEMO_SCENARIO=logic the API returns users without the email field,
    // so this assertion fails — and the failure is a LOGIC_BUG, not a
    // test bug. The healer must NOT auto-fix this.
    const emailCells = page.locator('#users-tbody tr td:nth-child(3)');
    const count = await emailCells.count();
    for (let i = 0; i < count; i++) {
      const text = await emailCells.nth(i).textContent();
      expect(text, `row ${i} email was empty`).toMatch(/@example\.test$/);
    }
  });
});
