/**
 * Overlap fixture: this test file is in `tests/api/` (matches the API track
 * path glob) AND imports `@playwright/test` (matches the UI track import
 * signal). Per the spec's accumulate semantics, the scout MUST classify this
 * test as requiring BOTH the API track AND the UI track.
 *
 * Used by `scripts/tests/test_pipeline_three_lane.py::test_track_accumulate_semantics`
 * to verify the scout doesn't first-match-win (which would produce only API
 * track) but instead runs all detection rules and accumulates results.
 */

import { test, expect } from '@playwright/test';

test('widget renders and api responds', async ({ page }) => {
  // UI assertion (would require functional+UI lanes)
  await page.goto('/widget');
  await expect(page.getByRole('heading', { name: /widget/i })).toBeVisible();

  // API assertion (would require functional+API lanes)
  const response = await page.request.get('/api/widget');
  expect(response.status()).toBe(200);
});
