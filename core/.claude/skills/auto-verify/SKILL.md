---
name: auto-verify
description: >
  Unified verification pipeline: identifies changed files, maps to targeted tests,
  runs tests with smart priority, analyzes failures, applies fixes with approval,
  then runs quality gate, contract verification, and performance baseline checks.
  Use after making code changes to verify correctness.
allowed-tools: "Bash Read Grep Glob Write Edit Skill"
argument-hint: "[--files <paths>] [--full-suite]"
version: "1.2.0"
type: workflow
---

# Auto-Verify — Post-Change Verification

Automatically verify code changes by running targeted tests and analyzing results.

**Arguments:** $ARGUMENTS

---

## STEP 0: Gate Check — Read Upstream Results

Before running verification, check if the upstream `fix-loop` stage passed:

1. If `test-results/fix-loop.json` exists, read it
2. Parse the `result` field
3. If `result` is `FAILED` or `FLAKY`:
   - Report: "BLOCKED: fix-loop reported {result} — resolve upstream failures before running auto-verify."
   - Exit immediately — do not proceed to change identification
4. If `result` is `PASSED`, `FIXED`, or the file does not exist → proceed to STEP 1

```bash
if [ -f test-results/fix-loop.json ]; then
  UPSTREAM_RESULT=$(python3 -c "import json; print(json.load(open('test-results/fix-loop.json'))['result'])")
  if [ "$UPSTREAM_RESULT" = "FAILED" ] || [ "$UPSTREAM_RESULT" = "FLAKY" ]; then
    echo "BLOCKED: fix-loop reported $UPSTREAM_RESULT"
    exit 1
  fi
  echo "fix-loop result: $UPSTREAM_RESULT — proceeding"
else
  echo "No fix-loop results found — proceeding without gate check"
fi
```

---

## STEP 1: Identify Changes

```bash
git diff --name-only HEAD
git diff --name-only --cached
```

If `--files` provided, use those instead.

## STEP 2: Map Changes to Tests

For each changed file, find related test files using these strategies in order:

### 2.1 Path-Based Mapping (try first)

| Source Pattern | Test Pattern(s) to Check |
|---------------|-------------------------|
| `src/<path>/<name>.py` | `tests/<path>/test_<name>.py`, `tests/test_<name>.py` |
| `src/<path>/<name>.ts` | `tests/<path>/<name>.test.ts`, `src/<path>/<name>.test.ts`, `__tests__/<path>/<name>.test.ts` |
| `app/<path>/<name>.py` | `tests/<path>/test_<name>.py` |
| `src/<path>/<name>.kt` | `src/test/<path>/<name>Test.kt` |

### 2.2 Import-Based Mapping (fallback if path-based finds nothing)

```bash
# Find test files that import the changed module
grep -rl "from.*<module_name>" tests/ --include="*.py" --include="*.ts"
grep -rl "import.*<module_name>" tests/ --include="*.py" --include="*.ts"
```

### 2.3 Convention Detection

Check the project for test layout conventions:
- Look at existing test files to detect naming patterns
- Check `CLAUDE.md`, `pyproject.toml`, or `jest.config.*` for test path config
- If the project uses a non-standard layout, adapt mapping rules accordingly

If no test files are found for a changed file, flag it: "No tests found for `<file>` — consider adding tests."

## STEP 3: Run Targeted Tests

### 3.0 Risk Classification and Auto-Escalation

Before running tests, classify each changed file by risk level:

| Risk Level | Module Patterns | Action |
|------------|----------------|--------|
| CRITICAL | `auth/*`, `payment/*`, `crypto/*`, `security/*`, `token/*`, `oauth/*`, `billing/*` | Auto-escalate to full suite |
| HIGH | `models/*`, `migrations/*`, `database/*`, `db/*`, `schema/*`, `entities/*` | Auto-escalate to full suite |
| MEDIUM | `routes/*`, `controllers/*`, `handlers/*`, `api/*`, `endpoints/*`, `views/*` | Run targeted tests + related integration tests |
| LOW | `utils/*`, `helpers/*`, `configs/*`, `constants/*`, `types/*`, `interfaces/*` | Run targeted tests only |

If ANY changed file is classified as HIGH or CRITICAL, auto-escalate to full test suite regardless of whether `--full-suite` was specified. Log the escalation reason:

```
Risk escalation: <file> classified as <CRITICAL|HIGH> — running full test suite
```

### 3.1 Execute Tests

Run only the tests related to changed files first (unless escalated to full suite):

1. Execute mapped test files (or full suite if risk >= HIGH)
2. If all pass and `--full-suite` not specified and risk < HIGH → report success
3. If any fail → analyze and attempt fix

## STEP 4: Analyze Failures

For each failure:
1. Read the test and source code
2. Determine if the failure is from our change or pre-existing using git-stash verification
3. If from our change → suggest fix
4. If pre-existing → note it but don't block

### 4.1 Git-Stash Verification for Pre-Existing Failures

For every failing test, verify whether the failure is pre-existing or caused by our changes using a stash-based comparison:

```bash
# 1. Stash our changes to restore clean state
git stash

# 2. Run the specific failing test against clean state
<test_runner> <failing_test_file>::<failing_test_name>

# 3. Restore our changes
git stash pop
```

**Decision logic:**

| Test on clean state | Test with our changes | Verdict | Action |
|--------------------|-----------------------|---------|--------|
| FAILS | FAILS | Pre-existing failure | Note it, do not block |
| PASSES | FAILS | Our change caused it | BLOCK — must fix before proceeding |
| PASSES | PASSES | Not a real failure | Likely flaky — log and re-run |
| FAILS | PASSES | Our change fixed it | Note as incidental fix |

If `git stash` fails (e.g., no changes to stash, merge conflicts), fall back to heuristic analysis: check `git log` for recent changes to the failing test's source files and classify based on recency.

### Content Verification Note

When verifying UI tests, distinguish between:
- **Test passes because UI rendered correctly** — layout, styles, elements all present
- **Test passes because UI rendered correctly BUT with no data** — empty tables, blank charts, stale content

If changed files include API endpoints, data fetching, or state management:
1. Verify that UI tests assert data presence (not just element presence)
2. Flag tests that only check `toBeVisible()` without checking content
3. Recommend adding data count assertions for tables, lists, and charts

## STEP 5: Apply Fixes (with approval)

For each identified fix:
1. Describe the fix to the user
2. Apply only if approved or if running autonomously
3. Re-run affected tests after fix

## STEP 6: Regression Check

If fixes were applied, run broader test suite to check for regressions.

## STEP 6A: Quality Gate (if tests pass)

After all tests pass, run quality checks on changed code:

1. **Coverage diff** — verify new/changed code has ≥80% test coverage
2. **Complexity check** — no new function exceeds cyclomatic complexity 10
3. **Duplication scan** — no new code blocks duplicate existing code
4. If any quality check fails → report as QUALITY_GATE warning (non-blocking unless `--strict-quality`)

Reference: delegates to `/code-quality-gate` skill for detailed analysis.

## STEP 6B: Contract Verification (if API changed)

If changed files include API routes, endpoints, schemas, or Pydantic models:

1. Run contract tests to verify consumer-provider compatibility
2. Check if API response shapes match existing contracts
3. If contract test fails → report as CONTRACT_BREAK (blocking)

Reference: delegates to `/contract-test` skill if Pact is configured.

## STEP 6C: Performance Baseline (if perf-sensitive code changed)

If changed files match perf-sensitive paths (request handlers, database queries, serialization):

1. Run targeted performance benchmarks if baseline exists
2. Compare against baseline — flag >10% regression
3. If regression detected → report as PERF_REGRESSION warning

Reference: delegates to `/perf-test` skill if k6/Lighthouse is configured.

## STEP 7: Report

```
Auto-Verify: [PASSED / FIXED / FAILED]
  Changed files: N
  Tests run: M
  Passed: P | Failed: F
  Fixes applied: X
  Regressions: Y
  Quality gate: PASSED/WARNED/SKIPPED
  Contract check: PASSED/FAILED/SKIPPED
  Perf baseline: PASSED/REGRESSED/SKIPPED
```

## STEP 8: Structured Output

Write machine-readable results to `test-results/auto-verify.json`:

```json
{
  "skill": "auto-verify",
  "timestamp": "<ISO-8601>",
  "result": "PASSED|FIXED|FAILED",
  "summary": {
    "total": "<tests_run>",
    "passed": "<passed_count>",
    "failed": "<failed_count>",
    "skipped": "<skipped_count>",
    "flaky": "<flaky_count>"
  },
  "quality_gate": "PASSED|WARNED|FAILED|SKIPPED",
  "contract_check": "PASSED|FAILED|SKIPPED",
  "perf_baseline": "PASSED|REGRESSED|SKIPPED",
  "failures": [],
  "warnings": [],
  "duration_ms": "<elapsed>"
}
```

Create `test-results/` directory if it doesn't exist. This JSON is consumed by stage gates — see `testing.md` for the full schema.
