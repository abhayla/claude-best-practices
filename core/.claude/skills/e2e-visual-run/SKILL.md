---
name: e2e-visual-run
description: >
  Run a full Playwright E2E suite with queue-based orchestration, per-test
  screenshot capture, dual-signal visual verification (ARIA snapshot + screenshot
  AI diff), and confidence-gated auto-healing. Auto-detects the Playwright
  config and dev server for zero-config execution. Use with optional section
  filter: /e2e-visual-run salary. Use --update-baselines to approve intentional
  visual changes. Playwright-only — NOT for Cypress/Selenium/Detox/Flutter
  (use their native runners), one-off screenshot comparison (use
  /verify-screenshots), post-change targeted verification (use /auto-verify),
  or E2E best practices reference (use /e2e-best-practices).
triggers:
  - run e2e with screenshots
  - e2e visual verification
  - run e2e suite visually
  - visual e2e test run
  - e2e dual-signal verification
  - run e2e with auto-healing
type: workflow
allowed-tools: "Bash Read Write Edit Grep Glob Skill Agent"
argument-hint: "[section-name] [--update-baselines]"
version: "3.0.0"
---

Autonomous Playwright E2E test suite runner with visual verification and
self-healing. Auto-detects the Playwright config and dev server for zero-config
execution. Screenshots captured for EVERY test (pass and fail) because the
screenshot verdict is authoritative — exit codes are secondary signals.
Dual-signal verification ensures both structural (ARIA snapshot) and visual
(screenshot) correctness. Failures classified with confidence scores — only
high-confidence fixes are auto-applied. Global retry budget prevents runaway
fixing.

**Scope:** This skill targets Playwright only. Cypress, Selenium, Detox, and
Flutter are intentionally out of scope — use their native runners. Removing
multi-framework support in v3.0.0 tightened the dual-signal contract (ARIA
YAML baselines + `toHaveScreenshot()`), which is Playwright-specific.

## Mode Detection

| Argument | Mode | Behavior |
|----------|------|----------|
| *(none)* or `[section-name]` | **Full Pipeline** | Steps 0–6: discover, run, verify, heal, report |
| `--update-baselines` | **Baseline Update** | Steps 0–3 only: discover, run, capture, then replace all baselines |

**Baseline Update mode** (`--update-baselines`):
1. Run Steps 0–3 normally (discover framework, run tests, capture evidence)
2. For each captured screenshot: copy to `{visual.baseline_dir}/{test_name}.png`
   (create baseline dir if it doesn't exist)
3. For Playwright ARIA snapshots: run tests with `--update-snapshots` flag to
   regenerate YAML baselines in `__snapshots__/`
4. Skip Steps 4–5 (no verification or healing)
5. Report: "Updated N screenshot baselines and N ARIA snapshots"
6. Do NOT auto-commit — let the user review the diff before committing

Can be combined with section filter: `/e2e-visual-run salary --update-baselines`

## STEP 0: Environment Discovery

Auto-detect the Playwright config, test commands, and dev server for
autonomous execution. This step makes the skill work in any Playwright
project without manual config.

1. **Detect the Playwright config** — scan for `playwright.config.{ts,js,mjs}`
   in the project root. Record:

   | Setting | Value |
   |---------|-------|
   | Framework | Playwright |
   | Test command | `npx playwright test` |
   | Single-test command | `npx playwright test {file} --grep "{test}" --workers=1` |

   Playwright defaults to headless in CI; no flag needed.

   If no config found: fail with `"No playwright.config.{ts,js,mjs} found.
   This skill is Playwright-only — for Cypress, Selenium, Detox, or Flutter
   E2E suites, use the framework's native test runner."`

2. **Detect dev server** — scan in priority order:
   a. Read `webServer.command` and `webServer.url` from `playwright.config.*`
   b. Fall back to `package.json` scripts: check for `dev`, `start`, `serve`
      keys (in that order)

3. **Start dev server if not running**:
   - Check if the detected URL responds (`curl -sf --max-time 2 {url}`)
   - If not responding: start the dev server in background, wait up to 30s
     for health
   - Store PID in `.pipeline/dev-server.pid` for cleanup
   - **PID safety:** record the process command alongside the PID; in Step 1
     and Step 6, verify the process name matches before killing (prevents
     killing an unrelated process that reused the PID)
   - **Port-in-use guard:** if the URL responds but was not started by us,
     and the Playwright config has `webServer.reuseExistingServer: false`,
     fail with `"Port {port} is in use by another process — stop it before
     running the suite."`
   - If no dev server detected and no URL responds: warn but continue (tests
     may manage their own server via `globalSetup`)

4. **Detect test directory** — read `testDir` from `playwright.config.*`;
   fall back to scanning `e2e/`, `tests/e2e/`, or `test/e2e/`

5. **Write discovered config** to state file for downstream steps:
   ```json
   {
     "framework": "playwright",
     "test_command": "npx playwright test",
     "single_test_command": "npx playwright test {file} --grep \"{test}\" --workers=1",
     "dev_server": {
       "command": "npm run dev",
       "url": "http://localhost:3000",
       "pid": 12345,
       "process_name": "node",
       "started_by_us": true
     },
     "test_dir": "e2e/"
   }
   ```

6. **Ensure the Playwright config supports evidence capture:**
   Read `playwright.config.*` and verify these settings exist. If missing,
   add them:
   ```typescript
   use: {
     screenshot: 'on',                    // capture every test (pass and fail)
   },
   outputDir: 'test-evidence/latest',     // evidence output location
   ```
   If the project has no shared fixture for a11y snapshot capture, create
   `{test_dir}/e2e-evidence.setup.ts` (see Step 1 for fixture details).
   Log all config modifications so the user can review them on the next
   `git status`. First-run artifacts (config edits, fixture, generated
   baselines in `__snapshots__/`) are flagged in the Step 6 report so the
   user can commit them intentionally — they are NOT auto-committed.

## STEP 1: Pre-Flight Checks

Verify the environment before running any tests.

1. If `.pipeline/dev-server.pid` exists from a previous crashed run, kill the
   stale process before starting a new one
2. Delete stale auth/session files if they exist
3. Run type-check and lint — fix errors before proceeding
4. Read `.claude/config/e2e-pipeline.yml` for queue settings, retry limits, and
   classification config. If the file doesn't exist, use these defaults:
   ```
   queue.ordering: longest-first
   queue.batch_size: 5
   retry.global_budget: 15
   retry.per_test_max_attempts: 3
   pipeline.timeout_minutes: 30
   healing.confidence_threshold: 0.85
   visual.threshold: 0.2
   visual.animations: disabled
   agents.test_scout.screenshot_mode: always
   agents.visual_inspector.dual_signal: true
   agents.visual_inspector.aria_snapshot_format: yaml
   agents.visual_inspector.auto_generate_baseline: true
   agents.test_healer.auto_fix_classifications: [SELECTOR, TIMING, DATA, FLAKY_TEST, INFRASTRUCTURE, TEST_POLLUTION]
   agents.test_healer.human_review_classifications: [LOGIC_BUG, VISUAL_REGRESSION]
   ```
5. **Ensure evidence capture fixture exists** (Playwright, first run only):
   If `{test_dir}/e2e-evidence.setup.ts` does not exist, create it:
   ```typescript
   // e2e-evidence.setup.ts — auto-generated by e2e-visual-run
   // Captures a11y tree JSON + applies pre-capture prep for every test
   import { test as base, expect } from '@playwright/test';
   export const test = base.extend({
     // Auto-capture a11y snapshot after each test
     page: async ({ page }, use, testInfo) => {
       await use(page);
       // Post-test: capture a11y tree JSON for healing phase
       const snapshot = await page.locator('body').ariaSnapshot();
       const name = testInfo.title.replace(/\s+/g, '_');
       const result = testInfo.status === 'passed' ? 'pass' : 'fail';
       await testInfo.attach(`a11y-${name}.${result}`, {
         body: JSON.stringify(snapshot, null, 2), contentType: 'application/json'
       });
     },
   });
   export { expect };
   ```
   Log: "Created e2e-evidence.setup.ts — tests should import `{ test }` from
   this file instead of `@playwright/test` for full evidence capture.
   Existing tests will still work without changes (screenshots captured via config)."
6. Create directories: `mkdir -p .pipeline test-evidence/{run_id}/screenshots test-evidence/{run_id}/a11y test-results`
7. Initialize state file `.pipeline/e2e-state.json` with empty queues and
   the discovered config from Step 0

**run_id format:** `{ISO-8601-timestamp}_{7-char-git-sha}` (replace `:` with `-` for filesystem safety)

## STEP 2: Discover and Queue Tests

Populate the test queue with prioritized ordering.

1. Discover test files using `npx playwright test --list` (machine-readable),
   or scan the discovered `test_dir` from Step 0
2. If a section argument was provided (e.g., `/e2e-visual-run salary`),
   filter using Playwright's `--grep` on the test title. Section matching
   semantics (applied in this order, stop on first match):
   - **Describe block title**: matches any test inside a `test.describe("{section}")` block
   - **Test title substring**: matches any test whose title contains `{section}` (case-insensitive)
   - **@tag**: if `{section}` starts with `@`, matches tests tagged via `test("title @tag", ...)`
   - **File path substring**: matches any test in a file whose path contains `{section}`

   Generate the grep pattern accordingly (e.g., `--grep "salary"` or
   `--grep "@salary"`) and record it in the state file under `section_filter`.
3. Order tests by estimated duration (longest-first) using `duration_hints`
   from config. When no hints exist, fall back to alphabetical order.
   Longest-first reduces total wall time by front-loading slow tests.
4. **Read test history** — if `.pipeline/test-history.json` exists, load flakiness
   scores. Log warnings for tests with score > 0.3:
   `"test_dashboard: flakiness_score=0.6 (POSSIBLY_FLAKY, last classified as TIMING)"`
5. Write all test items to `test_queue` in the state file:
   ```json
   {"test": "test_name", "file": "<test-file-path>", "attempt": 0, "estimated_duration_ms": null, "flakiness_score": 0.0}
   ```

## STEP 3: Execute Tests (Scout Phase)

Run tests and capture evidence for verification. Read `references/scout-phase.md`
for detailed framework-specific capture guidance.

Process tests in batches of `batch_size` (default 5) from `test_queue`.
Each batch runs sequentially via CLI — one `single_test_command` per test.
Update the state file after EACH individual test completes (not per-batch).
The batch size controls how many tests run before checking verify_queue.

For each test in the current batch:

1. **Run the test** using the discovered `single_test_command` from Step 0
2. **Record exit code** and duration
3. **Pre-capture preparation** — handled via config and fixtures, not in-test
   API calls (the skill runs tests via CLI and cannot inject page-object calls):
   - Step 0.6 ensures `screenshot: 'on'` in `playwright.config.*`
   - If `visual.mask_selectors` are configured, inject a CSS stylesheet that
     sets `visibility: hidden` on masked selectors via Playwright's
     `expect.toHaveScreenshot.stylePath` or the evidence fixture
   - CSS animations are disabled via the evidence fixture's
     `reducedMotion: 'reduce'` media emulation
4. **Capture screenshot** for EVERY test (pass and fail) — the screenshot
   verdict is authoritative, exit codes are secondary signals:
   - Handled automatically via `screenshot: 'on'` in config (set in Step 0.6)
   - Screenshots and attachments are written to `test-evidence/latest/`
     (the `outputDir` set in Step 0.6)
   - After the test run (Step 3.5), rename `test-evidence/latest/` to
     `test-evidence/{run_id}/` and reorganize into `screenshots/` and `a11y/`
     subdirectories
5. **Capture accessibility tree** for EVERY test (pass or fail):
   - The evidence fixture (`e2e-evidence.setup.ts` from Step 1.5) auto-captures
     a11y JSON as a test attachment after each test
   - Collect attachments from Playwright's output and copy to
     `test-evidence/{run_id}/a11y/{test_name}.json`
   - For YAML baselines: run with `--update-snapshots` on first run to generate
     `__snapshots__/` baselines. On subsequent runs, `toMatchAriaSnapshot()` in
     tests compares against stored baselines automatically
6. **Move item** from `test_queue` to `verify_queue` in state file with results:
   ```json
   {
     "test": "test_name",
     "exit_code_result": "PASSED|FAILED",
     "screenshot_path": "test-evidence/{run_id}/screenshots/test_name.{pass|fail}.png",
     "a11y_snapshot_path": "test-evidence/{run_id}/a11y/test_name.json",
     "a11y_yaml_baseline": true,
     "duration_ms": 1234,
     "error_output": "stderr if failed, null if passed"
   }
   ```
7. **Write incrementally** — update state file after EACH test, not in batch

## STEP 3.5: Map Playwright Output to Evidence Directory

Playwright saves artifacts to its own directory structure (e.g.,
`test-results/{hash}/test-finished-1.png` with truncated names). Map
these to the canonical evidence structure before Step 4 verification.

1. Scan `test-evidence/latest/` (the `outputDir` from Step 0.6):
   - Screenshots: find `*.png` files, rename to
     `test-evidence/{run_id}/screenshots/{test_name}.{pass|fail}.png`
     using the test name from the parent directory or Playwright's JSON report
   - A11y attachments: find `a11y-*.json` attachments, copy to
     `test-evidence/{run_id}/a11y/{test_name}.json`
   - Parse `test-evidence/latest/results.json` (Playwright JSON reporter)
     for test name → artifact path mapping if direct naming is ambiguous

2. **Verify mapping**: log count of mapped screenshots and a11y files.
   If any test in `verify_queue` has no corresponding screenshot, log a
   warning and flag that verdict as `low_confidence` (single-signal only).

## STEP 4: Verify Results (Inspector Phase)

Dual-signal verification: accessibility tree + screenshot AI diff.
Read `references/inspection-phase.md` for detailed verification criteria.
Do NOT verify a11y inline for large test suites — dispatch an agent to
batch-verify all a11y snapshots at once (prevents context burn from 20+
inline JSON parses). Screenshot verification uses `verify-screenshots` skill.

**Dispatch a11y inspector agent** for all items in `verify_queue`:
```
Agent("general-purpose", prompt="
  You are the accessibility inspector for E2E test verification.
  Evidence directory: test-evidence/{run_id}/a11y/
  State file: .pipeline/e2e-state.json (read verify_queue for test list)
  Reference: read references/inspection-phase.md for the full checklist.

  For each test, apply the framework-dependent verification below, then
  write per-test verdicts {test: verdict, confidence, reason} to
  .pipeline/a11y-verdicts.json. Output: N passed, N failed, N changed.
")
```

The agent follows these verification rules for each item in `verify_queue`:

1. **Accessibility tree verification:**

   **With ARIA YAML baseline:**
   - Run `toMatchAriaSnapshot()` against stored YAML baseline in `__snapshots__/`
   - If baseline doesn't exist (first run): auto-generate it, log "A11y baseline
     created — will compare on next run", treat as PASS for this run (flag
     as `first_run_baseline` in the verdict so Step 6 can surface it)
   - Partial matching: omit attributes that vary between runs
   - Regex for dynamic text: `/\d+ items/`, `/Updated .*/`

   **Without a baseline (before first `--update-snapshots` run):**
   - Parse the a11y snapshot JSON using the checklist in
     `references/inspection-phase.md` (structural, state, data population checks)

2. **Screenshot verification** — Use `Skill("verify-screenshots")` if available:
   ```
   Skill("verify-screenshots", args="--proof-mode --run-id={run_id} --threshold={visual.threshold}")
   ```

   **Provisioning check:** before calling `Skill("verify-screenshots")`, verify
   the skill is installed by checking that
   `.claude/skills/verify-screenshots/SKILL.md` exists (`Glob` pattern). If
   the file is missing, use the fallback below and log:
   "verify-screenshots not provisioned — falling back to Playwright native
   `toHaveScreenshot()`. Provision /verify-screenshots for richer diffs."

   **Fallback (verify-screenshots missing):**
   - Use Playwright native `toHaveScreenshot()` with threshold from config
   - On first run (no baseline): `toHaveScreenshot()` auto-creates the
     baseline and passes. Treat this as `first_run_baseline` and surface it
     in Step 6 so the user commits the baseline intentionally

3. **Dual-signal verdict:**

   | A11y Tree | Screenshot | Exit Code | Verdict | Destination |
   |-----------|-----------|-----------|---------|-------------|
   | PASS | PASS | PASS | **PASS** | `completed` |
   | CHANGED | CHANGED | PASS | **EXPECTED_CHANGE** | `expected_changes` |
   | CHANGED | PASS | PASS | **EXPECTED_CHANGE** | `expected_changes` |
   | PASS | CHANGED | PASS | **EXPECTED_CHANGE** | `expected_changes` |
   | PASS | FAIL | any | **FAIL** (visual regression) | `fix_queue` |
   | FAIL | PASS | any | **FAIL** (a11y regression) | `fix_queue` |
   | FAIL | FAIL | any | **FAIL** (both broken) | `fix_queue` (high priority) |

   **EXPECTED_CHANGE detection:** if exit code is PASS but visual or a11y differs
   from baseline, the UI likely changed intentionally. Route to the declared
   `expected_changes` queue in state (NOT `fix_queue`, NOT `completed`). Step 6
   reports these separately so the user can run `/e2e-visual-run --update-baselines`
   to approve them.

   **State schema addendum:** the state file declares four queues plus a
   completion lane — `test_queue`, `verify_queue`, `fix_queue`, `expected_changes`,
   `completed`, `known_issues`. Every verdict MUST route to exactly one of
   these; there is no implicit "other" bucket.

4. **Dynamic content handling** — Before flagging as FAILED, check for:
   - Timestamps/dates: ignore in comparison
   - Loading spinners (`aria-busy="true"`): wait and re-capture
   - Random avatars/images: ignore region (covered by `visual.mask_selectors`)
   - Empty state with no `aria-busy`: real failure

5. **Record verdict** in state file with confidence score (0.0-1.0)

## STEP 5: Heal Failures (Healer Phase)

Confidence-gated, classification-driven repair. Read `references/healing-phase.md`
for detailed fix strategies and confidence heuristics per classification.

For each item in `fix_queue`:

1. **Check attempt count** — if >= `per_test_max_attempts` from config (default 3),
   move to `known_issues` with full history and skip to next item

2. **Check global budget** — if `global_retries_used >= global_budget` (default 15),
   STOP all healing and proceed to Step 6

3. **Check flakiness history** — if `history.quarantine_flaky` is true (default),
   read the test's `flakiness_score` from `.pipeline/test-history.json`:
   - score >= `history.flaky_threshold` (default 0.7) → AUTO-QUARANTINE CHECK:
     - Read `quarantined_since_run` and `probe_runs_since_quarantine` from history
     - **Probe-run recovery rule**: every `history.probe_interval` runs (default 5),
       force one probe attempt through the full healing cycle even if quarantined.
       This prevents permanent quarantine when the underlying flake is fixed.
     - If this is a probe run: proceed normally, label attempt as `probe_run: true`
     - Otherwise: move to `known_issues` with `"reason": "historically_flaky"`,
       record `probe_runs_since_quarantine += 1`. Do not spend retry budget.
   - **Decay rule**: if the most recent `history.decay_window` runs (default 3)
     all PASSED, reset `flakiness_score` to 0 and remove from quarantine — the
     flake is considered rehabilitated.
   - score 0.3–0.7 → proceed but flag as `POSSIBLY_FLAKY` in warnings
   - score < 0.3 or no history → genuine failure, proceed normally

4. **Pre-classify** using the decision tree in `references/healing-phase.md`:
   - If VISUAL_REGRESSION or LOGIC_BUG → skip fix-loop entirely, move directly
     to `known_issues` with human-review flag. Do not waste a subagent call.
   - Otherwise → proceed to diagnosis

5. **Diagnose and fix** — dispatch in a subagent to prevent context burn
   when multiple failures need healing:
   ```
   Agent("general-purpose", prompt="
     Invoke Skill('fix-loop') with:
     - failure_output: {error_output from scout phase}
     - retest_command: {single_test_command from Step 0}
     - max_iterations: 1
     Return: classification, confidence (HIGH/MEDIUM/LOW), fix description,
     and whether the fix succeeded.
   ")
   ```

6. **Confidence gate** — read fix-loop's returned confidence level:

   | fix-loop Confidence | Numeric Mapping | Action |
   |--------------------|-----------------|--------|
   | HIGH | >= 0.85 (healing.confidence_threshold) | Accept fix, proceed to quality checks |
   | MEDIUM | 0.5–0.85 | Accept fix but flag as `low_confidence_fix` in state |
   | LOW | < 0.5 | Revert fix, move to `known_issues` with suggestion attached |

   The authoritative confidence comes from fix-loop's `test-failure-analyzer-agent`.
   The pre-classification in step 4 is a routing gate only.

7. **Classification-specific repair** (for reference — fix-loop handles the details):

   | Classification | Strategy | Auto-Fix? |
   |---------------|----------|-----------|
   | SELECTOR | Regenerate selectors using a11y tree. Prefer `getByRole()`, `getByLabel()` | Yes (if confidence gate passes) |
   | TIMING | Add explicit waits (`waitFor`, `toBeVisible`). Replace `sleep()` | Yes (if confidence gate passes) |
   | DATA | Fix test data setup/teardown. Update fixtures. Seed missing data | Yes (if confidence gate passes) |
   | FLAKY_TEST | Identify source (timing, shared state). Stabilize per testing rule | Yes (if confidence gate passes) |
   | INFRASTRUCTURE | Environment reset, then retry | Yes (env only) |
   | TEST_POLLUTION | Isolate with `beforeEach` reset, per-test browser context | Yes (if confidence gate passes) |
   | VISUAL_REGRESSION | Flag for human review with before/after screenshots | Human review (pre-classified in step 4) |
   | LOGIC_BUG | Log with full diagnosis. Do NOT auto-fix application code | Human review (pre-classified in step 4) |

8. **After fix attempt:**
   - Increment attempt count and `global_retries_used`
   - Record classification, confidence, and fix description in history
   - If fix succeeded: move item back to `test_queue` (re-enters Step 3)
   - If fix failed and attempts remain: try a DIFFERENT approach next pass
   - Each attempt MUST try a different strategy (tracked via history)

9. **Fix quality checks** before requeuing:
   - Syntax check: modified test file parses without errors
   - Import check: no broken imports introduced
   - Related test check: if shared fixture modified, flag potential regressions
   - Minimal change: fewest lines possible

## STEP 6: Aggregate Results and Report

After all queues drain (or global budget exhausted):

1. **Compute verdict:**
   - PASSED: all tests in `completed` with PASS verdict, zero `known_issues`
   - NEEDS_REVIEW: any test with EXPECTED_CHANGE verdict (intentional UI changes detected)
   - FAILED: any test in `known_issues` OR any FAIL verdict in `completed`

2. **Update duration hints** in `.claude/config/e2e-pipeline.yml` — write observed
   durations as median of current observation and existing hint (or just current
   if no hint exists). This creates a self-improving feedback loop for queue ordering.
   Format: `duration_hints: { test_checkout_flow: 45000, test_login: 12000 }` (ms).

3. **Update test history** — append each test's result (PASS/FAIL) to
   `.pipeline/test-history.json`. Keep a sliding window of the last N runs
   (default: `history.window_size` = 10). Recompute `flakiness_score` as
   `FAIL count / total runs`. This file persists across runs (not in cleanup list).

4. **Tear down dev server** — if Step 0 started it (`dev_server.started_by_us: true`),
   kill the process using `.pipeline/dev-server.pid` and remove the PID file.

5. **Write** `test-results/e2e-pipeline.json`:
   ```json
   {
     "skill": "e2e-visual-run",
     "timestamp": "<ISO-8601>",
     "result": "PASSED|NEEDS_REVIEW|FAILED",
     "run_id": "<run_id>",
     "framework": "playwright",
     "summary": {
       "total": 42, "passed": 38, "failed": 0,
       "healed": 3, "expected_changes": 0, "known_issues": 1, "skipped": 0
     },
     "global_retries_used": 5,
     "global_retries_remaining": 10,
     "duration_ms": 180000,
     "failures": [],
     "known_issues": [],
     "expected_changes": [],
     "first_run_artifacts": {
       "config_edits": [],
       "fixture_created": null,
       "baselines_generated": []
     },
     "warnings": []
   }
   ```
   `first_run_artifacts` lists uncommitted changes the skill made to the
   project (config edits, fixture, baselines) so the user can review and
   commit them intentionally.

6. **Present summary:**
   ```
   E2E Pipeline: PASSED | NEEDS_REVIEW | FAILED
     Framework: playwright (auto-detected)
     Tests: 42 total | 38 passed | 3 healed | 1 known issue
     Duration: 3m 0s
     Retries: 5/15 used
     Evidence: test-evidence/{run_id}/

     Known Issues:
       test_animation (TIMING, confidence: 0.72) — after 3 attempts

     Expected Changes (if any):
       Run `/e2e-visual-run --update-baselines` to approve visual changes
   ```

7. **Git checkpoint** — if any tests were healed, commit the test fixes with
   discipline:

   **Pre-commit guards** (ALL must pass or skip the commit and report the fixes
   as uncommitted):
   - Run `git status --porcelain` first. If the working tree has modifications
     outside the healed test files and `{test_dir}/`, do NOT auto-commit —
     report "healed N tests but working tree has unrelated changes; fixes left
     staged for manual review" and stage only the healed test files.
   - Check current branch: if on `main` or `master`, do NOT commit — heal
     fixes must land on a feature branch per `git-collaboration.md`.
   - Stage explicit files only (healed test file paths from `fix_queue`
     history), never `git add -A` or `git add .`.

   **Commit message** (conventional commits):
   ```
   fix(e2e): heal N test failures (SELECTOR: X, TIMING: Y, DATA: Z)
   ```

   **First-run artifacts are NOT auto-committed:** config edits from Step 0.6,
   the evidence fixture from Step 1.5, and newly-generated `__snapshots__/`
   baselines remain uncommitted. Step 6 lists them in the report so the user
   can review and commit them intentionally.

## CRITICAL RULES

- NEVER skip Step 0 (environment discovery) — autonomous execution depends on framework detection
- NEVER skip pre-flight checks — environment issues masquerade as test failures
- ALWAYS capture screenshots for EVERY test (pass and fail); NEVER treat exit code as authoritative for UI tests — the dual-signal verdict (accessibility + screenshot) is the source of truth
- NEVER auto-fix LOGIC_BUG or VISUAL_REGRESSION — flag for human review via pre-classification gate
- NEVER auto-apply a fix with LOW confidence — suggest it but do not modify code
- NEVER apply the same fix twice — track history, try different approaches each attempt
- NEVER exceed global retry budget (default 15) — stop healing and report
- NEVER modify application source code for SELECTOR/TIMING/DATA fixes — only test code
- NEVER skip accessibility tree capture for passing tests — dual-signal needs it always
- NEVER batch-write results — update state file after EACH test for progress visibility
- ALWAYS read `.claude/config/e2e-pipeline.yml` for settings — fall back to defaults if missing
- ALWAYS tear down dev server in Step 6 if Step 0 started it — prevent orphaned processes
- ALWAYS disable CSS animations and apply mask selectors before screenshot capture
