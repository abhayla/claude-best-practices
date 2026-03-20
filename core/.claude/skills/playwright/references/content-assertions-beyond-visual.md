# Content Assertions (Beyond Visual)

### Data Presence

```typescript
// Verify data containers are populated — not just rendered
test('dashboard shows data', async ({ page }) => {
  await page.goto('/dashboard');
  await page.waitForLoadState('networkidle');

  // Visual check
  await expect(page).toHaveScreenshot('dashboard.png');

  // Content checks — catch empty-but-rendered states
  const tableRows = page.locator('table tbody tr');
  await expect(tableRows).not.toHaveCount(0);  // Table is not empty

  const chartDataPoints = page.locator('[data-testid="chart"] .data-point');
  await expect(chartDataPoints).not.toHaveCount(0);  // Chart has data

  // No empty-state messages visible when data is expected
  await expect(page.locator('text=No results found')).not.toBeVisible();
  await expect(page.locator('text=No data available')).not.toBeVisible();
});
```

### Data Validity

```typescript
// Catch placeholder, garbled, or invalid data
test('table shows valid data', async ({ page }) => {
  await page.goto('/data-table');
  await page.waitForLoadState('networkidle');

  // Get all cell values
  const cells = await page.locator('table tbody td').allTextContents();

  for (const cell of cells) {
    // No placeholder data
    expect(cell).not.toMatch(/^(undefined|null|NaN|Lorem ipsum|TODO|FIXME|test\d*)$/i);
    // No empty cells (unless explicitly allowed)
    expect(cell.trim()).not.toBe('');
  }
});
```

### Data Freshness

```typescript
// Verify timestamps are within expected recency
test('feed shows recent data', async ({ page }) => {
  await page.goto('/feed');
  await page.waitForLoadState('networkidle');

  const timestamps = await page.locator('[data-testid="timestamp"]').allTextContents();
  expect(timestamps.length).toBeGreaterThan(0);

  // At least one entry should be from today (or within expected window)
  // Adjust the recency window based on your data update interval
});
```

### Anti-Pattern: Screenshot-Only Testing

```typescript
// BAD: Only visual check — passes even if data is empty
test('dashboard renders', async ({ page }) => {
  await page.goto('/dashboard');
  await expect(page).toHaveScreenshot('dashboard.png');
  // This passes if the screen matches baseline — even if baseline was ALSO empty
});

// GOOD: Visual + content checks
test('dashboard shows data', async ({ page }) => {
  await page.goto('/dashboard');
  await expect(page).toHaveScreenshot('dashboard.png');         // Layout correct
  await expect(page.locator('table tbody tr')).not.toHaveCount(0); // Data present
  await expect(page.locator('text=No data')).not.toBeVisible();    // No empty state
});
```

---


