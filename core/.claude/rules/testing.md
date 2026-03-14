---
description: Testing conventions and best practices.
---

# Testing Rules

## General Principles

1. **Test Isolation** — Each test should be independent; no shared mutable state
2. **Descriptive Names** — Test names should describe the scenario and expected outcome
3. **Arrange-Act-Assert** — Structure tests clearly with setup, action, and verification
4. **One Assertion Focus** — Each test should verify one behavior (multiple asserts OK if related)
5. **No Test Interdependence** — Tests must pass in any order

## Test Categories

| Category | Purpose | Speed |
|----------|---------|-------|
| Unit | Individual functions/methods | Fast (ms) |
| Integration | Component interactions | Medium (seconds) |
| E2E | Full user flows | Slow (minutes) |

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

| Field | Values | Meaning |
|-------|--------|---------|
| `result` | `PASSED`, `FAILED`, `FIXED`, `FLAKY` | Overall verification outcome |
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

Downstream stages read `test-results/*.json` to determine if verification passed:

```bash
# Check if all verification passed
python -c "
import json, glob, sys
results = [json.load(open(f)) for f in glob.glob('test-results/*.json')]
failed = [r for r in results if r['result'] == 'FAILED']
if failed:
    for r in failed:
        print(f\"BLOCKED: {r['skill']} — {r['result']}\")
    sys.exit(1)
print('All verification gates passed')
"
```

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
