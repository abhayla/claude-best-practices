# Advanced Capabilities

Reference material for cross-browser testing, network interception, test artifacts
and reporting, and advanced browser features (Shadow DOM, WebSockets, geolocation,
cookies, drag-and-drop, performance metrics).

---

## Cross-Browser Testing

### 9.1 Browser Projects in Config

```typescript
// playwright.config.ts — projects section
projects: [
  // Desktop browsers
  { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
  { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
  { name: 'webkit', use: { ...devices['Desktop Safari'] } },

  // Mobile viewports
  { name: 'mobile-chrome', use: { ...devices['Pixel 5'] } },
  { name: 'mobile-safari', use: { ...devices['iPhone 13'] } },

  // Tablet
  { name: 'tablet', use: { ...devices['iPad (gen 7)'] } },

  // Custom device
  {
    name: 'custom-mobile',
    use: {
      viewport: { width: 390, height: 844 },
      userAgent: 'Custom Mobile Agent',
      isMobile: true,
      hasTouch: true,
      deviceScaleFactor: 3,
    },
  },
],
```

### 9.2 Running Specific Browsers

```bash
# Run all browsers
npx playwright test

# Run specific browser
npx playwright test --project=chromium
npx playwright test --project=firefox

# Run only mobile
npx playwright test --project=mobile-chrome --project=mobile-safari
```

### 9.3 Browser-Specific Test Logic

```typescript
test('responsive menu behavior', async ({ page, isMobile }) => {
  await page.goto('/');

  if (isMobile) {
    // Mobile: hamburger menu
    await page.getByRole('button', { name: 'Menu' }).click();
    await expect(page.getByRole('navigation')).toBeVisible();
  } else {
    // Desktop: navigation always visible
    await expect(page.getByRole('navigation')).toBeVisible();
  }
});
```

---

## Network Interception

### 10.1 Mock API Responses

```typescript
test('display mocked product data', async ({ page }) => {
  // Mock API response
  await page.route('**/api/products', async route => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        { id: 1, name: 'Mock Widget', price: 9.99 },
        { id: 2, name: 'Mock Gadget', price: 19.99 },
      ]),
    });
  });

  await page.goto('/products');
  await expect(page.getByText('Mock Widget')).toBeVisible();
  await expect(page.getByText('$9.99')).toBeVisible();
});
```

### 10.2 Simulate Error Responses

```typescript
test('handle API errors gracefully', async ({ page }) => {
  await page.route('**/api/products', route =>
    route.fulfill({ status: 500, body: 'Internal Server Error' })
  );

  await page.goto('/products');
  await expect(page.getByText('Something went wrong')).toBeVisible();
  await expect(page.getByRole('button', { name: 'Retry' })).toBeVisible();
});
```

### 10.3 Simulate Slow Networks

```typescript
test('loading state during slow response', async ({ page }) => {
  await page.route('**/api/data', async route => {
    // Delay response by 3 seconds
    await new Promise(resolve => setTimeout(resolve, 3000));
    await route.fulfill({
      status: 200,
      body: JSON.stringify({ items: [] }),
    });
  });

  await page.goto('/data');
  // Verify loading indicator appears
  await expect(page.getByRole('progressbar')).toBeVisible();
  // Then verify it disappears when data loads
  await expect(page.getByRole('progressbar')).toBeHidden({ timeout: 10_000 });
});
```

### 10.4 Block Resources

```typescript
test('page loads without external resources', async ({ page }) => {
  // Block images, ads, analytics
  await page.route('**/*.{png,jpg,jpeg,gif,svg}', route => route.abort());
  await page.route('**/analytics/**', route => route.abort());
  await page.route('**/ads/**', route => route.abort());

  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Welcome' })).toBeVisible();
});
```

### 10.5 Test Offline Behavior

```typescript
test('offline fallback page', async ({ page, context }) => {
  await page.goto('/');
  // Cache the page, then go offline
  await context.setOffline(true);

  await page.goto('/dashboard');
  await expect(page.getByText('You are offline')).toBeVisible();

  // Come back online
  await context.setOffline(false);
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Dashboard' })).toBeVisible();
});
```

### 10.6 HAR Recording and Replay

```bash
# Record network traffic to HAR file
npx playwright test --save-har=e2e/fixtures/network.har
```

```typescript
// Replay recorded network traffic
test('replay from HAR', async ({ page }) => {
  await page.routeFromHAR('e2e/fixtures/network.har', {
    url: '**/api/**',
    update: false,  // Set to true to re-record
  });

  await page.goto('/dashboard');
  await expect(page.getByText('Recorded Data')).toBeVisible();
});
```

---

## Test Artifacts & Reporting

### 11.1 Reporter Configuration

```typescript
// playwright.config.ts
reporter: [
  // HTML report — interactive, best for local dev
  ['html', { open: 'on-failure', outputFolder: 'playwright-report' }],

  // JUnit — for CI systems (Jenkins, GitHub Actions)
  ['junit', { outputFile: 'test-results/junit.xml' }],

  // JSON — for custom dashboards
  ['json', { outputFile: 'test-results/results.json' }],

  // List — console output during run
  ['list'],

  // Dot — minimal console output
  // ['dot'],
],
```

### 11.2 Video Recording

```typescript
// playwright.config.ts
use: {
  // Record video on failure only (saves disk space)
  video: 'retain-on-failure',

  // Or always record (useful during initial test development)
  // video: 'on',

  // Video size
  video: {
    mode: 'retain-on-failure',
    size: { width: 1280, height: 720 },
  },
},
```

### 11.3 CI Artifact Upload — GitHub Actions

```yaml
# .github/workflows/e2e.yml
name: E2E Tests
on: [push, pull_request]

jobs:
  e2e:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: 20

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright browsers
        run: npx playwright install --with-deps

      - name: Run E2E tests
        run: npx playwright test
        env:
          CI: true

      - name: Upload HTML report
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 14

      - name: Upload test results (traces, screenshots, videos)
        if: failure()
        uses: actions/upload-artifact@v4
        with:
          name: test-results
          path: test-results/
          retention-days: 7
```

### 11.4 Custom Annotations for Failure Context

```typescript
test('annotated test with failure context', async ({ page }, testInfo) => {
  testInfo.annotations.push(
    { type: 'feature', description: 'Checkout Flow' },
    { type: 'severity', description: 'critical' },
  );

  await page.goto('/checkout');

  // On failure, attach the current URL and local storage
  try {
    await page.getByRole('button', { name: 'Pay' }).click();
    await expect(page).toHaveURL('/confirmation');
  } catch (error) {
    await testInfo.attach('current-url', {
      body: page.url(),
      contentType: 'text/plain',
    });
    const storage = await page.evaluate(() => JSON.stringify(localStorage));
    await testInfo.attach('localStorage', {
      body: storage,
      contentType: 'application/json',
    });
    throw error;
  }
});
```

---

## Advanced Browser Capabilities

### 13.1 Shadow DOM

Web components encapsulate DOM inside shadow roots. Use the `>> shadow=` piercing selector
to reach elements inside shadow DOM:

```typescript
// Pierce a single shadow root
const inner = page.locator('my-component >> shadow=.inner-class');
await expect(inner).toBeVisible();

// Chain through nested shadow roots
const deepElement = page.locator('outer-host >> shadow=inner-host >> shadow=.target');
await expect(deepElement).toHaveText('Expected content');

// Combine with role-based selectors inside shadow DOM
const button = page.locator('my-toolbar >> shadow=button[aria-label="Save"]');
await button.click();
```

### 13.2 WebSocket Testing

Intercept and mock WebSocket connections to test real-time features without a live server:

```typescript
test('receives real-time notifications', async ({ page }) => {
  // Intercept WebSocket connections matching a URL pattern
  await page.routeWebSocket('**/ws/notifications', (ws) => {
    ws.onMessage((message) => {
      // Echo back or respond with mock data
      if (message === 'ping') {
        ws.send('pong');
      }
    });

    // Simulate a server-sent message after connection
    setTimeout(() => {
      ws.send(JSON.stringify({ type: 'alert', text: 'New message' }));
    }, 500);
  });

  await page.goto('/dashboard');
  await expect(page.getByText('New message')).toBeVisible();
});
```

### 13.3 Geolocation and Permissions

Override geolocation and grant browser permissions to test location-aware features:

```typescript
test('shows nearby stores based on location', async ({ browser }) => {
  const context = await browser.newContext({
    geolocation: { latitude: 40.7128, longitude: -74.0060 },
    permissions: ['geolocation'],
  });
  const page = await context.newPage();

  await page.goto('/store-finder');
  await page.getByRole('button', { name: 'Use my location' }).click();
  await expect(page.getByText('Stores near New York')).toBeVisible();

  // Change location mid-test
  await context.setGeolocation({ latitude: 34.0522, longitude: -118.2437 });
  await page.getByRole('button', { name: 'Refresh' }).click();
  await expect(page.getByText('Stores near Los Angeles')).toBeVisible();

  await context.close();
});

// Grant other permissions (camera, microphone, notifications)
const context = await browser.newContext({
  permissions: ['geolocation', 'notifications'],
});
```

### 13.4 Cookie Management

Manipulate cookies directly for testing auth flows, consent banners, or session handling:

```typescript
test('respects cookie consent preferences', async ({ browser }) => {
  const context = await browser.newContext();
  const page = await context.newPage();

  // Pre-set cookies before navigation
  await context.addCookies([
    { name: 'consent', value: 'accepted', domain: 'localhost', path: '/' },
    { name: 'session_id', value: 'test-session-abc', domain: 'localhost', path: '/' },
  ]);

  await page.goto('/');
  // Consent banner should not appear since cookie is set
  await expect(page.getByRole('dialog', { name: 'Cookie consent' })).toBeHidden();

  // Read cookies to verify application behavior
  const cookies = await context.cookies();
  const trackingCookie = cookies.find(c => c.name === 'analytics_id');
  expect(trackingCookie).toBeDefined();

  // Clear cookies to simulate logged-out state
  await context.clearCookies();
  await page.reload();
  await expect(page.getByRole('link', { name: 'Sign in' })).toBeVisible();

  await context.close();
});
```

### 13.5 Drag and Drop

Test drag-and-drop interactions using the built-in `dragTo` method or manual mouse control:

```typescript
test('reorder items via drag and drop', async ({ page }) => {
  await page.goto('/kanban');

  // Simple drag-to-target
  const card = page.getByText('Task A');
  const targetColumn = page.getByTestId('column-done');
  await card.dragTo(targetColumn);
  await expect(targetColumn.getByText('Task A')).toBeVisible();
});

test('precise drag with mouse control', async ({ page }) => {
  await page.goto('/canvas-editor');

  // Manual drag for pixel-level precision or custom drag behavior
  const source = page.getByTestId('draggable-widget');
  const box = await source.boundingBox();
  if (box) {
    await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
    await page.mouse.down();
    await page.mouse.move(box.x + 200, box.y + 100, { steps: 10 });
    await page.mouse.up();
  }

  await expect(page.getByTestId('draggable-widget')).toHaveCSS('transform', /translate/);
});
```

### 13.6 Performance Metrics

Collect JavaScript heap size, DOM node counts, and code coverage for performance budgets:

```typescript
test('page meets performance budget', async ({ page }) => {
  await page.goto('/');

  // Collect CDP metrics (Chromium only)
  const client = await page.context().newCDPSession(page);
  await client.send('Performance.enable');
  const { metrics } = await client.send('Performance.getMetrics');

  const jsHeap = metrics.find(m => m.name === 'JSHeapUsedSize');
  const domNodes = metrics.find(m => m.name === 'Nodes');

  // Assert against performance budgets
  expect(jsHeap?.value).toBeLessThan(50 * 1024 * 1024); // < 50MB JS heap
  expect(domNodes?.value).toBeLessThan(1500);            // < 1500 DOM nodes
});

test('measure JS coverage', async ({ page }) => {
  // Start JS coverage collection
  await page.coverage.startJSCoverage();
  await page.goto('/');
  await page.getByRole('link', { name: 'Features' }).click();

  const coverage = await page.coverage.stopJSCoverage();

  // Calculate total bytes vs used bytes
  let totalBytes = 0;
  let usedBytes = 0;
  for (const entry of coverage) {
    totalBytes += entry.text.length;
    for (const range of entry.ranges) {
      usedBytes += range.end - range.start;
    }
  }

  const usagePercent = (usedBytes / totalBytes) * 100;
  console.log(`JS coverage: ${usagePercent.toFixed(1)}% of ${(totalBytes / 1024).toFixed(0)}KB used`);
  expect(usagePercent).toBeGreaterThan(50); // At least 50% of loaded JS is used
});
```

Note: `page.coverage` and CDP sessions are **Chromium-only** features. Gate these tests to run
only against the Chromium project in your Playwright config.

---