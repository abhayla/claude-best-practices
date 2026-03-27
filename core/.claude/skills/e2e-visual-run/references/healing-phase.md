# Healing Phase: Classification-Driven Test Repair

Detailed guidance for STEP 5 of the e2e-visual-run skill.

## Classification Decision Tree

```
Test failed
  │
  ├─ Element not found? ──────────────→ SELECTOR
  │    (NoSuchElement, locator timeout,
  │     "element not attached to DOM")
  │
  ├─ Timeout / slow response? ────────→ TIMING
  │    (TimeoutError, waitFor exceeded,
  │     "waiting for selector")
  │
  ├─ Data mismatch? ──────────────────→ DATA
  │    (assertion: expected "John" got "",
  │     empty table, missing fixtures)
  │
  ├─ Passes alone, fails in suite? ───→ TEST_POLLUTION
  │    (shared state, DB not reset,
  │     global variable leak)
  │
  ├─ Passes sometimes, fails others? ─→ FLAKY_TEST
  │    (random timing, network jitter,
  │     animation race condition)
  │
  ├─ Server down / DB unreachable? ───→ INFRASTRUCTURE
  │    (ECONNREFUSED, 503, "no such table")
  │
  ├─ Screenshot looks wrong but ──────→ VISUAL_REGRESSION
  │   exit code passed?
  │    (layout shifted, color changed,
  │     element misplaced)
  │
  └─ Application returns wrong ───────→ LOGIC_BUG
     data / wrong behavior?
      (API returns 422, business rule
       violated, calculation wrong)
```

## Confidence Heuristics (Pre-Classification)

These guide the pre-classification routing step in STEP 5. The authoritative
confidence comes from fix-loop's `test-failure-analyzer-agent` — these heuristics
are for routing decisions only (e.g., skip fix-loop for VISUAL_REGRESSION).

| Error Pattern | Pre-Classification | Pre-Confidence | Notes |
|--------------|-------------------|----------------|-------|
| Exact: "NoSuchElementException", "locator timeout" | SELECTOR | HIGH | Clear element-not-found signal |
| Exact: "TimeoutError", "waitFor exceeded" | TIMING | HIGH | Unambiguous timeout |
| Contains "expected" + "got" or "assert" | DATA | MEDIUM | Could be data or logic bug |
| Passes alone, fails in suite | TEST_POLLUTION | MEDIUM | Needs isolation test to confirm |
| Intermittent across retries | FLAKY_TEST | LOW | Needs evidence from multiple runs |
| "ECONNREFUSED", "503", "no such table" | INFRASTRUCTURE | HIGH | Environment issue |
| Screenshot differs but exit code PASS | VISUAL_REGRESSION | HIGH | Route to human review |
| API returns wrong data, business rule violated | LOGIC_BUG | HIGH | Route to human review |
| No clear pattern match | UNKNOWN | LOW | Escalate to user |

**Routing rules:**
- VISUAL_REGRESSION or LOGIC_BUG → skip fix-loop, move to `known_issues`
- UNKNOWN with LOW confidence → escalate to user, do not attempt fix
- All others → proceed to fix-loop for authoritative classification + fix

## Fix Strategies Per Classification

### SELECTOR (Auto-Fix)

**Root cause:** UI element moved, renamed, or restructured.

**Fix approach:**
1. Check `.pipeline/test-history.json` for previously successful locators for this
   test — if found, try them first before regenerating
2. Read the a11y tree snapshot to find the element by role/label
3. Generate 2–3 alternative locators ranked by resilience:
   - Primary: `getByRole('button', { name: 'Submit' })` (most resilient)
   - Fallback 1: `getByLabel('Submit')` or `getByText('Submit')`
   - Fallback 2: `[data-testid='submit-btn']` (if present in DOM)
4. Apply the highest-resilience locator that matches the current DOM
5. Record all generated locators in `test-history.json` under `known_locators`
   for this test — on future SELECTOR failures, these are tried first (step 1)
6. If element genuinely removed, the test needs updating (not just the selector)

**Anti-pattern:** Never replace one brittle selector with another brittle selector.

### TIMING (Auto-Fix)

**Root cause:** Element not ready when test interacts with it.

**Fix approach:**
1. Replace `sleep()` / fixed delays with event-driven waits:
   - `await expect(element).toBeVisible()` before clicking
   - `await page.waitForLoadState('networkidle')` after navigation
   - `await expect(table).toHaveCount(n)` before asserting rows
2. Add `{ timeout: 10000 }` to specific slow operations, not globally
3. For animations: wait for `transitionend` or check `aria-busy`

**Anti-pattern:** Never increase global timeout — fix the specific wait.

### DATA (Auto-Fix)

**Root cause:** Test data missing, stale, or wrong format.

**Fix approach:**
1. Check fixture/seed files — is the expected data actually seeded?
2. Check teardown — is previous test's data leaking or being cleaned too aggressively?
3. Add explicit data setup in `beforeEach` if relying on implicit state
4. Use factories/builders for test data, not hardcoded values

### FLAKY_TEST (Auto-Fix)

**Root cause:** Non-deterministic behavior in test or app.

**Fix approach:**
1. Identify the flakiness source:
   - Timing → add explicit waits (see TIMING)
   - Shared state → isolate with `beforeEach` reset (see TEST_POLLUTION)
   - Network → mock external API calls
   - Animation → disable animations in test config or wait for completion
2. Run the test 3x in isolation to confirm the fix eliminates flakiness

### INFRASTRUCTURE (Auto-Fix — Environment Only)

**Root cause:** Test environment not properly set up.

**Fix approach:**
1. Check if dev server is running, restart if needed
2. Check if database is accessible, run migrations if needed
3. Check environment variables are set
4. Retry the test after environment fix

**Escalation:** If infrastructure issue persists after 1 retry, escalate to user.

### TEST_POLLUTION (Auto-Fix)

**Root cause:** Tests share mutable state.

**Fix approach:**
1. Add state reset in `beforeEach`:
   - Browser: new context per test (`browser.newContext()`)
   - Database: transaction rollback or re-seed
   - Global variables: reset to defaults
2. Check for `beforeAll` / session-scoped fixtures with mutable state — convert to `beforeEach`
3. Run the failing test in isolation to confirm it passes alone

### VISUAL_REGRESSION (Human Review)

**Root cause:** UI changed — intentionally or not.

**Do NOT auto-fix.** Instead:
1. Capture before/after screenshots
2. Highlight the visual difference
3. Present to user: "Intentional change? Update baseline. Bug? Fix the component."
4. Log as known issue with screenshots attached

### LOGIC_BUG (Human Review)

**Root cause:** Application code is wrong, not the test.

**Do NOT auto-fix.** Instead:
1. Log the full error with:
   - API response (if applicable)
   - Expected vs actual values
   - Stack trace
   - Affected component/endpoint
2. Suggest the likely fix location
3. Flag for human review

## Known Issue Log Format

When a test exhausts its attempt cap:

```json
{
  "test": "test_name",
  "file": "<test-file-path>",
  "attempts": 3,
  "final_classification": "TIMING",
  "history": [
    {"attempt": 1, "classification": "SELECTOR", "fix": "updated to getByRole", "result": "FAILED"},
    {"attempt": 2, "classification": "TIMING", "fix": "added waitFor", "result": "FAILED"},
    {"attempt": 3, "classification": "TIMING", "fix": "increased timeout to 10s", "result": "FAILED"}
  ],
  "root_cause": "Animation causes element to be non-interactive for ~2s after load",
  "recommended_action": "Investigate CSS animation on component — may need animation-complete event"
}
```

## Global Retry Budget

The budget prevents runaway healing across large test suites:

- **Default:** 15 total retries across all tests
- **Per-test cap:** 3 attempts (from config)
- **Budget tracking:** increment `global_retries_used` after each healing attempt
- **Exhaustion:** when budget hits 0, STOP healing all remaining fix_queue items,
  move them to known_issues, and proceed to Step 6 (aggregation)

A suite with 100 tests and 10 failures: worst case 10 × 3 = 30 attempts needed,
but budget caps at 15 — forcing prioritization of the most fixable failures first.
