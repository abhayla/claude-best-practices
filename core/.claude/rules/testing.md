---
description: Testing conventions and best practices.
globs: ["**/test_*", "**/*_test.*", "**/tests/**", "**/*.test.*", "**/*.spec.*"]
---

# Testing Rules

## General Principles

1. **Test Isolation** — Each test should be independent; no shared mutable state
2. **Descriptive Names** — Test names should describe the scenario and expected outcome: `test_<method>_<condition>_<expected>` (Python), `should <verb> when <condition>` (JS)
3. **Arrange-Act-Assert** — Structure tests clearly with setup, action, and verification
4. **One Assertion Focus** — Each test should verify one behavior (multiple asserts OK if related)
5. **No Test Interdependence** — Tests must pass in any order; use `--randomly` / `--randomize` to verify
6. **No Empty Assertions** — Every test MUST contain at least one meaningful assertion. Tests with no `assert` / `expect` / `verify`, or with trivial assertions (`assert True`, `expect(1).toBe(1)`) are bugs — they pass without testing anything
7. **CI Is Mandatory** — PRs MUST NOT merge with failing tests. MUST NOT use `--no-verify`, `[skip ci]`, or `[ci skip]` to bypass test gates. If a test blocks CI, fix the test — do not skip the gate

## Test Categories & Pyramid

| Category | Purpose | Speed | Target Ratio |
|----------|---------|-------|-------------|
| Unit | Individual functions/methods | Fast (ms) | ~70% of tests |
| Integration | Component interactions | Medium (seconds) | ~20% of tests |
| E2E | Full user flows | Slow (minutes) | ~10% of tests |

If E2E tests outnumber unit tests, the pyramid is inverted — refactor to push coverage down to unit level. Prefer unit tests for logic, integration tests for boundaries, E2E tests only for critical user flows.

## Running Tests

- Run targeted tests first (faster feedback)
- Run full suite before committing
- Use `-x` flag to stop on first failure when debugging

## Fixtures & Test Data

- Use factories/fixtures for test data — don't hardcode
- Clean up test data in teardown
- Use in-memory databases for unit tests where possible
- Mock external services (APIs, email, file systems)

## Handling Failures

- Distinguish real failures from flaky tests
- Fix flaky tests immediately — they erode confidence
- Never `@skip` or `@ignore` a test without a tracking issue
- Re-run flaky tests 2-3 times before investigating

## Flaky Test Prevention

- **Use auto-wait over timeouts** — Never use `sleep(2)` or fixed delays. Use framework-provided waiters: `waitFor`, `eventually`, `toBeVisible`. Fixed delays are the #1 cause of flaky tests.
- **Isolate test state** — Each test gets its own database transaction, browser context, or temp directory. Never share mutable state across tests. Use `beforeEach` setup, not `beforeAll`.
- **Mock external dependencies** — Network calls to third-party APIs, email services, payment providers MUST be mocked. External service flakiness should not fail your tests.
- **Use deterministic test data** — No `random()`, no `Date.now()` in assertions, no reliance on database auto-increment order. Use factories with fixed seeds.
- **Control time** — Use clock mocking (`jest.useFakeTimers`, `freezegun`, `timecop`) for time-dependent logic. Never assert against wall clock time.
- **Avoid order dependence** — Tests MUST pass when run individually, in reverse order, or in random order. Use `--randomize` flag to verify.

## Flaky Test Detection & Quarantine

When a test fails intermittently, follow this workflow:

### Detection
```bash
# Python: run tests N times to identify flakes
pytest tests/ --count=5 -x  # (requires pytest-repeat)

# JavaScript: run tests with retries to find flakes
npx jest --forceExit --detectOpenHandles 2>&1 | grep -E "FAIL|PASS"

# Kotlin/Android: run connected tests multiple times
./gradlew :app:connectedDebugAndroidTest -Pandroid.testInstrumentationRunnerArguments.iterations=3

# Any framework: run full suite 3x, diff results
for i in 1 2 3; do pytest tests/ --tb=line -q 2>&1 | tail -5 >> run_$i.txt; done
diff run_1.txt run_2.txt
```

### Classification

| Pattern | Likely Cause | Fix |
|---------|-------------|-----|
| Fails on CI but passes locally | Environment difference (timing, resources) | Use auto-wait, increase CI resources |
| Fails randomly ~10% of runs | Race condition or shared state | Isolate state, add synchronization |
| Fails only when run with other tests | Test pollution (shared DB, global state) | Reset state in beforeEach/teardown |
| Fails at specific times | Time-dependent logic | Mock clocks, avoid real timestamps |
| Fails after N minutes | Timeout or resource leak | Fix leak, increase timeout with logging |

### Quarantine Workflow

1. **Tag the flaky test** — mark with metadata so CI tracks it separately:
   ```python
   # Python
   @pytest.mark.flaky(reruns=3, reason="JIRA-1234: intermittent timeout")

   # JavaScript
   test.retry(3)  // Jest/Vitest

   # Kotlin
   @RepeatedTest(3)  // or @FlakyTest annotation
   ```
2. **Log a tracking issue** — every quarantined test MUST have a linked issue
3. **Separate CI reporting** — flaky tests run but don't block the pipeline:
   ```yaml
   # GitHub Actions: separate flaky test job
   flaky-tests:
     continue-on-error: true
     steps:
       - run: pytest -m flaky --reruns 3
   ```
4. **Fix within 1 sprint** — quarantine is temporary, not permanent. Review weekly.
5. **Remove quarantine after fix** — verify with 10+ consecutive clean runs

### Metrics to Track

| Metric | Healthy | Action Needed |
|--------|---------|---------------|
| Flaky test count | < 3% of suite | Prioritize fixes if > 5% |
| Mean time to fix flake | < 1 sprint | Escalate if backlog grows |
| Tests in quarantine | < 10 | Review quarantine list weekly |
| False failure rate in CI | < 2% | Investigate if > 5% |

## Coverage Regression Prevention

- Coverage MUST NOT decrease on a PR. Use ratcheting: the new coverage must be >= the previous value.
- Enforce via CI: `--cov-fail-under` (pytest), `coverageThreshold` (Jest/Vitest), `jacocoTestReport` minimum.
- New/changed code MUST have >= 80% line coverage and >= 70% branch coverage.
- Security-critical paths (auth, payment, crypto) MUST have >= 90% coverage — no exceptions.

## Test Timeouts

- Unit tests: MUST complete in < 5 seconds per test. Flag any unit test exceeding 2 seconds.
- Integration tests: MUST complete in < 30 seconds per test.
- E2E tests: MUST complete in < 5 minutes per test.
- Set framework-level defaults: `timeout = 5000` (Vitest/Jest), `--timeout=5000` (pytest-timeout).
- If a test needs a longer timeout, it belongs in a higher test category — not a longer timeout.

## Parallel Test Safety

- Tests MUST be safe to run in parallel (`pytest-xdist`, `jest --maxWorkers`, `vitest --pool=threads`).
- MUST NOT rely on fixed port numbers, shared temp files, or global singletons across tests.
- Database tests MUST use per-test transactions or isolated schemas — never a shared database state.
- If a test cannot run in parallel, mark it explicitly (`@pytest.mark.serial`, `test.concurrent.skip`).

## Security Testing

- Auth/authorization endpoints MUST have tests for: no token (401), expired token (401), wrong scope (403), valid token (200).
- Input validation endpoints MUST have tests for: SQL injection payloads, XSS strings, oversized payloads, malformed JSON.
- Payment/financial endpoints MUST have tests for: negative amounts, zero amounts, currency edge cases, idempotency.
- New security-critical paths without tests MUST block the PR.

## Mock Drift Prevention

- Unit-level mocks MUST match the real implementation's return type/shape. Use typed mocks where possible (`jest.mocked<T>()`, `mocker.patch() -> MagicMock(spec=RealClass)`).
- Periodically verify mocks against real implementations — run integration tests alongside unit tests in CI.
- When a real API changes, update all mocks that reference it in the same PR. Never change an API without updating its mocks.
- Contract tests (Pact/Specmatic) MUST be used for cross-service API boundaries — unit mocks alone are insufficient.

## Test Pollution Detection

- Run tests with `--randomly` (pytest-randomly) or `--randomize` (Jest) in CI at least weekly.
- When a test fails only when run with other tests, isolate it: run the failing test alone, then with its predecessor. Fix the shared state leak.
- MUST NOT use `beforeAll` / `session`-scoped fixtures for mutable state — use `beforeEach` / `function`-scoped instead.

## Warnings as Signals

- `ResourceWarning` (unclosed files/connections), `DeprecationWarning`, and framework warnings MUST NOT be ignored.
- Configure `-W error::ResourceWarning` (Python) or equivalent to promote resource leaks to failures.
- Review `DeprecationWarning` before each major dependency upgrade — they signal upcoming breakage.

## Documentation

- Add brief comments explaining non-obvious test setups
- Document test fixtures and their purpose
- Keep test helper functions close to where they're used

## Observability Verification

### Structured Log Assertions

Verify logs emitted during test execution contain required fields:

```python
# Assert structured logs have required fields
def assert_structured_log(log_line):
    log = json.loads(log_line)
    required_fields = ["timestamp", "level", "service", "trace_id", "message"]
    for field in required_fields:
        assert field in log, f"Structured log missing '{field}'"

    # No PII in logs
    pii_patterns = ["password", "ssn", "credit_card", "secret"]
    log_str = json.dumps(log).lower()
    for pattern in pii_patterns:
        assert pattern not in log_str, f"PII field '{pattern}' found in log"
```

### Correlation ID Flow

Every request must carry a consistent trace/correlation ID across all services:

```python
def test_correlation_id_propagated():
    corr_id = "test-corr-" + str(uuid.uuid4())
    response = client.get("/api/users", headers={"X-Correlation-ID": corr_id})

    # Response should echo correlation ID
    assert response.headers.get("X-Correlation-ID") == corr_id

    # Logs should contain the same correlation ID
    logs = get_captured_logs()
    corr_logs = [l for l in logs if corr_id in l]
    assert len(corr_logs) > 0, "Correlation ID not found in service logs"
```

### Metrics Emission

Verify that custom metrics are emitted during operations:

```python
def test_request_metrics_emitted():
    # Make a request
    response = client.get("/api/users")

    # Check Prometheus/OpenTelemetry metrics endpoint
    metrics = client.get("/metrics").text
    assert 'http_requests_total{method="GET",path="/api/users"' in metrics
    assert 'http_request_duration_seconds' in metrics
```

## Structured Test Output

All verification skills (`auto-verify`, `fix-loop`, `android-run-e2e`, `playwright`, `flutter-e2e-test`, `verify-screenshots`, `perf-test`, `contract-test`, `code-quality-gate`, `db-migrate-verify`) MUST produce a machine-readable JSON summary alongside their human-readable report. This enables stage gates to programmatically determine pass/fail.

### Output Format

Write to `test-results/{skill-name}.json` after each verification run:

```json
{
  "skill": "auto-verify",
  "timestamp": "2026-03-14T10:30:00Z",
  "result": "PASSED",
  "summary": {
    "total": 42,
    "passed": 40,
    "failed": 0,
    "skipped": 2,
    "flaky": 0
  },
  "quality_gate": "PASSED",
  "contract_check": "SKIPPED",
  "perf_baseline": "SKIPPED",
  "failures": [],
  "warnings": ["2 tests skipped: test_legacy_api, test_deprecated_endpoint"],
  "duration_ms": 12340
}
```

### Result Values

**CRITICAL:** The field name `result` is the canonical gate signal. All skills
MUST use `result` (not `status`, `verdict`, or `outcome`). Downstream gate
checks parse this exact field name. Changing it breaks the entire pipeline.

| Field | Values | Meaning |
|-------|--------|---------|
| `result` | `PASSED`, `FAILED`, `FIXED` | Overall verification outcome |
FLAKY tests are reported as FAILED with `flaky_detected: true`. There is no separate FLAKY result — flaky is a failure category, not an acceptable outcome.

| `quality_gate` | `PASSED`, `WARNED`, `FAILED`, `SKIPPED` | Code quality check result |
| `contract_check` | `PASSED`, `FAILED`, `SKIPPED` | Contract test result |
| `perf_baseline` | `PASSED`, `REGRESSED`, `SKIPPED` | Performance baseline comparison |

### Failure Entry Format

```json
{
  "test": "test_create_user",
  "category": "ASSERTION_FAILURE",
  "file": "tests/test_users.py:42",
  "message": "Expected status 201, got 422",
  "confidence": "HIGH"
}
```

### Stage Gate Usage

The stage gate aggregator is the SINGLE source of truth for pipeline pass/fail decisions. Individual skill results are inputs to the aggregator, not standalone verdicts. No downstream stage should read a single skill's JSON file to make a go/no-go decision — the aggregator's output is the only authoritative verdict.

Downstream stages read ALL `test-results/*.json` files to determine if verification passed:

```bash
# Aggregate ALL verification results — the union of failures determines the verdict
python -c "
import json, glob, sys, os

result_files = glob.glob('test-results/*.json')
if not result_files:
    print('ERROR: No test-results/*.json files found — cannot determine verification status')
    sys.exit(1)

results = []
for f in result_files:
    try:
        results.append(json.load(open(f)))
    except (json.JSONDecodeError, KeyError) as e:
        print(f'ERROR: Could not parse {f}: {e}')
        sys.exit(1)

# Check for contradictory results across skills
statuses = {r['skill']: r['result'] for r in results}
pass_skills = {s for s, v in statuses.items() if v in ('PASSED', 'FIXED')}
fail_skills = {s for s, v in statuses.items() if v == 'FAILED'}

# Detect contradictions: if skill A says PASSED but skill B says FAILED for overlapping concerns
contradictions = []
if 'auto-verify' in pass_skills and 'contract-test' in fail_skills:
    contradictions.append('auto-verify reports PASSED but contract-test reports FAILED — investigate API compatibility')
if 'auto-verify' in pass_skills and 'perf-test' in fail_skills:
    contradictions.append('auto-verify reports PASSED but perf-test reports FAILED — investigate performance regression')

# Report all failures (union, not first-match)
all_failures = []
for r in results:
    if r['result'] == 'FAILED':
        all_failures.append(r)
        print(f\"BLOCKED: {r['skill']} — {r['result']}\")
        for failure in r.get('failures', []):
            print(f\"  - {failure.get('test', 'unknown')}: {failure.get('message', 'no message')}\")

for c in contradictions:
    print(f'CONTRADICTION: {c}')

if all_failures or contradictions:
    print(f'\\nTotal blocked skills: {len(all_failures)}, contradictions: {len(contradictions)}')
    sys.exit(1)

print(f'All {len(results)} verification gates passed')
"
```

The aggregator MUST read ALL JSON files and report the union of failures. Skipping a file or stopping at the first failure masks downstream problems.

### Directory Convention

```
test-results/           # gitignored — generated per run
  auto-verify.json
  fix-loop.json
  code-quality-gate.json
  contract-test.json
  perf-test.json
  db-migrate-verify.json
```

Add `test-results/` to `.gitignore` — these are ephemeral per-run artifacts.

### Screenshot Proof Archive

When `--capture-proof` is enabled (default: true), E2E/UI tests capture
screenshots on every test (pass and fail) as visual evidence. Use
`--no-capture-proof` to disable. The archive is run-scoped and ephemeral.

If the project has no E2E/UI tests, `--capture-proof` is a no-op — the manifest
will have an empty `screenshots` array and visual review will SKIP (not block).

#### run_id Format

Format: `{ISO-8601-timestamp}_{7-char-git-sha}`

Examples:
- `2026-03-17T14:30:12Z_abc1234`
- `2026-03-17T09:15:00Z_f7e2a91`
- `2026-01-05T22:00:45Z_0d3c8b2`

The short SHA is always 7 characters (git's default `--short` length). The
timestamp uses UTC with seconds precision. No colons in the timestamp when
used as a directory name — replace `:` with `-` for filesystem safety:
`2026-03-17T14-30-12Z_abc1234`.

#### Directory Convention

```
test-evidence/                  # gitignored — generated per pipeline run
  {run_id}/                     # e.g., 2026-03-17T14-30-12Z_abc1234
    screenshots/                # All captured screenshots (PNG, max 1440x900)
      {test_name}.pass.png
      {test_name}.fail.png
      {test_name}.{platform}.pass.png  # Multi-platform runs
      {test_name}.iter{N}.fail.png     # Fix-loop iteration screenshots
    manifest.json               # Index of all screenshots
    visual-review.json          # AI multimodal review verdicts
```

Add `test-evidence/` and `test-results/` to `.gitignore`.

**Screenshot format:** PNG, max resolution 1440x900 (for optimal multimodal
token cost ~1,728 tokens/image). Downscale larger screenshots before archiving.

**Retention:** `test-pipeline-agent` cleans `test-evidence/` at pipeline start.
For manual runs, only the most recent 3 `{run_id}` directories are kept —
older runs are deleted automatically when a new run starts.

#### Manifest Schema

Written by `tester-agent` after test execution. Field types annotated.

```json
{
  "run_id": "2026-03-17T14-30-12Z_abc1234",
  "capture_proof": true,
  "platforms": ["playwright-chromium", "maestro-android"],
  "screenshot_count": 50,
  "screenshots": [
    {
      "test": "test_login_success",
      "file": "tests/e2e/test_auth.py::test_login_success",
      "result": "PASSED",
      "screenshot": "screenshots/test_login_success.pass.png",
      "platform": "playwright-chromium",
      "timestamp": "2026-03-17T14:30:12Z",
      "iteration": null
    },
    {
      "test": "test_checkout_flow",
      "file": "tests/e2e/test_checkout.py::test_checkout_flow",
      "result": "FAILED",
      "screenshot": "screenshots/test_checkout_flow.iter2.fail.png",
      "platform": "playwright-chromium",
      "timestamp": "2026-03-17T14:30:45Z",
      "iteration": 2
    }
  ]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `run_id` | string | yes | Pipeline run identifier |
| `capture_proof` | boolean | yes | Always `true` when manifest exists |
| `platforms` | string[] | yes | List of test platforms used |
| `screenshot_count` | number | yes | Total screenshots captured |
| `screenshots[].test` | string | yes | Test function name |
| `screenshots[].file` | string | yes | Test file path with function |
| `screenshots[].result` | enum | yes | `"PASSED"` or `"FAILED"` |
| `screenshots[].screenshot` | string | yes | Relative path to PNG file |
| `screenshots[].platform` | string | yes | Platform that captured this |
| `screenshots[].timestamp` | string | yes | ISO-8601 capture time |
| `screenshots[].iteration` | number\|null | yes | Fix-loop iteration (null if not from fix-loop) |

#### Visual Review Schema

Written by `/auto-verify` Step 2.5. This is the **single source of truth** for
visual review results — stored at `test-evidence/{run_id}/visual-review.json`.
A summary is also embedded in `test-results/auto-verify.json` via the
`visual_review` field, but the file is authoritative.

```json
{
  "skill": "visual-proof-review",
  "run_id": "2026-03-17T14-30-12Z_abc1234",
  "timestamp": "2026-03-17T14:31:00Z",
  "screenshots_reviewed": 50,
  "screenshots_total": 50,
  "confirmed_passes": 43,
  "confirmed_failures": 5,
  "overrides": [
    {
      "test": "test_dashboard_loads",
      "original_result": "PASSED",
      "visual_verdict": "FAILED",
      "reason": "Empty table — no data rows visible",
      "screenshot": "screenshots/test_dashboard_loads.pass.png"
    }
  ],
  "flags": [
    {
      "test": "test_login_timeout",
      "original_result": "FAILED",
      "visual_observation": "Screenshot shows successful login — possible flaky",
      "screenshot": "screenshots/test_login_timeout.fail.png"
    }
  ],
  "result": "PASSED|FAILED"
}
```

| Field | Type | Description |
|-------|------|-------------|
| `result` | enum | `"PASSED"` (zero overrides) or `"FAILED"` (any override exists) |
| `overrides` | array | Tests that passed by exit code but failed visually |
| `flags` | array | Tests that failed by exit code but looked correct visually |
| `screenshots_reviewed` | number | How many screenshots were analyzed |

`/post-fix-pipeline` reads `test-evidence/{run_id}/visual-review.json` directly
and blocks commit if any overrides exist.

#### Integration with Stage Gate Aggregator

The aggregator reads `test-results/*.json` for pipeline verdicts. It does NOT
read `test-evidence/` directly. The visual review summary is embedded in
`test-results/auto-verify.json` via the `visual_review` field — this keeps
the aggregation contract unchanged (one directory, one glob pattern). The
full visual-review.json in `test-evidence/` is the detailed source of truth
for debugging and audit.
