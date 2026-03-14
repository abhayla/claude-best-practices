---
name: perf-test
description: >
  Run performance tests using k6 load testing, Lighthouse web performance audits,
  and bundle size analysis. Extracts NFR thresholds from PRDs, compares results
  against baselines, and flags regressions with CI-ready fail thresholds.
triggers:
  - performance test
  - load test
  - k6
  - lighthouse
  - bundle size
  - web performance
  - perf regression
  - nfr thresholds
allowed-tools: "Bash Read Write Edit Grep Glob Agent"
argument-hint: "<project directory, PRD path, or baseline results path>"
version: "1.0.0"
type: workflow
---

# Performance Testing — k6 + Lighthouse + Bundle Analysis

Run load tests, web performance audits, and bundle analysis with baseline comparison and NFR-driven thresholds.

**Input:** $ARGUMENTS

---

## STEP 1: Extract NFR Thresholds from PRD

Scan the project for PRD, requirements, or NFR documents and extract performance targets:

```bash
# Search for NFR / performance requirements in common locations
find . -type f \( -name "*.md" -o -name "*.txt" -o -name "*.pdf" \) \
  | xargs grep -li -E "(NFR|non.?functional|performance.?requirement|SLA|latency|throughput|response.?time)" 2>/dev/null
```

Extract and normalize thresholds into a structured format:

```markdown
## Extracted NFR Thresholds

| Metric | Target | Source |
|--------|--------|--------|
| p95 response time | < 500ms | PRD section 4.2 |
| p99 response time | < 1500ms | PRD section 4.2 |
| Error rate | < 1% | SLA document |
| Throughput | >= 200 rps | PRD section 4.2 |
| Lighthouse performance score | >= 90 | PRD section 5.1 |
| LCP | < 2.5s | Web Vitals targets |
| CLS | < 0.1 | Web Vitals targets |
| Bundle size (JS) | < 250KB gzipped | PRD section 5.3 |
```

If no PRD exists, use industry-standard defaults:
- p95 latency < 500ms, p99 < 1500ms
- Error rate < 1%
- Lighthouse performance >= 90
- LCP < 2.5s, FID < 100ms, CLS < 0.1

---

## STEP 2: Write k6 Scripts

Create k6 test scripts under `perf/k6/` for each test type. All scripts import thresholds from the NFR extraction.

### 2.1 Shared Configuration

```javascript
// perf/k6/config.js
export const NFR = {
  p95_latency: 500,   // ms
  p99_latency: 1500,  // ms
  error_rate: 0.01,   // 1%
  min_rps: 200,
};

export const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";

export const defaultThresholds = {
  http_req_duration: [`p(95)<${NFR.p95_latency}`, `p(99)<${NFR.p99_latency}`],
  http_req_failed: [`rate<${NFR.error_rate}`],
  iterations: [`rate>=${NFR.min_rps}`],
};
```

### 2.2 Smoke Test (Sanity check — minimal load)

```javascript
// perf/k6/smoke.js
import http from "k6/http";
import { check } from "k6";
import { BASE_URL, defaultThresholds } from "./config.js";

export const options = {
  vus: 1,
  duration: "30s",
  thresholds: defaultThresholds,
};

export default function () {
  const res = http.get(`${BASE_URL}/health`);
  check(res, { "status is 200": (r) => r.status === 200 });
}
```

### 2.3 Load Test (Expected traffic)

```javascript
// perf/k6/load.js
import http from "k6/http";
import { check, sleep } from "k6";
import { BASE_URL, defaultThresholds } from "./config.js";

export const options = {
  stages: [
    { duration: "2m", target: 50 },   // ramp up
    { duration: "5m", target: 50 },   // steady state
    { duration: "2m", target: 0 },    // ramp down
  ],
  thresholds: defaultThresholds,
};

export default function () {
  const res = http.get(`${BASE_URL}/api/v1/resource`);
  check(res, {
    "status is 200": (r) => r.status === 200,
    "response time < 500ms": (r) => r.timings.duration < 500,
  });
  sleep(1);
}
```

### 2.4 Stress Test (Beyond expected limits)

```javascript
// perf/k6/stress.js
export const options = {
  stages: [
    { duration: "2m", target: 50 },
    { duration: "3m", target: 100 },
    { duration: "3m", target: 200 },  // beyond normal
    { duration: "3m", target: 300 },  // breaking point
    { duration: "2m", target: 0 },
  ],
  thresholds: defaultThresholds,
};
```

### 2.5 Spike Test (Sudden traffic surge)

```javascript
// perf/k6/spike.js
export const options = {
  stages: [
    { duration: "30s", target: 10 },
    { duration: "10s", target: 500 },  // spike
    { duration: "1m", target: 500 },
    { duration: "10s", target: 10 },   // drop
    { duration: "1m", target: 10 },
  ],
  thresholds: defaultThresholds,
};
```

### 2.6 Soak Test (Extended duration for memory leaks)

```javascript
// perf/k6/soak.js
export const options = {
  stages: [
    { duration: "5m", target: 50 },
    { duration: "60m", target: 50 },  // sustained load
    { duration: "5m", target: 0 },
  ],
  thresholds: defaultThresholds,
};
```

---

## STEP 3: Run k6 Load Tests

```bash
# Install k6 if not present
which k6 || brew install grafana/k6/k6  # macOS
# or: snap install k6                   # Linux
# or: choco install k6                  # Windows

# Run smoke test first (fast sanity check)
k6 run perf/k6/smoke.js --out json=perf/results/smoke.json

# Run load test
k6 run perf/k6/load.js --out json=perf/results/load.json

# Run stress test (only when smoke + load pass)
k6 run perf/k6/stress.js --out json=perf/results/stress.json
```

Save the summary output for baseline comparison:
```bash
k6 run perf/k6/load.js --summary-export=perf/results/load-summary.json
```

---

## STEP 4: Run Lighthouse Audit

```bash
# Install Lighthouse CLI
npm install -g lighthouse

# Run performance audit (headless Chrome)
lighthouse http://localhost:3000 \
  --output=json,html \
  --output-path=perf/results/lighthouse \
  --only-categories=performance \
  --chrome-flags="--headless --no-sandbox"
```

Extract and evaluate Core Web Vitals:

```markdown
## Lighthouse Results

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Performance Score | 92 | >= 90 | PASS |
| LCP (Largest Contentful Paint) | 2.1s | < 2.5s | PASS |
| FID (First Input Delay) | 45ms | < 100ms | PASS |
| CLS (Cumulative Layout Shift) | 0.05 | < 0.1 | PASS |
| TTI (Time to Interactive) | 3.2s | < 3.8s | PASS |
| TTFB (Time to First Byte) | 180ms | < 600ms | PASS |
```

For multiple pages, run in a loop:
```bash
for url in "/" "/dashboard" "/profile" "/search"; do
  lighthouse "http://localhost:3000${url}" \
    --output=json \
    --output-path="perf/results/lighthouse-$(echo $url | tr '/' '-').json" \
    --only-categories=performance \
    --chrome-flags="--headless --no-sandbox"
done
```

---

## STEP 5: Analyze Bundle Size

Detect the bundler and run the appropriate analysis:

| Indicator | Bundler | Analysis Tool |
|-----------|---------|---------------|
| `webpack.config.*` | Webpack | `webpack-bundle-analyzer` |
| `vite.config.*` | Vite | `rollup-plugin-visualizer` |
| `next.config.*` | Next.js | `@next/bundle-analyzer` |
| `package.json` (any) | Any | `source-map-explorer` |

```bash
# Webpack: generate stats and analyze
npx webpack --profile --json > perf/results/webpack-stats.json
npx webpack-bundle-analyzer perf/results/webpack-stats.json --mode static \
  --report perf/results/bundle-report.html --no-open

# Vite / Rollup: use source-map-explorer on the build output
npm run build
npx source-map-explorer dist/assets/*.js --json perf/results/bundle-analysis.json

# Next.js: use built-in analyzer
ANALYZE=true npm run build
```

Record bundle sizes:
```markdown
## Bundle Size Analysis

| Bundle | Raw | Gzipped | Budget | Status |
|--------|-----|---------|--------|--------|
| main.js | 480KB | 145KB | < 250KB gz | PASS |
| vendor.js | 320KB | 98KB | < 150KB gz | PASS |
| CSS total | 45KB | 12KB | < 50KB gz | PASS |
| **Total JS** | **800KB** | **243KB** | **< 400KB gz** | PASS |
```

---

## STEP 6: Compare Against Baseline

Store results in `perf/baselines/` and compare on each run:

```bash
# Save current run as baseline (first time or after intentional reset)
cp perf/results/load-summary.json perf/baselines/load-summary.json

# Compare current vs baseline
cat perf/results/load-summary.json | python3 -c "
import json, sys
current = json.load(sys.stdin)
baseline = json.load(open('perf/baselines/load-summary.json'))

metrics = [
    ('p95 latency', 'http_req_duration', 'p(95)'),
    ('p99 latency', 'http_req_duration', 'p(99)'),
    ('error rate', 'http_req_failed', 'rate'),
    ('median latency', 'http_req_duration', 'med'),
]

print('| Metric | Baseline | Current | Delta | Status |')
print('|--------|----------|---------|-------|--------|')
for label, metric, stat in metrics:
    b = baseline['metrics'][metric]['values'][stat]
    c = current['metrics'][metric]['values'][stat]
    delta = ((c - b) / b) * 100 if b else 0
    status = 'REGRESSION' if delta > 10 else 'OK'
    print(f'| {label} | {b:.1f} | {c:.1f} | {delta:+.1f}% | {status} |')
"
```

Regression thresholds:
- **p95 latency**: flag if > 10% worse than baseline
- **Error rate**: flag if > 0.5% absolute increase
- **Bundle size**: flag if > 5% increase in gzipped size
- **Lighthouse score**: flag if any metric drops below target

---

## STEP 7: CI Integration

```yaml
# .github/workflows/perf-test.yml
name: Performance Tests
on:
  pull_request:
    branches: [main]
  schedule:
    - cron: "0 3 * * 1"  # weekly Monday 3am

jobs:
  k6-load-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: grafana/setup-k6-action@v1

      - name: Start application
        run: docker compose up -d && sleep 10

      - name: Run smoke test
        run: k6 run perf/k6/smoke.js --summary-export=perf/results/smoke-summary.json

      - name: Run load test
        run: k6 run perf/k6/load.js --summary-export=perf/results/load-summary.json

      - name: Compare baseline
        run: python3 perf/compare-baseline.py

      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: perf-results
          path: perf/results/

  lighthouse:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: treosh/lighthouse-ci-action@v12
        with:
          urls: |
            http://localhost:3000/
            http://localhost:3000/dashboard
          budgetPath: perf/lighthouse-budget.json
          uploadArtifacts: true

  bundle-size:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm run build
      - name: Check bundle size
        run: npx bundlesize --config perf/bundlesize.config.json
```

Budget config for Lighthouse CI:
```json
// perf/lighthouse-budget.json
[{
  "path": "/*",
  "resourceSizes": [
    { "resourceType": "script", "budget": 250 },
    { "resourceType": "stylesheet", "budget": 50 },
    { "resourceType": "total", "budget": 500 }
  ],
  "timings": [
    { "metric": "largest-contentful-paint", "budget": 2500 },
    { "metric": "cumulative-layout-shift", "budget": 0.1 },
    { "metric": "interactive", "budget": 3800 }
  ]
}]
```

---

## STEP 8: Output Summary

```markdown
## Performance Test Summary

### k6 Load Test Results
| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| p95 latency | 320ms | < 500ms | PASS |
| p99 latency | 890ms | < 1500ms | PASS |
| Error rate | 0.2% | < 1% | PASS |
| Throughput | 245 rps | >= 200 rps | PASS |

### Lighthouse Scores
| Page | Perf | LCP | FID | CLS |
|------|------|-----|-----|-----|
| / | 94 | 1.8s | 32ms | 0.02 |
| /dashboard | 88 | 2.9s | 55ms | 0.08 |

### Bundle Size
| Bundle | Gzipped | Budget | Status |
|--------|---------|--------|--------|
| Total JS | 198KB | < 250KB | PASS |

### Baseline Comparison
| Metric | Baseline | Current | Delta |
|--------|----------|---------|-------|
| p95 latency | 310ms | 320ms | +3.2% OK |
| Bundle size | 192KB | 198KB | +3.1% OK |

### Regressions Found
- /dashboard LCP is 2.9s (target < 2.5s) — investigate image loading
```

---

## MUST DO

- Always extract NFR thresholds from project requirements before writing tests
- Always run smoke tests before load/stress tests — fail fast on broken endpoints
- Always store results in `perf/results/` and baselines in `perf/baselines/`
- Always compare against baseline and flag regressions with percentage deltas
- Always test against a production-like environment (not dev mode with hot reload)
- Always include both server-side (k6) and client-side (Lighthouse) metrics
- Always generate machine-readable output (JSON) alongside human-readable reports
- Always run Lighthouse with `--chrome-flags="--headless --no-sandbox"` in CI

## MUST NOT DO

- MUST NOT run soak tests in CI — they take 60+ minutes; run them in dedicated environments instead
- MUST NOT use `k6 cloud` without confirming the team has a Grafana Cloud account
- MUST NOT hardcode absolute URLs in k6 scripts — use `__ENV.BASE_URL` with a fallback
- MUST NOT compare Lighthouse scores across different machines — hardware variance skews results; compare against same-machine baselines instead
- MUST NOT skip bundle analysis for frontend projects — bundle regressions compound silently
- MUST NOT treat Lighthouse scores as pass/fail in isolation — Core Web Vitals (LCP, FID, CLS) are the actionable metrics
- MUST NOT commit large JSON result files to git — add `perf/results/` to `.gitignore` and upload as CI artifacts instead
