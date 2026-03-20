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
version: "1.1.0"
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


**Read:** `references/write-k6-scripts.md` for detailed step 2: write k6 scripts reference material.

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


**Read:** `references/performance-test-summary.md` for detailed performance test summary reference material.

## Baseline Management Policy

Performance baselines are critical reference points. Uncontrolled updates mask regressions and erode the value of baseline comparisons.

### 1. No Auto-Update in CI

Baselines MUST NOT be auto-updated in CI pipelines. Updating baselines requires an explicit `--update-baseline` flag passed by a developer who has reviewed the performance delta. CI runs compare against the existing baseline and report regressions — they never silently adopt new numbers as the baseline.

```bash
# Manual baseline update (developer-initiated only)
python3 perf/compare-baseline.py --update-baseline

# CI mode (default): compare only, never update
python3 perf/compare-baseline.py
```

### 2. Delta Logging Before Update

Before any baseline update, log the delta between old and new values as a permanent record. This creates an audit trail of intentional performance changes:

```bash
# Append delta to persistent log before overwriting baseline
python3 -c "
import json, datetime
old = json.load(open('perf/baselines/load-summary.json'))
new = json.load(open('perf/results/load-summary.json'))
entry = {
    'date': datetime.datetime.utcnow().isoformat() + 'Z',
    'metrics': {}
}
for metric in ['http_req_duration', 'http_req_failed']:
    for stat in ['p(95)', 'p(99)', 'med', 'rate']:
        key = f'{metric}.{stat}'
        old_val = old.get('metrics', {}).get(metric, {}).get('values', {}).get(stat)
        new_val = new.get('metrics', {}).get(metric, {}).get('values', {}).get(stat)
        if old_val is not None and new_val is not None:
            entry['metrics'][key] = {'old': old_val, 'new': new_val, 'delta_pct': round(((new_val - old_val) / old_val) * 100, 2) if old_val else 0}
import os
log_path = 'perf/baselines/update-log.jsonl'
os.makedirs(os.path.dirname(log_path), exist_ok=True)
with open(log_path, 'a') as f:
    f.write(json.dumps(entry) + '\n')
print('Baseline delta logged to ' + log_path)
"
```

### 3. Stale Baseline Re-Benchmark

Baselines older than 90 days should trigger a full re-benchmark. Stale baselines may reflect infrastructure, dependency, or runtime conditions that no longer apply:

```bash
# Check baseline age
BASELINE_AGE_DAYS=$(python3 -c "
import os, datetime
mtime = os.path.getmtime('perf/baselines/load-summary.json')
age = (datetime.datetime.now() - datetime.datetime.fromtimestamp(mtime)).days
print(age)
")

if [ "$BASELINE_AGE_DAYS" -gt 90 ]; then
  echo "WARNING: Baseline is ${BASELINE_AGE_DAYS} days old (> 90 day threshold). Run a full re-benchmark before trusting comparisons."
fi
```

When a baseline exceeds 90 days, run all test types (smoke, load, stress) and update the baseline with the `--update-baseline` flag after verifying results are consistent across multiple runs.

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
