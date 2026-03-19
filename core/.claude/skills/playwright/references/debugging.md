# Debugging — MCP Execution Debugger

Reference material for debugging Playwright tests, including interactive debugging,
trace viewer, failure diagnostics, and network request logging.

---


### 8.1 Interactive Debugging

```typescript
test('debug this flow', async ({ page }) => {
  await page.goto('/checkout');

  // Pause execution — opens Playwright Inspector
  await page.pause();

  // Continue stepping through the test in the Inspector UI
  await page.getByRole('button', { name: 'Pay' }).click();
});
```

Run with headed mode for visual debugging:

```bash
# Run with browser visible
npx playwright test --headed

# Run with Playwright Inspector (step-through debugger)
npx playwright test --debug

# Debug a specific test
npx playwright test auth.spec.ts:15 --debug
```

### 8.2 Trace Viewer

```bash
# Enable trace collection
npx playwright test --trace on

# View traces after test run
npx playwright show-trace test-results/auth-spec-ts/trace.zip
```

The trace viewer shows:
- Step-by-step action log with timestamps
- DOM snapshots before and after each action
- Network requests and responses
- Console logs and errors
- Source code location for each step

### 8.3 Capture Diagnostics on Failure

```typescript
test.afterEach(async ({ page }, testInfo) => {
  if (testInfo.status !== 'passed') {
    // Capture console errors
    const consoleLogs: string[] = [];
    page.on('console', msg => consoleLogs.push(`${msg.type()}: ${msg.text()}`));

    // Attach screenshot with annotations
    const screenshot = await page.screenshot({ fullPage: true });
    await testInfo.attach('failure-screenshot', {
      body: screenshot,
      contentType: 'image/png',
    });

    // Attach DOM snapshot
    const html = await page.content();
    await testInfo.attach('page-html', {
      body: html,
      contentType: 'text/html',
    });

    // Attach console logs
    await testInfo.attach('console-logs', {
      body: consoleLogs.join('\n'),
      contentType: 'text/plain',
    });
  }
});
```

### 8.4 Network Request Logging

```typescript
test('debug network issues', async ({ page }) => {
  const requests: string[] = [];
  const failures: string[] = [];

  page.on('request', req => requests.push(`${req.method()} ${req.url()}`));
  page.on('requestfailed', req =>
    failures.push(`FAILED: ${req.method()} ${req.url()} - ${req.failure()?.errorText}`)
  );
  page.on('response', resp => {
    if (resp.status() >= 400) {
      failures.push(`${resp.status()} ${resp.url()}`);
    }
  });

  await page.goto('/dashboard');
  // ... test actions ...

  // Log for debugging
  console.log('All requests:', requests);
  if (failures.length) {
    console.log('Failed requests:', failures);
  }
});
```

---