# E2E Anti-Patterns Checklist

Unified cross-framework anti-patterns. Each entry: what goes wrong, why it
fails, and what to do instead.

---

## Timing Anti-Patterns

### Fixed Delays (`sleep`, `waitForTimeout`, `Future.delayed`)

**Why it fails:** Fixed delays either wait too long (slow tests) or too short
(flaky tests). Network latency, CI runner speed, and server load all vary.

**Use instead:** Auto-wait assertions (`expect().toBeVisible()`,
`pumpAndSettle()`, `waitFor().toBeVisible()`). For API-dependent updates,
use `waitForResponse()` or polling with timeout.

### Arbitrary Timeout Increases

**Why it fails:** Bumping a timeout from 5s to 30s masks the real problem
(missing wait condition, slow query, race condition). The test becomes slow
AND still flaky under load.

**Use instead:** Identify what the test is actually waiting for. Add an
explicit wait for that specific condition. If the app is genuinely slow,
fix the app — don't stretch the test.

---

## Selector Anti-Patterns

### CSS/XPath as Primary Selectors

**Why it fails:** CSS classes change during styling refactors. XPath breaks
on any structural DOM change. Both couple tests to implementation details.

**Use instead:** Accessibility role selectors (`getByRole`, `bySemanticsLabel`),
then labels (`getByLabel`), then test IDs (`data-testid`). CSS/XPath only as
last resort for third-party components.

### Coordinate-Based Taps (`tapAt(Offset(150, 300))`)

**Why it fails:** Screen resolution, font size, device density, and platform
chrome all shift coordinates. Tests pass on one device, fail on another.

**Use instead:** Semantic finders (`find.byKey()`, `by.id()`, `getByRole()`).
If the element has no accessible identifier, add one to the source code.

### Over-Applying `data-testid`

**Why it fails:** Adding `data-testid` to every element creates a parallel
naming system that drifts from the UI. It clutters markup and discourages
accessible design.

**Use instead:** `data-testid` only when semantic selectors are insufficient
(dynamic content, duplicate elements, third-party components, i18n text).

---

## Data Anti-Patterns

### Shared Test Accounts (`test@example.com`)

**Why it fails:** Parallel workers using the same account cause race
conditions — one test logs out while another is mid-flow. State leaks
between tests (leftover cart items, changed settings).

**Use instead:** UUID-based unique accounts per test:
`user_${crypto.randomUUID()}@test.com`. Each test creates its own user.

### Hardcoded Primary Keys (`expect(id).toBe(42)`)

**Why it fails:** Auto-increment IDs differ between environments, test runs,
and database states. A test that passes locally fails in CI because the
seeded data has different IDs.

**Use instead:** Assert on content, not identifiers:
`expect(name).toBe('Alice')`, `expect(items).toHaveLength(3)`.

### Assuming Clean Database

**Why it fails:** Tests that don't seed their own data depend on some other
process having set up the "right" state. Database resets, migration changes,
or re-ordering tests break them.

**Use instead:** Every test seeds what it needs. Use API-driven seeding in
`beforeEach` or test fixtures. Assume nothing about pre-existing data.

### Unbounded "Golden Dataset"

**Why it fails:** A shared dataset grows over time, becomes stale, and nobody
knows which tests depend on which records. Changing any record risks breaking
unrelated tests.

**Use instead:** Per-test factory-generated data with explicit lifecycle.
No test should depend on data it didn't create.

---

## Scope Anti-Patterns

### Over-Scoped E2E Tests

**Why it fails:** Testing business logic (calculations, validation rules,
string formatting) through E2E is slow, flaky, and hard to debug. E2E tests
should verify integration, not logic.

**Use instead:** Unit tests for logic, integration tests for service
boundaries, E2E only for full user journeys that cross multiple pages/screens.

### Inverted Test Pyramid

**Why it fails:** More E2E tests than unit tests means CI takes 30+ minutes,
flaky test rate exceeds 5%, and developers skip tests locally. Maintenance
cost grows quadratically with E2E count.

**Use instead:** For each E2E test, ask: "Could a unit or integration test
cover this?" If yes, replace it. Target: ~70% unit, ~20% integration, ~10% E2E.

### Testing Implementation Details via E2E

**Why it fails:** E2E tests that verify internal state (database records, cache
entries, internal API calls) couple tests to implementation. Refactoring the
internals breaks tests even when user-facing behavior is unchanged.

**Use instead:** Assert on user-visible outcomes only: what the user sees on
screen, what response the API returns, what email the user receives.

---

## Auth Anti-Patterns

### Login via UI in Every Test

**Why it fails:** Logging in through the UI adds 3-10 seconds per test and
multiplies flakiness (login page rendering, form filling, redirect timing).
For a 50-test suite, that's 2.5-8 minutes wasted on login alone.

**Use instead:** Login once in global setup, save auth state (cookies/tokens)
to a file, reuse across all non-auth tests via `storageState` or equivalent.

### Hardcoded Credentials in Test Files

**Why it fails:** Credentials committed to source control are a security risk.
They also break when rotated or when running against different environments.

**Use instead:** Load from environment variables (`$TEST_USER_EMAIL`,
`$TEST_USER_PASSWORD`). In CI, inject via secrets management.

---

## CI Anti-Patterns

### Full E2E Suite on PR Gate

**Why it fails:** 15-30 minute test runs on every PR push destroy developer
velocity. Developers start ignoring CI results or pushing `[skip ci]`.

**Use instead:** PR gate runs smoke suite (5-10 critical paths, < 10 min).
Full suite runs on merge to main. Visual regression runs nightly.

### No Sharding

**Why it fails:** Running 200 E2E tests sequentially takes 30+ minutes.
Developers can't get feedback before context-switching to another task.

**Use instead:** Shard across parallel CI workers (`--shard=1/4`, GitHub
Actions matrix). Each shard runs independently. Target: < 15 min total.

### Using `[skip ci]` or `--no-verify`

**Why it fails:** Skipping CI to "just merge this quick fix" introduces
unverified code. The "quick fix" often breaks something else.

**Use instead:** Never skip CI gates. If tests are too slow, fix the suite
(shard, reduce scope, push coverage to unit level).

---

## Assertion Anti-Patterns

### Screenshot-Only Testing

**Why it fails:** Screenshots confirm visual appearance but miss data
correctness. An empty table with correct styling passes a screenshot check.
A page showing cached/stale data looks visually identical to fresh data.

**Use instead:** Pair screenshots with content assertions: element visible
AND text content present AND no error messages AND correct item count.

### Empty Assertions

**Why it fails:** A test with no `assert`/`expect`/`verify` always passes.
It tests nothing. Common in auto-generated test stubs that were never completed.

**Use instead:** Every test MUST contain at least one meaningful assertion.
Tests with only navigation steps and no assertions are bugs.

---

## Environment Anti-Patterns

### Hardcoded URLs and Ports

**Why it fails:** `http://localhost:3000` works on a developer's machine but
fails in CI where the app runs on a different port or hostname.

**Use instead:** Environment variables (`$BASE_URL`, `$API_URL`) or framework
config (`baseURL` in Playwright, `baseUrl` in Cypress).

### No Cleanup Between Test Runs

**Why it fails:** Leftover data from previous runs causes test pollution —
assertions fail because unexpected records exist, unique constraints block
inserts, or UI shows stale content.

**Use instead:** Explicit teardown per test (delete created records). Or use
container-based isolation (Testcontainers) where each run starts fresh.
