---
name: auto-verify
description: >
  Run a post-change verification pipeline that maps changed files to targeted tests,
  executes via tester-agent with UI screenshot verdicts, enforces quality gates, and
  produces structured results for pipeline consumption. Does NOT fix — use /fix-loop
  for fixes, /test-pipeline for the full fix-verify-commit chain.
triggers:
  - auto-verify
  - verify my changes
  - post-change verification
  - run verification
  - verify before commit
  - verify correctness
allowed-tools: "Bash Read Grep Glob Write Skill Agent"
argument-hint: "[--files <paths>] [--full-suite] [--strict-gates] [--capture-proof | --no-capture-proof]"
version: "3.2.0"
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
| `--files` | git diff | Specific files to verify (overridden by `--full-suite`) |
| `--full-suite` | false | Run full test suite regardless of risk (overrides `--files`) |
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
  UPSTREAM_RESULT=$(python3 -c "
import json, sys
try:
    data = json.load(open('test-results/fix-loop.json'))
    print(data.get('result', 'UNKNOWN'))
except (json.JSONDecodeError, IOError) as e:
    print(f'WARN: Could not parse fix-loop.json: {e}', file=sys.stderr)
    print('UNKNOWN')
")
  if [ "$UPSTREAM_RESULT" = "FAILED" ] || [ "$UPSTREAM_RESULT" = "FLAKY" ]; then
    echo "BLOCKED: fix-loop reported $UPSTREAM_RESULT"
    exit 1
  fi
  if [ "$UPSTREAM_RESULT" = "UNKNOWN" ]; then
    echo "WARN: fix-loop.json unreadable — treating as missing"
    # Fall through to the missing-file logic below
  else
    echo "fix-loop result: $UPSTREAM_RESULT — proceeding"
  fi
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

**Fallback if `/regression-test` is not installed:** Use `git diff --name-only` to
identify changed files, then map to tests by naming convention (`*_test.py`,
`test_*.py`, `*.test.ts`, `*.spec.ts`) and directory adjacency. Set risk to
MEDIUM (no import graph tracing available). Log: "WARN: /regression-test not
available — using fallback file-based test mapping."

After `/regression-test` completes, read `test-results/regression-test.json`:

1. Extract the affected test list and overall risk level
2. If `regression-test` result is `FAILED` with `confidence: BLOCKED`
   (test infra broken — cannot map tests) → exit with BLOCKED
3. If `regression-test` result is `FAILED` with `confidence: LOW`
   (some tests failed during mapping) → note failures but proceed to STEP 2
   (tester-agent will re-run them with full verdict rules)
4. Use the mapped test files and risk classification for STEP 2
5. If zero affected tests found → skip Steps 2-3, write auto-verify.json with
   `result: "PASSED"`, `summary.total: 0`, and `warnings: ["No tests mapped to
   changed files"]`. Proceed to Step 4 (quality gates still run).

Coverage gaps flagged by `/regression-test` (source files with no mapped tests)
are reported in the final auto-verify output as warnings.

## STEP 2: Execute Tests (via tester-agent)

**Fallback if `tester-agent` is not installed:** Run tests directly using the
project's test runner (detect from CLAUDE.md, pyproject.toml, package.json, or
build.gradle). All tests use exit-code verdicts (no screenshot verification).
Log: "WARN: tester-agent not available — running tests directly without UI
screenshot verification."

**Terminal failure if no test runner detected:** If none of CLAUDE.md test
commands, pyproject.toml, package.json, or build.gradle exist, write
`test-results/auto-verify.json` with `result: "FAILED"`,
`failures: [{"test": "N/A", "category": "INFRA_MISSING", "message": "No test
framework detected — cannot execute tests"}]` and exit.

Delegate test execution to `tester-agent`, which provides:
- **UI test detection** — auto-classifies tests by scanning imports for UI frameworks
- **Per-test screenshot verification (UI tests)** — runs each UI test individually,
  captures screenshot, verifies via AI/baseline, records screenshot-based verdict
- **Batch execution (non-UI tests)** — standard batch run with exit-code verdicts
- Smart test ordering (CRITICAL risk first, then HIGH, MEDIUM, LOW)
- Verdict rules: UI tests use screenshot verdict; non-UI use exit codes
- Isolated re-run of failures to detect test pollution
- Structured output with pass/fail/skip/flaky breakdown and verdict_source per test

```
Agent("tester-agent", prompt="Run these tests and provide a verdict.

Test files (from /regression-test mapping):
$AFFECTED_TESTS

Risk classification:
$OVERALL_RISK

Options:
- Full suite: $FULL_SUITE
- Run ID: $RUN_ID

IMPORTANT — UI Test Screenshot Verification:
1. Classify each test file as UI or non-UI by scanning imports
   (see your UI Test Detection rules). If visual-tests.yml exists
   in the project root, use its patterns instead of import scanning.
2. For UI tests: execute the Per-Test Screenshot Orchestration loop —
   run one test at a time, capture screenshot, verify screenshot
   (baseline first, then text hint, then generic AI review),
   record verdict with verdict_source: 'screenshot'.
   Screenshot verification is MANDATORY and ALWAYS ON for UI tests.
3. For non-UI tests: run batch execution with exit-code verdicts,
   verdict_source: 'exit_code'.

Screenshot storage: test-evidence/{run_id}/screenshots/
  {test_name}.{pass|fail}.png

Use the project's test runner (detect from CLAUDE.md, pyproject.toml,
package.json, or build.gradle). Run targeted tests first unless
risk >= HIGH or --full-suite specified.

Return: verdict (PASSED/FAILED), test counts, failure details,
ui_test_count, screenshot manifest, per-test verdict_source.")
```

After `tester-agent` returns, the agent provides TWO verdict dimensions:

| Verdict | Source | Authoritative For |
|---------|--------|-------------------|
| `ui_verdict` | Screenshot verification | UI tests |
| `code_verdict` | Exit codes | Non-UI tests |

1. If EITHER verdict is **FAILED** → proceed to STEP 3 (evaluate results, report)
2. If BOTH verdicts are **PASSED** → proceed to STEP 2.5 (confirmation review) then STEP 4
3. Record the agent's screenshot manifest in `test-evidence/{run_id}/manifest.json`

---

## STEP 2.5: Visual Proof Review

**For UI tests:** This step is MANDATORY and ALWAYS runs. It serves as a
confirmation pass — the tester-agent already verified each screenshot inline,
and this step batch-reviews the verdicts for consistency and catches edge cases.
`--capture-proof` / `--no-capture-proof` flags do NOT affect UI test screenshots.

**For non-UI tests:** Skip this step if `--capture-proof` is not enabled or
`--no-capture-proof` was passed. When enabled for non-UI tests, it provides
supplementary visual evidence (not authoritative).

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

**UI tests (verdict_source: "screenshot")** — tester-agent already set the
verdict from screenshot. This pass confirms or catches edge cases:

| Tester Verdict | Confirmation Review | Action |
|----------------|-------------------|--------|
| PASSED | Confirms correct | No action — verdict stands |
| PASSED | Spots missed issue | OVERRIDE → FAILED (add to overrides) |
| FAILED | Confirms failure | No action — verdict stands |
| FAILED | Looks actually correct | FLAG for review (possible AI triage error) |

**Non-UI tests (verdict_source: "exit_code")** — screenshot is supplementary:

| Exit Code | Visual Assessment | Verdict | Action |
|-----------|-------------------|---------|--------|
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

After test execution and visual review:

### Verdict Logic by Test Type

| Test Type | Primary Verdict Source | Secondary Signal |
|-----------|----------------------|------------------|
| UI test | Screenshot verification (from tester-agent) | Exit code (logged, not authoritative) |
| Non-UI test | Exit code | Screenshot (if captured, supplementary only) |

### Verdict Combinations for UI Tests

| Exit Code | Screenshot Verdict | Final Result | Rationale |
|-----------|-------------------|--------------|-----------|
| PASSED | PASSED | **PASSED** | Both agree — confident pass |
| PASSED | FAILED | **FAILED** | Screenshot is authoritative — visual defect detected |
| FAILED | PASSED | **FAILED** + FLAG | Still failed (exit code indicates code issue), but flag for review — possible assertion bug or timing issue |
| FAILED | FAILED | **FAILED** | Both agree — confirmed failure |

### Decision Flow

1. **All tests pass** (UI screenshot verdicts + non-UI exit codes, and no visual overrides) → proceed to STEP 4 (quality gates)
2. **Any test fails:**
   - Classify each failure using the test output AND verdict_source (category, file, message)
   - Check for pre-existing failures using git-stash verification (see below)
   - Report FAILED with detailed failure list including verdict_source per test
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
    "flaky": "<flaky_count>",
    "ui_tests": "<ui_test_count>",
    "ui_tests_screenshot_verified": "<count verified via screenshot>",
    "non_ui_tests": "<non_ui_test_count>"
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
  "failures": [
    {
      "test": "test_name",
      "verdict_source": "screenshot|exit_code",
      "category": "VISUAL_DEFECT|ASSERTION_FAILURE|...",
      "file": "tests/test_file.py:42",
      "message": "description",
      "confidence": "HIGH|MEDIUM|LOW"
    }
  ],
  "warnings": [],
  "duration_ms": "<elapsed>"
}
```

**For UI tests:** `visual_review` is ALWAYS populated (mandatory). The `failures`
array includes `verdict_source: "screenshot"` for each UI test failure.

**For non-UI tests:** If `--capture-proof` was not enabled:
```json
"visual_review": {
  "enabled": false
}
```

Create `test-results/` directory if it doesn't exist. This JSON is consumed by stage gates — see `testing.md` for the full schema.

**Standalone cleanup:** When running outside the pipeline (no Pipeline ID),
delete stale `test-results/auto-verify.json` before starting to prevent the
stage gate aggregator from reading results from a previous run.

---

## CRITICAL RULES

- MUST NOT apply fixes — fixing belongs in `/fix-loop`. — Why: mixing verification and fixing in one skill creates circular dependencies and unclear verdicts.
- MUST produce `test-results/auto-verify.json` on every run, even when BLOCKED or zero tests found. — Why: downstream stage gates read this file; missing file = pipeline hang.
- MUST use `result` as the canonical gate field name — never `status`, `verdict`, or `outcome`. — Why: all pipeline skills parse `result` by convention; renaming breaks the aggregator.
- MUST distinguish UI test verdicts (screenshot-authoritative) from non-UI (exit-code-authoritative). — Why: UI tests can pass exit code but fail visually (empty table, broken layout).
- MUST NOT proceed past Step 0 if upstream fix-loop reported FAILED or FLAKY. — Why: verifying known-broken code wastes compute and produces misleading results.
- MUST report pre-existing failures separately from regression failures in the output. — Why: blocking on pre-existing failures prevents any new work from passing verification.
- MUST degrade gracefully if `/regression-test` or `tester-agent` are missing — use fallbacks, not hard failures. — Why: not all projects have these installed; hard failure makes the skill unusable in simpler setups.
