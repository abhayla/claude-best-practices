---
name: e2e-best-practices
description: >
  Apply cross-framework E2E testing best practices for selector strategy, test data
  isolation, CI pipeline tiering, mock decisions, auth patterns, and parallel execution.
  Use when writing, reviewing, or modifying end-to-end tests in any framework.
  MUST consult before writing E2E tests — selectors, data isolation, and wait strategy
  are the top three causes of flaky E2E suites.
type: reference
allowed-tools: "Read Grep Glob"
argument-hint: "<topic: selectors|data|ci|mocks|auth|parallel|all>"
version: "1.0.0"
triggers:
  - e2e best practices
  - e2e patterns
  - e2e test writing
  - end-to-end best practices
---

# E2E Best Practices Reference

Cross-framework E2E testing patterns that complement framework-specific skills
(`/playwright`, `/flutter-e2e-test`, `/react-native-e2e`, `/android-run-e2e`).
This reference covers the universal principles — apply them regardless of framework.

**Read:** `references/anti-patterns.md` for the full cross-framework anti-patterns checklist.
**Read:** `references/edge-cases.md` for platform and environment edge cases.

**Request:** $ARGUMENTS

---

## CI Pipeline Tiering

Never put the full E2E suite on the PR gate — it kills developer velocity.
Tier your E2E execution by trigger event:

| Trigger | What to Run | Time Budget | Purpose |
|---------|-------------|-------------|---------|
| PR opened/updated | Smoke suite (5-10 critical user journeys) | < 10 min | Fast feedback on breaking changes |
| Merge to main | Full E2E suite (sharded across workers) | < 15 min | Comprehensive regression check |
| Nightly schedule | Full + visual regression + performance | < 30 min | Catch slow-burn regressions |

### Smoke Suite Selection Criteria

Include tests that cover:
- Authentication flow (login/logout)
- Primary revenue path (checkout, subscription, core feature)
- Cross-cutting navigation (can users reach key pages?)
- Most recent regression (the flow that broke last)

Exclude from smoke: edge cases, admin flows, rarely-used features.

### Sharding for Full Suite

Distribute tests across parallel CI runners to stay under the 15-minute budget:

```yaml
# GitHub Actions matrix sharding example
strategy:
  matrix:
    shard: [1, 2, 3, 4]
steps:
  - run: npx playwright test --shard=${{ matrix.shard }}/4
  # Or: pytest --splits=4 --group=${{ matrix.shard }}
  # Or: flutter test integration_test/ --shard-index=${{ matrix.shard }} --total-shards=4
```

Each shard MUST be independently executable — no ordering dependencies between shards.

### Nightly-Only Tests

Reserve for nightly: visual regression baselines, Lighthouse/performance budgets,
cross-browser matrix (Firefox, Safari), and mobile device emulation.

---

## E2E Test Data Isolation

Test data strategy determines whether E2E tests are reliable or perpetually flaky.

### Data Seeding Decision Framework

| Method | Speed | Reliability | Use When |
|--------|-------|-------------|----------|
| API-driven seeding | Fast | High | Default choice — validates creation path, realistic data |
| Direct database insert | Fastest | Medium | Performance-critical setup, large datasets |
| UI-driven creation | Slow | Low | Only when testing the creation flow itself |

API-driven seeding is the default. Create test data via the application's own API
before each test, not via raw SQL or UI clicks.

### Isolation Rules

1. **UUID-based unique data** — Every test generates unique identifiers:
   `user_${crypto.randomUUID()}@test.com`, never `test@example.com`
2. **No shared test accounts** — Parallel workers using the same account cause
   race conditions (one test logs out while another is mid-flow)
3. **No hardcoded primary keys** — Assert on content, not IDs:
   `expect(name).toBe('Alice')`, not `expect(id).toBe(42)`
4. **Explicit teardown** — Each test cleans up what it creates. With
   Testcontainers, container destruction handles this automatically
5. **No "golden dataset"** assumptions — Tests that assume pre-existing data
   break when the dataset drifts. Seed what you need, every time

**Read:** `/test-data-management` for factory patterns, Faker usage, and builder
implementations across Python and TypeScript.

---

## Mock Decision Framework for E2E

E2E tests exist to verify real integration. Over-mocking defeats the purpose.

| Service Type | E2E Decision | Reasoning |
|-------------|--------------|-----------|
| External paid APIs (Stripe, Twilio, SendGrid) | **Mock** | Cost, rate limits, flakiness, sandbox limitations |
| External free APIs (geocoding, weather) | **Mock in CI, real in staging** | Free but unreliable in CI (network, rate limits) |
| Internal services you own | **Real** | The whole point of E2E is testing real integration |
| Database | **Real** (Testcontainers or dedicated test DB) | Mocking DB masks SQL bugs, constraint violations |
| Auth provider (OAuth/SSO) | **Mock tokens in CI, real in staging** | OAuth flows require browser redirects that are fragile in CI |
| File storage (S3, GCS) | **Local emulator** (MinIO, fake-gcs) | Real cloud storage adds latency and cost |
| Email/SMS | **Mock** (MailHog, mock SMTP) | Never send real emails/SMS from tests |

### When Mocking Undermines Confidence

If a mock passes but the real service would fail, the E2E test provides false
confidence. Signs of over-mocking:
- More than 50% of service calls are mocked in E2E
- Mocks return hardcoded success responses without error scenarios
- Nobody runs E2E against real services in any environment

Use framework-native mocking for network interception (Playwright `page.route()`,
Detox mocks, Flutter `HttpOverrides`) — these intercept at the network layer
without modifying application code.

---

## Cross-Framework Selector Philosophy

Every E2E framework has its own locator API, but the underlying principle is
universal: **select elements the way a user identifies them, not the way a
developer implemented them.**

### The Intent Hierarchy

| Priority | Selector Type | Survives | Example Concept |
|----------|--------------|----------|-----------------|
| 1 | Accessibility role + name | Refactors, redesigns | "the Submit button" |
| 2 | Label / visible text | Most refactors | "the Email field" |
| 3 | Explicit test ID | All refactors | `data-testid="checkout-btn"` |
| 4 | CSS class / type | Nothing | `.btn-primary`, `ElevatedButton` |

### Framework Equivalents

| Priority | Playwright | Flutter | Detox | Maestro |
|----------|-----------|---------|-------|---------|
| 1 (Role) | `getByRole('button', {name})` | `bySemanticsLabel('Submit')` | `by.label('Submit')` | `tapOn: "Submit"` |
| 2 (Label) | `getByLabel('Email')` | `bySemanticsLabel('Email')` | `by.label('Email')` | `tapOn: "Email"` |
| 3 (TestID) | `getByTestId('checkout')` | `byKey(Key('checkout'))` | `by.id('checkout')` | `tapOn: {id: "checkout"}` |
| 4 (CSS/Type) | `locator('.btn')` | `byType(ElevatedButton)` | `by.type('RCTTextInput')` | N/A |

### When to Add `data-testid` to Source Code

Add test IDs only when semantic selectors are insufficient:
- Dynamic content with no stable accessible name
- Multiple identical elements (e.g., list of "Delete" buttons)
- Third-party components that don't expose accessibility attributes
- Elements with text that changes by locale (i18n)

MUST NOT add `data-testid` to every element — it clutters markup and creates
a parallel naming system that drifts from the real UI.

### Selector Maintenance

When a test breaks due to a selector change:
1. First, try a more resilient selector (role > label > testid)
2. If the UI genuinely changed, update the selector — don't add a second
   selector "just in case"
3. Never fall back to XPath in production tests — XPath selectors break on
   any structural change

---

## E2E Test Isolation & Parallel Execution

Parallel execution cuts CI time but requires strict isolation between workers.

### Per-Worker Isolation Checklist

| Resource | Isolation Strategy |
|----------|-------------------|
| Browser context | Fresh context per test (default in Playwright, Detox) |
| Auth state | Read-only shared state (Playwright `storageState`, Detox launch args) |
| Database | Per-worker schema/DB or UUID-prefixed data |
| Ports | Dynamic port allocation or env-variable ports — never hardcoded |
| File system | Per-worker temp directories (`tmp_path`, `os.tmpdir()`) |
| Cookies / localStorage | Cleared between tests (framework default or explicit cleanup) |

### Auth State Sharing

Login once in global setup, save the auth state, reuse across all tests as
**read-only**. This avoids logging in via UI for every test (slow, flaky).

Pattern: global setup logs in → saves cookies/tokens to file → each test loads
the saved state. The auth file is read-only during tests — no test should modify it.

### Fixture Encapsulation

Use test framework fixtures to encapsulate setup/teardown instead of global
`beforeEach`/`afterEach`. Fixtures are composable, type-safe, and self-cleaning:

```
# Pseudocode — applies to any framework
define fixture "authenticated_page":
  1. Create fresh browser context
  2. Load saved auth state
  3. Yield page to test
  4. Cleanup: close context (automatic)

define fixture "seeded_product":
  1. Create product via API (UUID name)
  2. Yield product data to test
  3. Cleanup: delete product via API
```

Fixtures compose: a test that needs both requests `authenticated_page` and
`seeded_product`. Each fixture manages its own lifecycle.

### Sharding Safety

When sharding across CI workers (`--shard=1/4`):
- Each shard MUST be independently runnable (no shared state between shards)
- Use `fullyParallel: true` (Playwright) only when ALL tests are truly isolated
- If any test has ordering dependencies, keep it in a serial group

---

## Environment Strategy

### Where E2E Tests Run

| Environment | What to Test | How to Set Up |
|-------------|-------------|---------------|
| Local development | Single test / debugging | Docker Compose with seeding script |
| PR preview (ephemeral) | Smoke suite | Auto-deployed per PR (Bunnyshell, Railway, Vercel Preview) |
| Staging | Full suite + visual regression | Mirrors production config |
| Production | Synthetic monitoring only | Read-only health checks, never write operations |

### Local E2E Setup

Provide a single command that starts everything needed for E2E:
```bash
# Example: start app + dependencies + seed data
docker compose -f docker-compose.test.yml up -d
# Or: framework-native dev server auto-start via config
```

### Environment Parity

Staging MUST mirror production configuration, not just code. Common parity failures:
- Different database engine (SQLite in test vs PostgreSQL in prod)
- Missing environment variables (feature flags, API keys)
- Different auth provider config (mock vs real OAuth)
- Missing CDN/proxy layer that affects CORS behavior

---

## E2E Auth Patterns

Authentication is the most common source of E2E test brittleness.

### Login-Once, Reuse State

| Approach | Speed | Reliability | Use When |
|----------|-------|-------------|----------|
| UI login every test | Slow | Low | Only when testing the login flow itself |
| Saved auth state (cookies/tokens) | Fast | High | Default for all non-auth tests |
| API-generated token | Fastest | Highest | When the app supports token-based auth |

### Multi-User Scenarios

For tests where user A interacts with user B's data:
1. Create both users via API (UUID-based, unique per test run)
2. Authenticate both in separate browser contexts
3. User A creates shared resource → User B verifies access
4. Teardown: delete both users and shared resources

### Role-Based Access Testing

Test each role's permissions in E2E, not just the happy path:

| Role | Test | Expected |
|------|------|----------|
| Admin | Access admin panel | 200, panel visible |
| Regular user | Access admin panel | Redirect to home or 403 |
| Unauthenticated | Access protected page | Redirect to login |

### Token Refresh in Long E2E Runs

If auth tokens expire during a test suite (common with 30+ minute nightly runs):
- Use long-lived test tokens (set token expiry to 24h in test environment)
- Or implement token refresh in the test fixture (refresh before each test)
- Never hardcode tokens in test files — load from environment or fixture

### OAuth/SSO in CI

Real OAuth flows require browser redirects that are fragile in CI. Options:
1. **Mock the OAuth provider** — Return a valid token without the redirect flow
2. **Use test-specific auth bypass** — A `/test/login` endpoint that accepts
   a secret header and returns a session (disabled in production)
3. **Pre-authenticated session** — Create session via API, inject cookies

---

## When NOT to E2E

E2E tests are expensive (slow, flaky, hard to maintain). Use them only for
flows that cannot be adequately tested at lower levels.

### Decision Framework

| What You're Testing | Best Test Level | Why |
|--------------------|----------------|-----|
| Business logic (calculations, rules) | Unit test | Fast, isolated, deterministic |
| Component rendering and interaction | Component test (Playwright CT, Storybook) | Real browser, isolated component |
| API request/response | Integration test | Tests real service boundary |
| Database queries and constraints | Integration test (Testcontainers) | Real DB, no mock drift |
| Full user journey (login → checkout → confirmation) | **E2E test** | Only E2E captures cross-page flows |
| Visual appearance of a single component | Visual snapshot (Storybook, golden test) | Cheaper than full E2E visual |
| Cross-service data flow | **E2E test** | Only E2E tests the real integration |

### Pyramid Health Check

If your test suite has more E2E tests than unit tests, the pyramid is inverted.
Symptoms:
- CI takes 30+ minutes
- Flaky test rate exceeds 5%
- Developers skip tests locally because they're too slow

Fix: push coverage down. For each E2E test, ask: "Could a unit or integration
test cover this with equal confidence?" If yes, replace it.

### Component Testing as E2E Alternative

Component tests render real components in a real browser — without loading the
full application. They fill the gap between unit tests and E2E:
- Faster than E2E (no navigation, no server, no database)
- More realistic than unit tests (real DOM, real browser APIs)
- Ideal for: form validation, conditional rendering, interactive widgets

---

## Message Queue E2E Testing

When E2E flows involve asynchronous message processing (Kafka, RabbitMQ, SQS),
standard synchronous assertions fail.

### Polling Assertions

Replace `sleep()` with a polling function that checks a condition with a timeout:

```
# Pseudocode — any language
function wait_for(condition_fn, timeout=10s, interval=500ms):
    deadline = now() + timeout
    while now() < deadline:
        if condition_fn() is true:
            return success
        wait(interval)
    raise "Condition not met within timeout"

# Usage: wait for order status to update after message processing
wait_for(() => get_order_status(order_id) == "CONFIRMED")
```

### Message Isolation for Parallel Tests

| Broker | Isolation Strategy |
|--------|-------------------|
| Kafka | Unique consumer group ID per test run (`test-group-${runId}`) |
| RabbitMQ | Temporary exclusive queue per test, bound to the exchange |
| SQS | Unique queue name per test run or use FIFO message group IDs |

### Dead Letter Queue Monitoring

Assert that no messages land in DLQ during normal operations:

```
# After test flow completes:
assert dlq_message_count(queue_name) == 0,
    "Messages in DLQ indicate unhandled processing failures"
```

**Read:** `/integration-test` for unit-level queue testing patterns with
Testcontainers (RabbitMQ, Kafka).

---

## Web-First Assertions & Wait Strategy

The #1 cause of flaky E2E tests is improper waiting. Every framework provides
auto-wait mechanisms — use them instead of fixed delays.

### Framework Auto-Wait Equivalents

| Framework | Auto-Wait Assertion | Explicit Wait | NEVER Use |
|-----------|-------------------|---------------|-----------|
| Playwright | `expect(locator).toBeVisible()` | `page.waitForResponse()` | `page.waitForTimeout()` |
| Flutter | `tester.pumpAndSettle()` | `pump(Duration(...))` | `Future.delayed()` |
| Detox | `waitFor(el).toBeVisible()` | `.withTimeout(5000)` | `sleep()` |
| Cypress | `cy.get().should('be.visible')` | `cy.intercept().wait()` | `cy.wait(5000)` |
| Maestro | Implicit (auto-waits) | `waitForAnimationToEnd` | N/A |

### Wait Strategy Decision Tree

1. **Element visibility?** → Use auto-wait assertion (`toBeVisible()`, `pumpAndSettle()`)
2. **API response needed?** → Wait for specific response (`waitForResponse('/api/data')`)
3. **Animation completing?** → Wait for animation end or disable animations in test config
4. **State transition?** → Poll for condition with timeout (see Message Queue section)
5. **Nothing else works?** → You likely have a test design problem, not a timing problem

### Content Assertions Beyond Visual

Screenshots catch visual bugs but miss data correctness. Pair every visual
check with content assertions:

| Check | What It Catches |
|-------|----------------|
| Element visible | Layout rendering |
| Text content present | Data loaded (not empty state) |
| No error messages visible | No server errors or validation failures |
| Correct count of items | Data completeness (not truncated) |
| No placeholder text visible | Data replaced loading states |

---

## MUST DO

- Use auto-wait assertions — every framework provides them
- Seed test data via API with UUID-unique values per test
- Select elements by accessibility role/label before falling back to test IDs
- Shard E2E suites across CI workers when suite exceeds 10 minutes
- Login once and reuse auth state for non-auth tests
- Pair visual checks with content assertions
- Clean up test data explicitly (or use container-based isolation)
- Keep the E2E smoke suite under 10 minutes on PR gates

## MUST NOT DO

- Use `sleep()`, `waitForTimeout()`, `Future.delayed()`, or any fixed delay
- Share mutable test accounts across parallel workers
- Put the full E2E suite on the PR gate
- Use CSS selectors or XPath before trying semantic/role-based selectors
- Mock internal services you own in E2E tests (defeats the purpose)
- Hardcode primary keys, ports, or URLs in test assertions
- Write E2E tests for logic that unit or integration tests can cover
- Skip teardown — leaked test data causes cascading failures in subsequent runs

**Read:** `references/anti-patterns.md` for the complete cross-framework anti-patterns checklist.
**Read:** `references/edge-cases.md` for platform-specific gotchas and mitigations.
