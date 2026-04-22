// Scenario: visual-change
// Expectation: exit code PASSED (the DOM structure is unchanged), but the
// screenshot baseline diffs because the CSS color on the h1 shifts under
// DEMO_SCENARIO=visual-change. The dual-signal verdict routes the test to
// `expected_changes` (not `fix_queue`): the visual inspector sees a CHANGED
// screenshot + exit PASSED = EXPECTED_CHANGE. Pipeline verdict: NEEDS_REVIEW.
import { test, expect } from '@playwright/test';

test.describe('dashboard visual @visual-change', () => {
  test('dashboard heading baseline', async ({ page }) => {
    await page.goto('/dashboard');
    const heading = page.getByRole('heading', { level: 1 });
    await expect(heading).toHaveText('Users Dashboard');
    // Screenshot the heading only so the comparison is stable against the
    // only intentional variation (the CSS color override in dashboard.html).
    await expect(heading).toHaveScreenshot('dashboard-heading.png', {
      maxDiffPixelRatio: 0.001,
    });
  });
});
