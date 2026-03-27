---
name: e2e-visual-run
description: >
  Run full E2E suite with async queue-based orchestration, per-test screenshot
  capture on failure, dual-signal visual verification (accessibility tree + screenshot
  AI diff), and classification-driven auto-healing with 3-attempt cap per test.
  Use with optional section filter: /e2e-visual-run salary
type: workflow
allowed-tools: "Bash Read Write Edit Grep Glob Skill"
argument-hint: "[section-name]"
version: "1.0.0"
---

Autonomous E2E test suite runner with visual verification and self-healing.
Screenshots captured for EVERY test (pass and fail) because the screenshot
verdict is authoritative — exit codes are secondary signals. Dual-signal
verification ensures both structural (a11y tree) and visual (screenshot)
correctness. Failures auto-classified and repaired. Global retry budget
prevents runaway fixing.

## STEP 1: Pre-Flight Checks

Verify the environment before running any tests.

1. Check dev server is running (detect ports from project config or CLAUDE.md)
2. Check database is accessible (run project's DB check command if available)
3. Check auth bypass is configured for test mode (if applicable)
4. Delete stale auth/session files if they exist
5. Run type-check and lint — fix errors before proceeding
6. Read `.claude/config/e2e-pipeline.yml` for queue settings, retry limits, and
   classification config. If the file doesn't exist, use these defaults:
   ```
   queue.ordering: longest-first
   queue.batch_size: 5
   retry.global_budget: 15
   retry.per_test_max_attempts: 3
   agents.test_scout.screenshot_mode: always
   agents.visual_inspector.dual_signal: true
   agents.test_healer.auto_fix_classifications: [SELECTOR, TIMING, DATA, FLAKY_TEST, INFRASTRUCTURE, TEST_POLLUTION]
   agents.test_healer.human_review_classifications: [LOGIC_BUG, VISUAL_REGRESSION]
   ```
7. Create directories: `mkdir -p .pipeline test-evidence/{run_id}/screenshots test-evidence/{run_id}/a11y test-results`
8. Initialize state file `.pipeline/e2e-state.json` with empty queues

**run_id format:** `{ISO-8601-timestamp}_{7-char-git-sha}` (replace `:` with `-` for filesystem safety)

## STEP 2: Discover and Queue Tests

Populate the test queue with prioritized ordering.

1. Discover test files using the project's test command with `--list` flag,
   or scan the E2E test directory (e.g., `e2e/tests/`, `tests/e2e/`)
2. If a section argument was provided (e.g., `/e2e-visual-run salary`),
   filter to only that section's tests
3. Order tests by estimated duration (longest-first) using `duration_hints`
   from config. When no hints exist, fall back to alphabetical order.
   Longest-first reduces total wall time by front-loading slow tests.
4. Write all test items to `test_queue` in the state file:
   ```json
   {"test": "test_name", "file": "<test-file-path>", "attempt": 0, "estimated_duration_ms": null}
   ```

## STEP 3: Execute Tests (Scout Phase)

Run tests and capture evidence for verification. Read `references/scout-phase.md`
for detailed framework-specific capture guidance.

For each batch of tests from `test_queue` (batch_size from config):

1. **Run the test** using the project's test command with `--workers=1`
2. **Record exit code** and duration
3. **Capture screenshot** for EVERY test (pass and fail) — the screenshot
   verdict is authoritative, exit codes are secondary signals:
   - Playwright: `screenshot: 'on'` in config or `await page.screenshot()`
   - Cypress: `cy.screenshot()` in afterEach
   - Selenium: `driver.save_screenshot()` in afterEach
   - Detox: `device.takeScreenshot()` in afterEach
   Save to `test-evidence/{run_id}/screenshots/{test_name}.{pass|fail}.png`
4. **Capture accessibility tree** for EVERY test (pass or fail):
   - Playwright: `page.accessibility.snapshot()`
   - Other frameworks: capture DOM structure as fallback
   Save to `test-evidence/{run_id}/a11y/{test_name}.json`
5. **Move item** from `test_queue` to `verify_queue` in state file with results:
   ```json
   {
     "test": "test_name",
     "exit_code_result": "PASSED|FAILED",
     "screenshot_path": "test-evidence/{run_id}/screenshots/test_name.{pass|fail}.png",
     "a11y_snapshot_path": "test-evidence/{run_id}/a11y/test_name.json",
     "duration_ms": 1234,
     "error_output": "stderr if failed, null if passed"
   }
   ```
6. **Write incrementally** — update state file after EACH test, not in batch

## STEP 4: Verify Results (Inspector Phase)

Dual-signal verification: accessibility tree + screenshot AI diff.
Read `references/inspection-phase.md` for detailed verification criteria.

For each item in `verify_queue`:

1. **Accessibility tree verification** — Parse the a11y snapshot JSON:
   - Required roles present (buttons, links, headings, form controls)
   - Labels are meaningful (not empty, not "undefined")
   - Hierarchy correct (headings nested properly, landmarks present)
   - Interactive elements reachable (not hidden when they should be active)

2. **Screenshot verification** (if screenshot exists) — Use `Skill("verify-screenshots")`:
   - Compare against baseline if available (`baselines/{test_name}.png`)
   - Use visual expectation text hint if available (from `visual-tests.yml`)
   - Fall back to generic AI review: layout correct, data populated, no error
     dialogs, no spinners/skeletons, text readable

3. **Dual-signal verdict:**

   | A11y Tree | Screenshot | Verdict | Action |
   |-----------|-----------|---------|--------|
   | PASS | PASS | **PASS** | Move to `completed` |
   | PASS | FAIL | **FAIL** | Visual regression — route to `fix_queue` |
   | FAIL | PASS | **FAIL** | Accessibility regression — route to `fix_queue` |
   | FAIL | FAIL | **FAIL** | Both broken — route to `fix_queue` (high priority) |

4. **Dynamic content handling** — Before flagging as FAILED, check for:
   - Timestamps/dates: ignore in comparison
   - Loading spinners (`aria-busy="true"`): wait and re-capture
   - Random avatars/images: ignore region
   - Empty state with no `aria-busy`: real failure

5. **Record verdict** in state file with confidence score (0.0-1.0)

## STEP 5: Heal Failures (Healer Phase)

Classification-driven targeted repair. Read `references/healing-phase.md`
for detailed fix strategies per classification.

For each item in `fix_queue`:

1. **Check attempt count** — if >= `per_test_max_attempts` from config (default 3),
   move to `known_issues` with full history and skip to next item

2. **Check global budget** — if `global_retries_used >= global_budget` (default 15),
   STOP all healing and proceed to Step 6

3. **Diagnose** — Invoke `Skill("fix-loop")` with:
   - `failure_output`: error output from scout phase
   - `retest_command`: the single-test run command
   - `max_iterations`: 1 (one fix attempt per healing pass)

4. **Classification-specific repair:**

   | Classification | Strategy | Auto-Fix? |
   |---------------|----------|-----------|
   | SELECTOR | Regenerate selectors using a11y tree. Prefer `getByRole()`, `getByLabel()` | Yes |
   | TIMING | Add explicit waits (`waitFor`, `toBeVisible`). Replace `sleep()` | Yes |
   | DATA | Fix test data setup/teardown. Update fixtures. Seed missing data | Yes |
   | FLAKY_TEST | Identify source (timing, shared state). Stabilize per testing rule | Yes |
   | INFRASTRUCTURE | Environment reset, then retry | Yes (env only) |
   | TEST_POLLUTION | Isolate with `beforeEach` reset, per-test browser context | Yes |
   | VISUAL_REGRESSION | Flag for human review with before/after screenshots | Human review |
   | LOGIC_BUG | Log with full diagnosis. Do NOT auto-fix application code | Human review |

5. **After fix attempt:**
   - Increment attempt count and `global_retries_used`
   - If fix succeeded: move item back to `test_queue` (re-enters Step 3)
   - If fix failed and attempts remain: try a DIFFERENT approach next pass
   - Each attempt MUST try a different strategy (tracked via history)

6. **Fix quality checks** before requeuing:
   - Syntax check: modified test file parses without errors
   - Import check: no broken imports introduced
   - Related test check: if shared fixture modified, flag potential regressions
   - Minimal change: fewest lines possible

## STEP 6: Aggregate Results and Report

After all queues drain (or global budget exhausted):

1. **Compute verdict:**
   - PASSED: all tests in `completed` with PASS verdict, zero `known_issues`
   - FAILED: any test in `known_issues` OR any FAIL verdict in `completed`

2. **Update duration hints** in `.claude/config/e2e-pipeline.yml` with
   observed durations (if config file exists)

3. **Write** `test-results/e2e-pipeline.json`:
   ```json
   {
     "skill": "e2e-visual-run",
     "timestamp": "<ISO-8601>",
     "result": "PASSED|FAILED",
     "run_id": "<run_id>",
     "summary": {
       "total": 42, "passed": 38, "failed": 0,
       "healed": 3, "known_issues": 1, "skipped": 0
     },
     "global_retries_used": 5,
     "global_retries_remaining": 10,
     "duration_ms": 180000,
     "failures": [],
     "known_issues": [],
     "warnings": []
   }
   ```

4. **Present summary:**
   ```
   E2E Pipeline: PASSED | FAILED
     Tests: 42 total | 38 passed | 3 healed | 1 known issue
     Duration: 3m 0s
     Retries: 5/15 used
     Evidence: test-evidence/{run_id}/

     Known Issues:
       test_animation (TIMING) — CSS animation delays interaction after 3 attempts
   ```

5. **Git checkpoint** — if any tests were healed, commit the test fixes:
   `fix(e2e): heal N test failures (SELECTOR: X, TIMING: Y, DATA: Z)`

## CRITICAL RULES

- NEVER skip pre-flight checks — environment issues masquerade as test failures
- ALWAYS capture screenshots for EVERY test (pass and fail) — screenshot verdict is authoritative
- NEVER treat exit code as authoritative for UI tests — dual-signal verdict is authoritative
- NEVER auto-fix LOGIC_BUG or VISUAL_REGRESSION — flag for human review
- NEVER apply the same fix twice — track history, try different approaches each attempt
- NEVER exceed global retry budget (default 15) — stop healing and report
- NEVER modify application source code for SELECTOR/TIMING/DATA fixes — only test code
- NEVER skip accessibility tree capture for passing tests — dual-signal needs it always
- NEVER batch-write results — update state file after EACH test for progress visibility
- ALWAYS read `.claude/config/e2e-pipeline.yml` for settings — fall back to defaults if missing
