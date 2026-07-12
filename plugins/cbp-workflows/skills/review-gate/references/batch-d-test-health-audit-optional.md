# Batch D: Test Health Audit (Optional)

### D.1 Run Test Maintenance Audit

```
Skill("test-maintenance", args="--step audit-only")
```

### D.2 Record Results

Extract the following metrics from the test-maintenance audit output and include them in the consolidated report's Recommendations section as warnings:

```
BATCH D — Test Health (non-blocking):
  Skip rate: {percentage of tests marked skip/ignore/disabled}
  Dead tests: {count of tests that never run in CI}
  Slow tests: {count of tests exceeding category timeout thresholds}
  Status: WARN (advisory only — does not affect verdict)
```

### D.3 Thresholds for Warnings

| Metric | Healthy | Warning Threshold |
|--------|---------|-------------------|
| Skip rate | < 5% | >= 5% of total test suite |
| Dead tests | 0 | >= 1 test never executed in CI |
| Slow tests | 0 | >= 3 tests exceeding their category timeout |

If any threshold is exceeded, add a warning entry to the consolidated report's `warnings` array in `test-results/review-gate.json`:

```json
{
  "source": "test-maintenance",
  "level": "WARN",
  "metrics": {
    "skip_rate_pct": 8.2,
    "dead_test_count": 3,
    "slow_test_count": 5
  },
  "message": "Test suite health degraded — 8.2% skip rate, 3 dead tests, 5 slow tests. Run /test-maintenance for remediation."
}
```

---

