---
name: fix-loop
description: >
  Analyze failures and iteratively apply minimal fixes, optionally retesting until resolved.
  Full Loop mode (with retest command) iterates until green. Single Fix mode
  (no retest) does one pass. Use when tests fail, builds break, or runtime errors
  occur. For unclear root causes or repeated failures, escalate to
  /systematic-debugging. For end-to-end bug resolution with verified proof,
  use /debugging-loop instead.
triggers:
  - fix-loop
  - fix tests
  - fix build
  - iterate fix
  - fix failures
  - retest until green
allowed-tools: "Bash Read Grep Glob Write Edit Skill Agent"
argument-hint: "[failure_output] [retest_command: <cmd>] [max_iterations: N] [--strict-gates] [--capture-proof | --no-capture-proof]"
version: "1.4.0"
type: workflow
---

# Fix Loop — Iterative Fix Cycle

Analyze failures, apply minimal fixes, and optionally retest until resolved.

**Critical:** Maximum {max_iterations} fix attempts — each MUST try a different approach. For simple failures with a known retest command, use this skill. When root cause is unclear or fix-loop has failed 2+ times, escalate to `/systematic-debugging`. For end-to-end bug resolution with verified proof, use `/debugging-loop` instead.

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
| `--strict-gates` | false | Passed by orchestrator for consistency; no upstream gate for fix-loop |
| `--capture-proof` | true (from config) | Forward to retest command — capture screenshots on every test |
| `--no-capture-proof` | — | Disable screenshot capture even if config says true |

---

## STEP 1: Analyze Failure (via test-failure-analyzer-agent)

Delegate failure classification to `test-failure-analyzer-agent` for structured
diagnosis. The agent is read-only — it classifies failures and suggests fixes
but does not modify files.

```
Agent("test-failure-analyzer-agent", prompt="Analyze these test failures and
classify each into exactly one category. Group by root cause. Output: category,
root file:line, fix suggestion, confidence level.

Test output:
$FAILURE_OUTPUT")
```

The agent returns a structured analysis with:
- **Category** per failure (one of: COMPILE_ERROR, ASSERTION_FAILURE, TIMEOUT,
  FIXTURE_MISMATCH, MISSING_IMPORT, RUNTIME_EXCEPTION, FLAKY_TEST,
  INFRASTRUCTURE, CONTRACT_MISMATCH, MIGRATION_FAILURE, AUTH_ERROR,
  VISUAL_REGRESSION, SCHEMA_VALIDATION, PERFORMANCE_REGRESSION,
  RESOURCE_LEAK, CONCURRENCY_ERROR, TEST_POLLUTION, EMPTY_ASSERTION)
- **Root file and line** for each failure
- **Grouped root causes** (multiple tests may fail from one issue)
- **Fix priority order** (which fix unblocks the most tests)
- **Confidence level** (High/Medium/Low)

Use the agent's output to drive STEP 1A (flaky detection) and STEP 2 (apply fix).
If the agent returns Low confidence on all failures, escalate to user immediately
rather than attempting fixes.

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

If `--capture-proof` is enabled, append the platform-appropriate screenshot flag
to the retest command:
- pytest/playwright: set `screenshot: 'on'` in config or `--screenshot on`
- Maestro: auto-inject `takeScreenshot` after each flow step
- Flutter: append capture-all mode for golden collection

Screenshots from each iteration are stored in
`test-evidence/{run_id}/screenshots/` with iteration suffix:
`{test_name}.iter{N}.{pass|fail}.png`

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
   - `COMPILE_ERROR` / `MISSING_IMPORT` → debugger-agent
   - `INFRASTRUCTURE` → check environment setup (DB connection, Redis, service health)
   - `CONTRACT_MISMATCH` → delegate to /contract-test for contract analysis
   - `MIGRATION_FAILURE` → delegate to /db-migrate-verify for schema validation
   - `VISUAL_REGRESSION` → delegate to /verify-screenshots for baseline comparison
4. If confidence remains Low after specialist consultation, report UNRESOLVED and ask for user input

## AUTO-RECORD LEARNING (MANDATORY)

After a fix iteration succeeds (test goes from FAIL → PASS), ALWAYS record the learning before reporting success. This is NOT optional.

1. **Classify** the fix: `TIMING`, `NETWORK`, `BUILD`, `STATE`, `CONFIG`, `API-COMPAT`, `AUTH`, `EMULATOR`
2. **Route** to the right knowledge base:
   - Test timing/flaky issues → `/test-knowledge add`
   - Stack-specific issues (emulator, platform, env) → stack knowledge base if available
   - Other → write symptom + fix to `.claude/learnings.json`
3. **Log** the learning:
   ```
   LEARNING RECORDED: [category] [one-line summary]
   ```

This ensures the same failure is auto-resolved next time without re-diagnosing.

## CRITICAL RULES

- Maximum {max_iterations} iterations — do NOT infinite loop — Why: unbounded retries waste compute and mask unfixable issues
- Each iteration must try a DIFFERENT fix approach — Why: repeating the same fix wastes iterations and hits max without progress
- Never suppress errors or add broad exception handlers — Why: suppression hides the real bug and creates silent failures downstream
- If confidence is Low, explain reasoning and ask for user input — Why: low-confidence fixes often introduce new bugs that compound the original failure
- ALWAYS record learning after successful fix — no exceptions — Why: unrecorded fixes get re-diagnosed from scratch next time, wasting future sessions
