---
name: auto-verify
description: >
  Run a verification pipeline that identifies changed files, maps to targeted tests,
  executes tests with smart priority, analyzes failures, and applies fixes with approval.
  Use after making code changes to verify correctness before committing.
allowed-tools: "Bash Read Grep Glob Write Edit Skill Agent"
argument-hint: "[--files <paths>] [--full-suite] [--strict-gates] [--capture-proof | --no-capture-proof]"
version: "2.0.0"
type: workflow
---

# Auto-Verify — Post-Change Verification

Verify code changes by running targeted tests, reviewing visual proof, and
enforcing quality gates. Does NOT apply fixes — fixing belongs in `/fix-loop`.

**Arguments:** $ARGUMENTS

---

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--files` | git diff | Specific files to verify |
| `--full-suite` | false | Run full test suite regardless of risk |
| `--strict-gates` | false | Missing upstream JSON = BLOCK (set by orchestrator) |
| `--capture-proof` | true (from config) | Capture screenshots on every test, pass or fail |
| `--no-capture-proof` | — | Disable screenshot capture even if config says true |

---

## STEP 0: Gate Check — Read Upstream Results

Check if the upstream `fix-loop` stage passed:

1. If `test-results/fix-loop.json` exists, read it:
   - If `result` is `FAILED` or `FLAKY` → BLOCK. Exit immediately.
   - If `result` is `PASSED` or `FIXED` → proceed to STEP 1.

2. If `test-results/fix-loop.json` does NOT exist:
   - **With `--strict-gates`:** BLOCK. Report: "BLOCKED: fix-loop output missing — run fix-loop first or use orchestrator."
   - **Without `--strict-gates`:** WARN: "No fix-loop results found — proceeding without gate check. Run via test-pipeline-agent for enforced gates."
   - Proceed to STEP 1.

```bash
if [ -f test-results/fix-loop.json ]; then
  UPSTREAM_RESULT=$(python3 -c "import json; print(json.load(open('test-results/fix-loop.json'))['result'])")
  if [ "$UPSTREAM_RESULT" = "FAILED" ] || [ "$UPSTREAM_RESULT" = "FLAKY" ]; then
    echo "BLOCKED: fix-loop reported $UPSTREAM_RESULT"
    exit 1
  fi
  echo "fix-loop result: $UPSTREAM_RESULT — proceeding"
else
  if [ "$STRICT_GATES" = "true" ]; then
    echo "BLOCKED: fix-loop output missing (--strict-gates enforced)"
    exit 1
  else
    echo "WARN: No fix-loop results found — proceeding without gate check"
  fi
fi
```

---

## STEP 1: Map Changes to Tests (via /regression-test)

Delegate change identification and test mapping to `/regression-test`, which
provides 2-level import graph tracing, coverage-based mapping, and risk
classification. This is the single canonical mapper for the pipeline.

**IMPORTANT:** `/regression-test` is invoked for MAPPING ONLY — it identifies
which tests to run and classifies risk, but does NOT execute the tests itself.
Test execution happens in STEP 2 via `tester-agent`. This avoids double
execution where tests run once for mapping and again for verification.

```
Skill("/regression-test", args="$FILES_ARG --framework auto")
```

After `/regression-test` completes, read `test-results/regression-test.json`:

1. Extract the affected test list and overall risk level
2. If `regression-test` result is `FAILED` with `confidence: BLOCKED`
   (test infra broken — cannot map tests) → exit with BLOCKED
3. If `regression-test` result is `FAILED` with `confidence: LOW`
   (some tests failed during mapping) → note failures but proceed to STEP 2
   (tester-agent will re-run them with full verdict rules)
4. Use the mapped test files and risk classification for STEP 2

Coverage gaps flagged by `/regression-test` (source files with no mapped tests)
are reported in the final auto-verify output as warnings.

## STEP 2: Execute Tests (via tester-agent)

Delegate test execution to `tester-agent`, which provides:
- Smart test ordering (CRITICAL risk first, then HIGH, MEDIUM, LOW)
- Verdict rules: FAILED if ANY test fails, FAILED if skip rate >10%,
  FAILED on ResourceWarning or unclosed connections
- Isolated re-run of failures to detect test pollution
- Structured output with pass/fail/skip/flaky breakdown

```
Agent("tester-agent", prompt="Run these tests and provide a verdict.

Test files (from /regression-test mapping):
$AFFECTED_TESTS

Risk classification:
$OVERALL_RISK

Options:
- Full suite: $FULL_SUITE
- Capture proof: $CAPTURE_PROOF

If --capture-proof is enabled, configure the test runner to capture a
screenshot after every test (pass and fail). Store screenshots in
test-evidence/{run_id}/screenshots/ with naming:
  {test_name}.{pass|fail}.png

Use the project's test runner (detect from CLAUDE.md, pyproject.toml,
package.json, or build.gradle). Run targeted tests first unless
risk >= HIGH or --full-suite specified.

Return: verdict (PASSED/FAILED), test counts, failure details,
screenshot manifest (if capture-proof enabled).")
```

After `tester-agent` returns:

1. If verdict is **FAILED** → proceed to STEP 3 (evaluate results, report)
2. If verdict is **PASSED** → proceed to STEP 2.5 (visual review) or STEP 4 (quality gates)
3. Record the agent's screenshot manifest in `test-evidence/{run_id}/manifest.json`

---

## STEP 2.5: Visual Proof Review (if --capture-proof enabled)

Skip this step entirely if `--capture-proof` is not enabled or `--no-capture-proof`
was passed.

### 2.5.1 Read Manifest

```bash
MANIFEST="test-evidence/${RUN_ID}/manifest.json"
if [ ! -f "$MANIFEST" ]; then
  echo "No screenshot manifest found — skipping visual review"
  # Set visual_review.enabled = false in structured output, proceed to STEP 3
fi
```

If the manifest exists but has zero screenshots (`screenshot_count: 0` or
empty `screenshots` array), this is normal for non-UI projects (API servers,
CLI tools, libraries). Handle gracefully:

```bash
SCREENSHOT_COUNT=$(python3 -c "import json; print(json.load(open('$MANIFEST')).get('screenshot_count', 0))")
if [ "$SCREENSHOT_COUNT" = "0" ]; then
  echo "Manifest found but 0 screenshots (non-UI project) — skipping visual review"
  # Write visual-review.json with result: PASSED, screenshots_reviewed: 0
  # Proceed to STEP 3
fi
```

Parse the manifest to get the list of all screenshots with their test names,
results, and file paths.

### 2.5.2 Review All Screenshots

For EVERY screenshot in the manifest (100% review rate):

1. **Read the screenshot** using multimodal Read (the image file)
2. **Evaluate** against these criteria (from `/verify-screenshots` Step 2):
   - No error dialogs, crash screens, or unhandled exception modals
   - Text is readable and not truncated
   - Layout appears correct (no overlapping elements)
   - Loading states are resolved (no spinners in final screenshots)
   - Data containers are populated (tables have rows, lists have items)
   - No empty-state placeholders when data is expected
   - No placeholder text ("Lorem ipsum", "undefined", "null", "NaN")
   - Timestamps/dates are within expected recency

3. **Classify** each screenshot:

| Test Result | Visual Assessment | Verdict | Action |
|-------------|-------------------|---------|--------|
| PASSED | Looks correct | CONFIRMED | No action |
| PASSED | Shows problems | OVERRIDE → FAILED | Add to overrides list |
| FAILED | Shows the failure | CONFIRMED | Enrich failure diagnosis |
| FAILED | Looks correct | FLAG for review | Possible flaky/timing issue |

### 2.5.3 Write Visual Review Results

Write `test-evidence/{run_id}/visual-review.json`:

```json
{
  "skill": "visual-proof-review",
  "run_id": "{run_id}",
  "timestamp": "{ISO-8601}",
  "screenshots_reviewed": 50,
  "screenshots_total": 50,
  "confirmed_passes": 43,
  "confirmed_failures": 5,
  "overrides": [
    {
      "test": "test_dashboard_loads",
      "original_result": "PASSED",
      "visual_verdict": "FAILED",
      "reason": "Dashboard shows empty table — no data rows visible despite test asserting element presence",
      "screenshot": "screenshots/test_dashboard_loads.pass.png"
    }
  ],
  "flags": [
    {
      "test": "test_login_timeout",
      "original_result": "FAILED",
      "visual_observation": "Screenshot shows successful login page — possible timing/flaky issue",
      "screenshot": "screenshots/test_login_timeout.fail.png"
    }
  ],
  "result": "PASSED|FAILED"
}
```

`result` is FAILED if ANY overrides exist (a passed test was visually broken).
`result` is PASSED if zero overrides (all passes confirmed, all failures confirmed).

### 2.5.4 Gate Impact

If visual review `result` is FAILED:
- Report each override with the reason and screenshot path
- The override failures are added to the main failure list in STEP 3
- These count as real failures for the auto-verify verdict

If visual review `result` is PASSED:
- Log: "Visual proof review: {N} screenshots confirmed, 0 overrides"
- Proceed normally

---

## STEP 3: Evaluate Results

After test execution (and visual review if enabled):

1. **All tests pass** (and no visual overrides) → proceed to STEP 4 (quality gates)
2. **Any test fails:**
   - Classify each failure using the test output (category, file, message)
   - Check for pre-existing failures using git-stash verification (see below)
   - Report FAILED with detailed failure list
   - Do NOT attempt fixes — fixing belongs in `/fix-loop` upstream

### Pre-Existing Failure Detection

For each failing test, verify whether it's caused by our changes:

```bash
git stash && <test_runner> <failing_test> && git stash pop
```

| Clean state | Our changes | Verdict | Action |
|-------------|-------------|---------|--------|
| FAILS | FAILS | Pre-existing | Note it, do not block |
| PASSES | FAILS | Our change caused it | BLOCK — report in failures |
| PASSES | PASSES | Flaky | Log, re-run to confirm |
| FAILS | PASSES | Incidental fix | Note as bonus |

---

## STEP 4: Quality Gate (if tests pass)

After all tests pass, run quality checks on changed code:

1. **Coverage diff** — verify new/changed code has ≥80% test coverage
2. **Complexity check** — no new function exceeds cyclomatic complexity 10
3. **Duplication scan** — no new code blocks duplicate existing code
4. If any quality check fails → report as QUALITY_GATE warning (non-blocking unless `--strict-quality`)

Reference: delegates to `/code-quality-gate` skill for detailed analysis.

## STEP 4A: Contract Verification (if API changed)

If changed files include API routes, endpoints, schemas, or Pydantic models:

1. Run contract tests to verify consumer-provider compatibility
2. Check if API response shapes match existing contracts
3. If contract test fails → report as CONTRACT_BREAK (blocking)

Reference: delegates to `/contract-test` skill if Pact is configured.

## STEP 4B: Performance Baseline (if perf-sensitive code changed)

If changed files match perf-sensitive paths (request handlers, database queries, serialization):

1. Run targeted performance benchmarks if baseline exists
2. Compare against baseline — flag >10% regression
3. If regression detected → report as PERF_REGRESSION warning

Reference: delegates to `/perf-test` skill if k6/Lighthouse is configured.

---

## STEP 5: Report

```
Auto-Verify: [PASSED / FAILED]
  Changed files: N
  Tests run: M
  Passed: P | Failed: F
  Visual review: N screenshots, K overrides
  Quality gate: PASSED/WARNED/SKIPPED
  Contract check: PASSED/FAILED/SKIPPED
  Perf baseline: PASSED/REGRESSED/SKIPPED
```

## STEP 6: Structured Output

Write machine-readable results to `test-results/auto-verify.json`:

```json
{
  "skill": "auto-verify",
  "timestamp": "<ISO-8601>",
  "result": "PASSED|FAILED",
  "summary": {
    "total": "<tests_run>",
    "passed": "<passed_count>",
    "failed": "<failed_count>",
    "skipped": "<skipped_count>",
    "flaky": "<flaky_count>"
  },
  "change_scope": {
    "source_files": "<count from regression-test>",
    "test_files": "<count>",
    "overall_risk": "<CRITICAL|HIGH|MEDIUM|LOW>",
    "coverage_gaps": ["<files with no mapped tests>"]
  },
  "quality_gate": "PASSED|WARNED|FAILED|SKIPPED",
  "contract_check": "PASSED|FAILED|SKIPPED",
  "perf_baseline": "PASSED|REGRESSED|SKIPPED",
  "visual_review": {
    "enabled": true,
    "screenshots_reviewed": 50,
    "overrides": 1,
    "flags": 1,
    "result": "PASSED|FAILED",
    "evidence_dir": "test-evidence/{run_id}/"
  },
  "failures": [],
  "warnings": [],
  "duration_ms": "<elapsed>"
}
```

If `--capture-proof` was not enabled, the `visual_review` field is:
```json
"visual_review": {
  "enabled": false
}
```

Create `test-results/` directory if it doesn't exist. This JSON is consumed by stage gates — see `testing.md` for the full schema.
