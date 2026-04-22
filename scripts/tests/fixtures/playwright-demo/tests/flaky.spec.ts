// Scenario: flaky
// Expectation: under DEMO_SCENARIO=flaky the /api/metric endpoint returns
// 500 on every other request, so this test alternates pass/fail. After a
// few runs the flakiness_score exceeds history.flaky_threshold and the
// test gets quarantined to known_issues without consuming the shared retry
// budget — the decay/probe-run rule will rehabilitate it once the flake
// is resolved.
import { test, expect } from '@playwright/test';

test.describe('metric @flaky', () => {
  test('metric endpoint returns a numeric value', async ({ page }) => {
    await page.goto('/dashboard');
    const metric = page.getByTestId('metric');
    // Auto-wait for the metric to populate (either number or 'error').
    await expect(metric).not.toHaveText('loading...', { timeout: 3_000 });
    // The assertion fails when the scenario intercepts with a 500 —
    // the dashboard then renders 'error' instead of a number.
    await expect(metric).toHaveText(/\d+/);
  });
});
