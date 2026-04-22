# Playwright Demo Fixture

Synthetic Playwright project used to exercise every branch of the testing
pipeline end-to-end. Drives `scripts/tests/test_pipeline_e2e.py`.

## What this fixture exercises

Each `*.spec.ts` file is keyed to one pipeline branch. The test behavior is
controlled by the `DEMO_SCENARIO` env var, which causes the tiny Express
server to toggle its responses or UI to trigger the targeted failure mode.

| `DEMO_SCENARIO` | Spec file | Exercises |
|---|---|---|
| `pass` (default) | `home.spec.ts` | Baseline: all pipeline steps PASS |
| `broken-locator` | `dashboard.spec.ts` | Element renamed → BROKEN_LOCATOR → auto-healed via SELECTOR fix |
| `timing` | `checkout.spec.ts` | Delayed element → TIMING → auto-healed via event-driven wait |
| `visual-change` | `visual.spec.ts` | Intentional UI drift → EXPECTED_CHANGE → NEEDS_REVIEW |
| `logic` | `logic.spec.ts` | API returns wrong data → LOGIC_BUG → known_issues + GitHub Issue |
| `flaky` | `flaky.spec.ts` | 50% pass rate → FLAKY_TEST → quarantine path |
| `infra` | `infra.spec.ts` | Fake upstream down → INFRASTRUCTURE → env reset attempt |

## Running standalone

```bash
cd scripts/tests/fixtures/playwright-demo
npm install
npx playwright install chromium
DEMO_SCENARIO=pass npx playwright test
```

The `webServer` declaration in `playwright.config.ts` auto-starts the
Express server on `http://localhost:4317` (uncommon port to avoid conflicts
with other local dev servers).

## Running through the pipeline

```bash
cd scripts/tests/fixtures/playwright-demo
DEMO_SCENARIO=pass /e2e-visual-run      # standalone slash command
```

Or, from the hub root, let `scripts/tests/test_pipeline_e2e.py` drive the
parametrized scenarios.

## File layout

```
playwright-demo/
  package.json             # express + @playwright/test
  playwright.config.ts     # webServer, outputDir, screenshot:on
  app/
    server.js              # tiny Express app, DEMO_SCENARIO-aware
    index.html             # home page
    dashboard.html         # dashboard with elements that can be renamed
    checkout.html          # checkout with optional setTimeout delay
  tests/
    home.spec.ts           # pass scenario
    dashboard.spec.ts      # broken-locator scenario
    checkout.spec.ts       # timing scenario
    visual.spec.ts         # visual-change scenario
    logic.spec.ts          # logic scenario
    flaky.spec.ts          # flaky scenario
    infra.spec.ts          # infra scenario
  .gitignore
```

Everything under `test-results/`, `test-evidence/`, `node_modules/`,
`.pipeline/`, `__snapshots__/` (except committed baselines) is gitignored.
