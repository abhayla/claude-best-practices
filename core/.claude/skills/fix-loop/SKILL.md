---
name: fix-loop
description: >
  Iterative fix cycle: analyze failures, apply minimal fixes, optionally retest.
  Full Loop mode (with retest command) iterates until resolved. Single Fix mode
  (no retest) does one pass. Use when tests fail, build breaks, or runtime errors.
allowed-tools: "Bash Read Grep Glob Write Edit Skill"
argument-hint: "[failure_output] [retest_command: <cmd>] [max_iterations: N]"
version: "1.1.0"
type: workflow
---

# Fix Loop — Iterative Fix Cycle

Analyze failures, apply minimal fixes, and optionally retest until resolved.

**Input:** $ARGUMENTS

---

## Mode Detection

| Input | Mode | Behavior |
|-------|------|----------|
| `retest_command` provided | **Full Loop** | Fix → retest → repeat until pass (max iterations) |
| No `retest_command` | **Single Fix** | Analyze → apply one fix → report |

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `failure_output` | — | The error output to analyze |
| `retest_command` | — | Command to re-run tests after fix |
| `max_iterations` | 5 | Maximum fix-test cycles. Callers (e.g., `/executing-plans`) may pass a lower value to keep total retry budgets bounded. |
| `files_of_interest` | — | Specific files to focus on |

---

## STEP 1: Analyze Failure

1. Parse the error output and classify into one of these categories:
   - `COMPILE_ERROR` — Code doesn't compile/parse
   - `ASSERTION_FAILURE` — Expected vs actual mismatch
   - `TIMEOUT` — Test exceeds time limit
   - `FIXTURE_MISMATCH` — Test setup/teardown issues
   - `MISSING_IMPORT` — Import or dependency not found
   - `RUNTIME_EXCEPTION` — Unexpected exception during execution
   - `FLAKY_TEST` — Intermittent failure (passes on retry)
   - `INFRASTRUCTURE` — Environment, network, or service issues
   - `CONTRACT_MISMATCH` — API response doesn't match consumer contract
   - `MIGRATION_FAILURE` — Database schema/migration error
   - `AUTH_ERROR` — Authentication or authorization failure
   - `VISUAL_REGRESSION` — Screenshot differs from baseline
   - `SCHEMA_VALIDATION` — Response/request doesn't match schema

2. Extract details from the error output:
   - Failing file and line number
   - Expected vs actual values
   - Stack trace information

3. Read the failing source code and test code

4. Identify root cause with confidence level (High/Medium/Low)

## STEP 1A: Flaky Test Detection

Before applying a fix, check if the failure is flaky:

1. Re-run ONLY the failing test(s) once
2. If the test passes on retry → classify as `FLAKY_TEST`
3. For flaky tests:
   - Do NOT apply a code fix
   - Tag with `@pytest.mark.flaky` / `@RepeatedTest` / `test.retry()`
   - Log a tracking issue
   - Report as FAILED with `flaky_detected: true` in the structured output — flaky is a failure category, not an acceptable outcome
4. Continue to STEP 2 only for non-flaky failures

## STEP 2: Apply Fix

1. Make the minimal change to address the root cause
2. Do NOT refactor unrelated code
3. Do NOT change test expectations unless the test is wrong
4. Prefer fixing source code over fixing tests

## STEP 3: Retest (Full Loop mode only)

Run the retest command and check results:
- If all pass → report success
- If different failure → analyze new failure (new iteration)
- If same failure → escalate analysis depth
- If max iterations reached → report remaining failures and suggest manual review

## STEP 4: Report

**On success:**
```
Fix Loop: RESOLVED in {N} iterations
  Category: [FAILURE_CATEGORY]
  Root cause: [description]
  Fix applied: [file:line — what changed]
  Flaky tests detected: M (quarantined)
  Tests: all passing
```

**On failure (max iterations):**
```
Fix Loop: UNRESOLVED after {N} iterations
  Category: [FAILURE_CATEGORY]
  Remaining failures: [list]
  Attempted fixes: [list]
  Flaky tests detected: M (quarantined)
  Suggestion: [manual review guidance]
```

## STEP 5: Structured Output

Write machine-readable results to `test-results/fix-loop.json`:

```json
{
  "skill": "fix-loop",
  "timestamp": "<ISO-8601>",
  "result": "PASSED|FAILED",
  "flaky_detected": true,
  "summary": {
    "iterations": "<N>",
    "max_iterations": "<max>",
    "category": "<FAILURE_CATEGORY>",
    "root_cause": "<description>",
    "flaky_tests_quarantined": "<count>"
  },
  "failures": [],
  "warnings": [],
  "duration_ms": "<elapsed>"
}
```

Create `test-results/` directory if it doesn't exist. This JSON is consumed by stage gates.

---

## ESCALATION

If the same error persists after 2 iterations:
1. Widen the search — read more context around the failing code
2. Check for deeper root causes (configuration, dependencies, environment)
3. Delegate to specialist agents based on failure category:
   - `COMPILE_ERROR` / `MISSING_IMPORT` → debugger agent
   - `INFRASTRUCTURE` → check environment setup (DB connection, Redis, service health)
   - `CONTRACT_MISMATCH` → delegate to /contract-test for contract analysis
   - `MIGRATION_FAILURE` → delegate to /db-migrate-verify for schema validation
   - `VISUAL_REGRESSION` → delegate to /verify-screenshots for baseline comparison
4. If confidence remains Low after specialist consultation, report UNRESOLVED and ask for user input

## CRITICAL RULES

- Maximum {max_iterations} iterations — do NOT infinite loop
- Each iteration must try a DIFFERENT fix approach
- Never suppress errors or add broad exception handlers
- If confidence is Low, explain reasoning and ask for user input
