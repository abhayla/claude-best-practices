// Tiny Express server for the playwright-demo fixture.
// Every response branch is controlled by the DEMO_SCENARIO env var so the
// Playwright specs can exercise every pipeline path: pass, broken-locator,
// timing, visual-change, logic, flaky, infra.
//
// This file is intentionally framework-free (no bundler, no TypeScript) so
// the fixture starts in under a second.

import express from 'express';
import { readFile } from 'node:fs/promises';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const SCENARIO = process.env.DEMO_SCENARIO || 'pass';
const PORT = Number(process.env.PORT || 4317);

const app = express();

// Health endpoint for Playwright's webServer.url probe.
app.get('/health', (_req, res) => {
  res.json({ status: 'ok', scenario: SCENARIO });
});

// Static HTML with DEMO_SCENARIO substitutions.
// We inline the scenario into the page so each test's DOM matches its
// scenario without needing client-side fetch for config.
async function renderPage(pageName, res) {
  const path = resolve(__dirname, `${pageName}.html`);
  const raw = await readFile(path, 'utf8');
  const body = raw.replace(/__SCENARIO__/g, SCENARIO);
  res.type('html').send(body);
}

app.get('/', (_req, res) => renderPage('index', res));
app.get('/dashboard', (_req, res) => renderPage('dashboard', res));
app.get('/checkout', (_req, res) => renderPage('checkout', res));

// API endpoints consumed by the SPA pages.
app.get('/api/users', (_req, res) => {
  if (SCENARIO === 'logic') {
    // LOGIC_BUG: API drops the email field, violating the schema contract.
    return res.json({
      users: [
        { id: 1, name: 'Alice' },
        { id: 2, name: 'Bob' },
      ],
    });
  }
  res.json({
    users: [
      { id: 1, name: 'Alice', email: 'alice@example.test' },
      { id: 2, name: 'Bob', email: 'bob@example.test' },
    ],
  });
});

app.get('/api/orders', async (_req, res) => {
  if (SCENARIO === 'infra') {
    // INFRASTRUCTURE: simulate upstream unavailable.
    return res.status(503).json({ error: 'upstream unavailable' });
  }
  // TIMING: simulate a slow upstream that exceeds Playwright's default
  // expect auto-retry timeout (5000ms). At 3000ms the auto-retry absorbed
  // the delay and tests passed when they should fail — runtime verification
  // (2026-04-22) caught this as Bug 13. 8000ms puts the delay firmly
  // outside the auto-retry window so the test deterministically fails,
  // letting the healer exercise its TIMING classification path.
  if (SCENARIO === 'timing') {
    const TIMING_DELAY_MS = 8000;  // MUST stay > Playwright's expect timeout
    await new Promise((r) => setTimeout(r, TIMING_DELAY_MS));
  }
  res.json({
    orders: [
      { id: 'O-1', total: 42.0, status: 'paid' },
      { id: 'O-2', total: 17.5, status: 'pending' },
    ],
  });
});

// Flaky handler — simulates a genuinely intermittent failure so the
// pipeline's quarantine + flakiness_score + probe-run logic gets exercised.
//
// Earlier design used `counter % 2 === 0` (fail on EVEN requests). A single
// test run makes one /api/metric request per fresh-server lifetime, which
// always gives counter=1 (odd) → no failure ever fires. The test therefore
// silently passed despite being named "flaky". Runtime verification
// (2026-04-22) caught this — Bug 14 in the runtime report.
//
// New design: Math.random() < 0.5 — each request has an independent 50%
// chance of failing. Single-request runs can fail on the first try, and
// repeated runs across multiple pipeline invocations accumulate a real
// flakiness_score that crosses the quarantine threshold (0.7 by default).
let flakyCounter = 0;
app.get('/api/metric', (_req, res) => {
  if (SCENARIO === 'flaky') {
    flakyCounter += 1;
    // 50% chance on each request — genuinely intermittent.
    if (Math.random() < 0.5) {
      return res.status(500).json({ error: 'transient metric compute failure' });
    }
  }
  res.json({ counter: flakyCounter, value: 123 });
});

app.listen(PORT, () => {
  process.stdout.write(`[demo] listening on http://localhost:${PORT} (scenario=${SCENARIO})\n`);
});
