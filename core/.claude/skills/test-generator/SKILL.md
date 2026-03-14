---
name: test-generator
description: >
  Auto-generate test suites from PRD requirements, schema, or API specs.
  Produces shared test infrastructure (conftest.py/setupTests.ts), unit, API,
  E2E stubs (skipped with Page Objects), BDD/Gherkin, property-based, snapshot tests,
  coverage thresholds, mutation testing setup, red phase gate verification, and
  structured JSON output for stage gate validation. Use before implementation (TDD red phase).
triggers:
  - generate tests
  - test stubs
  - test generation
  - pre-implementation tests
  - write tests from requirements
  - test matrix
allowed-tools: "Bash Read Write Edit Grep Glob Agent"
argument-hint: "<PRD file path, plan file path, schema file path, or feature description>"
---

# Test Generator — Requirements-Driven Test Suite Generation

Auto-generate comprehensive test suites from PRD requirements, schema definitions, or API specs. Produces failing tests (TDD red phase) ready for implementation.

**Input:** $ARGUMENTS

---

## STEP 1: Parse Sources

Read and extract testable requirements from available sources:

1. **PRD** — User stories (US-xxx), acceptance criteria (AC-xxx), NFRs (NFR-xxx)
2. **Plan** — Task verification commands, file paths, expected behavior
3. **Schema** — Entity definitions, constraints, relationships, seed data
4. **API spec** — Endpoints, request/response shapes, error codes, auth requirements

Build the test matrix:

```markdown
## Test Matrix

| Requirement | Test Type | Test ID | Description | Status |
|-------------|-----------|---------|-------------|--------|
| AC-001 | Unit | UT-001 | Validate email format | RED |
| AC-002 | API | AT-001 | POST /users returns 201 | RED |
| AC-003 | E2E | ET-001 | User can sign up | STUB |
| NFR-002 | Perf | PT-001 | p95 < 200ms under 100rps | STUB |
| NFR-006 | Security | ST-001 | Auth required on /users/me | RED |
```

Every AC and NFR MUST map to at least one test. If a requirement has no corresponding test, flag it.

Wait for confirmation of the test matrix before generating test files.

---

## STEP 2: Detect Test Framework

Auto-detect the project's test framework by scanning for config files:

| Indicator | Framework | Language |
|-----------|-----------|----------|
| `pyproject.toml` with `[tool.pytest]` | pytest | Python |
| `conftest.py` | pytest | Python |
| `jest.config.*` | Jest | JavaScript/TypeScript |
| `vitest.config.*` | Vitest | TypeScript |
| `*.test.ts` pattern | Jest or Vitest | TypeScript |
| `build.gradle.kts` with `testImplementation` | JUnit 5 | Kotlin/Android |
| `playwright.config.*` | Playwright | E2E |
| `k6` scripts in `tests/perf/` | k6 | Performance |

If no framework detected, recommend one based on the stack and set it up.

---

## STEP 3: Generate Shared Test Infrastructure

Before generating test files, create the shared fixtures/setup file that wires factories and fixtures to the test framework.

### 3.0 conftest.py / setupTests Generation

**Python (conftest.py):**
```python
# tests/conftest.py

import pytest
from tests.factories import *  # noqa: F401,F403 — export all factories as fixtures

@pytest.fixture(autouse=True)
def _db_transaction(db_session):
    """Wrap each test in a transaction and roll back after."""
    yield
    db_session.rollback()

@pytest.fixture
def client(app):
    """Async test client for API tests."""
    from httpx import AsyncClient, ASGITransport
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")
```

**JavaScript (setupTests.ts):**
```typescript
// tests/setupTests.ts

import { beforeEach, afterEach } from "vitest";
import { resetDatabase } from "./helpers/db";

beforeEach(async () => {
  await resetDatabase();
});

afterEach(() => {
  vi.restoreAllMocks();
});
```

Adapt imports and fixtures to the project's actual app factory, database session, and ORM. If Stage 5 produced factory functions, import them here.

---

## STEP 4: Generate Unit Tests

For each domain entity and use case, generate test stubs:

### 4.1 Test Structure

```python
# tests/unit/test_<entity>.py (Python/pytest example)

import pytest
from src.domain.<entity> import <Entity>

class TestCreate<Entity>:
    """Tests for AC-001: <acceptance criterion description>"""

    def test_valid_creation(self):
        """Given valid input, when creating <entity>, then succeeds."""
        # Arrange
        data = {"field": "value"}

        # Act
        result = Entity.create(**data)

        # Assert
        assert result.field == "value"

    def test_rejects_invalid_email(self):
        """Given invalid email, when creating user, then raises ValueError."""
        with pytest.raises(ValueError, match="Invalid email"):
            Entity.create(email="not-an-email")

    def test_rejects_empty_required_field(self):
        """Given empty name, when creating user, then raises ValueError."""
        with pytest.raises(ValueError, match="name is required"):
            Entity.create(name="")
```

### 4.2 Edge Cases to Generate

For each entity, auto-generate tests for:
- **Empty/null inputs** — Every required field with empty/null value
- **Boundary values** — Max length strings, min/max numbers, date boundaries
- **Invalid types** — Wrong type for each field
- **Duplicate handling** — Unique constraint violations
- **Relationship integrity** — FK references that don't exist

### 4.3 Test Data Factories

Generate factory functions for test data:

```python
# tests/factories.py

def make_user(**overrides):
    """Factory for User test data with sensible defaults."""
    defaults = {
        "email": "test@example.com",
        "name": "Test User",
        "status": "active",
    }
    defaults.update(overrides)
    return defaults
```

---

## STEP 5: Generate API Tests

For each API endpoint extracted from PRD or API spec:

```python
# tests/api/test_<resource>.py

import pytest
from httpx import AsyncClient

class TestCreate<Resource>:
    """Tests for AC-002: POST /<resource> creates a new <resource>."""

    async def test_creates_with_valid_data(self, client: AsyncClient):
        """Given valid payload, when POST /<resource>, then returns 201."""
        response = await client.post("/<resource>", json=make_<resource>())
        assert response.status_code == 201
        assert "id" in response.json()

    async def test_rejects_missing_required_fields(self, client: AsyncClient):
        """Given missing name, when POST /<resource>, then returns 422."""
        response = await client.post("/<resource>", json={})
        assert response.status_code == 422

    async def test_rejects_duplicate(self, client: AsyncClient):
        """Given existing email, when POST /users, then returns 409."""
        await client.post("/users", json=make_user())
        response = await client.post("/users", json=make_user())
        assert response.status_code == 409

    async def test_requires_auth(self, client: AsyncClient):
        """Given no auth token, when POST /<resource>, then returns 401."""
        response = await client.post("/<resource>", json=make_<resource>(),
                                      headers={})  # No auth
        assert response.status_code == 401
```

Generate tests for all CRUD operations + auth + error cases per endpoint.

---

## STEP 6: Generate E2E Test Stubs

Generate E2E test stubs using the Page Object Model pattern from the `playwright` skill. E2E tests at this stage are **skipped stubs** — they define test intent but do NOT contain assertions. Stage 8 fills in assertions and runs them against working code.

### 6.1 Stub Format

E2E stubs MUST follow this exact format:

**Python (pytest + Playwright):**
```python
# tests/e2e/test_<flow>.py

import pytest
from tests.e2e.pages.<page> import <Page>

@pytest.mark.skip(reason="E2E stub — fill in at Stage 8")
class TestUserRegistrationFlow:
    """E2E: AC-001 — User can register and receive confirmation."""

    def test_successful_registration(self, page):
        """Given new user, when completing registration, then sees welcome page."""
        # Page Objects are fully defined — test body is a stub
        # TODO: Add navigation + assertions in Stage 8
        pass

    def test_duplicate_email_shows_error(self, page):
        """Given existing user, when registering same email, then sees error."""
        # TODO: Add navigation + assertions in Stage 8
        pass
```

**JavaScript (Playwright Test):**
```typescript
// tests/e2e/user-registration.spec.ts

import { test } from "@playwright/test";

test.describe("User Registration Flow", () => {
  test.skip("successful registration", async ({ page }) => {
    // AC-001: User can register and receive confirmation
    // TODO: Add navigation + assertions in Stage 8
  });

  test.skip("duplicate email shows error", async ({ page }) => {
    // AC-002: Duplicate email rejection
    // TODO: Add navigation + assertions in Stage 8
  });
});
```

### 6.2 Page Object Classes (Fully Defined)

Page Objects are NOT stubs — define them completely so Stage 8 only needs to write test logic:

```python
# tests/e2e/pages/registration_page.py

class RegistrationPage:
    def __init__(self, page):
        self.page = page
        self.email_input = page.locator("[data-testid='email-input']")
        self.password_input = page.locator("[data-testid='password-input']")
        self.submit_button = page.locator("[data-testid='register-button']")
        self.error_message = page.locator("[data-testid='error-message']")

    async def goto(self):
        await self.page.goto("/register")

    async def register(self, email: str, password: str):
        await self.email_input.fill(email)
        await self.password_input.fill(password)
        await self.submit_button.click()
```

### 6.3 Rules

- Test functions use `@pytest.mark.skip` (Python) or `test.skip()` (JS) — NOT empty bodies without skip markers
- Each skip includes `reason="E2E stub — fill in at Stage 8"`
- Page Object classes are fully defined with locators and actions
- One test file per user flow, one Page Object per page/screen
- Test IDs in the test matrix use status `STUB` (not `RED`) for E2E tests

---

## STEP 7: Generate BDD Scenarios

For stakeholder-readable specs, generate Gherkin-style scenarios:

### 7.1 Feature Files

```gherkin
# tests/bdd/features/user_registration.feature

Feature: User Registration
  As a new user
  I want to create an account
  So that I can access the platform

  # AC-001: Valid registration
  Scenario: Successful registration with valid data
    Given the registration page is open
    When I enter email "user@example.com"
    And I enter password "SecurePass123!"
    And I click "Register"
    Then I should see "Welcome, user@example.com"
    And a confirmation email should be sent

  # AC-002: Duplicate email rejection
  Scenario: Registration fails with existing email
    Given a user exists with email "user@example.com"
    When I enter email "user@example.com"
    And I click "Register"
    Then I should see "Email already registered"

  # AC-003: Password strength
  Scenario Outline: Password validation
    When I enter password "<password>"
    Then I should see "<message>"

    Examples:
      | password | message |
      | short    | Password must be at least 8 characters |
      | nodigits | Password must contain a number |
      | NOLOWER  | Password must contain a lowercase letter |
      | Valid1!  | (accepted) |
```

### 7.2 Step Definitions

Generate step definition stubs for each unique step:

```python
# tests/bdd/steps/test_registration.py

from pytest_bdd import given, when, then, scenarios

scenarios("../features/user_registration.feature")

@given("the registration page is open")
def registration_page(browser):
    browser.goto("/register")

@when('I enter email "<email>"')
def enter_email(browser, email):
    browser.fill("input[name=email]", email)

@then('I should see "<message>"')
def verify_message(browser, message):
    assert browser.text_content("body").find(message) != -1
```

### 7.3 Framework Setup

| Language | BDD Framework | Install |
|----------|-------------|---------|
| Python | pytest-bdd | `pip install pytest-bdd` |
| JavaScript | Cucumber.js | `npm install @cucumber/cucumber` |
| Kotlin | Cucumber-JVM | `testImplementation("io.cucumber:cucumber-java")` |

---

### 7.4 When BDD Is Required

Generate BDD/Gherkin scenarios for:
- **User-facing features** — Any AC that describes end-user behavior (registration, checkout, search)
- **Multi-step workflows** — Features involving state transitions (order lifecycle, approval flows)
- **Stakeholder-visible behavior** — Features that non-technical stakeholders need to verify

Skip BDD for:
- Internal infrastructure (DB migrations, caching, logging)
- Pure computation (math functions, data transformations)
- Developer-facing APIs with no UI (unless consumer contracts apply)

---

## STEP 8: Property-Based Tests

For domain logic with complex input spaces, generate property-based tests:

### 8.1 Python (Hypothesis)

```python
# tests/property/test_<entity>_properties.py

from hypothesis import given, strategies as st
from src.domain.user import User

@given(email=st.emails())
def test_valid_emails_are_accepted(email):
    """Any valid email format should be accepted."""
    user = User.create(email=email, name="Test")
    assert user.email == email

@given(name=st.text(min_size=1, max_size=255))
def test_names_within_length_are_accepted(name):
    """Any non-empty name within max length should be accepted."""
    user = User.create(email="test@example.com", name=name)
    assert user.name == name

@given(amount=st.decimals(min_value=0, max_value=1_000_000, places=2))
def test_order_total_is_non_negative(amount):
    """Order totals should always be non-negative."""
    order = Order.create(amount=amount)
    assert order.total >= 0
```

### 8.2 JavaScript/TypeScript (fast-check)

```typescript
// tests/property/user.property.test.ts

import fc from "fast-check";

test("email normalization is idempotent", () => {
  fc.assert(
    fc.property(fc.emailAddress(), (email) => {
      const normalized = normalizeEmail(email);
      expect(normalizeEmail(normalized)).toBe(normalized);
    })
  );
});
```

### 8.3 When Property-Based Tests Are Required

Property-based tests are **mandatory** for domain logic with these patterns:
- **Serialization roundtrips** — `deserialize(serialize(x)) == x`
- **Idempotent operations** — `f(f(x)) == f(x)`
- **Invariants** — "balance is never negative", "list is always sorted after sort"
- **Commutativity** — `merge(a, b) == merge(b, a)`
- **Domain constraints** — "age is between 0 and 150", "price is non-negative"

Skip property-based tests for:
- Simple CRUD with no domain logic (pass-through to DB)
- UI rendering (use visual snapshot tests instead)
- External API wrappers (use contract tests instead)

---

## STEP 9: Coverage Configuration

### 9.1 Coverage Thresholds

Read coverage thresholds from these sources (in priority order):
1. **Plan file** — If Stage 2 plan specifies coverage targets, use those
2. **Project config** — `pyproject.toml` / `vitest.config.ts` existing thresholds
3. **Defaults** — Fall back to the targets below

Configure minimum coverage enforcement:

**Python (pyproject.toml):**
```toml
[tool.pytest.ini_options]
addopts = "--cov=src --cov-report=term-missing --cov-fail-under=80"

[tool.coverage.run]
branch = true

[tool.coverage.report]
fail_under = 80
exclude_lines = [
    "pragma: no cover",
    "if TYPE_CHECKING:",
    "if __name__ == .__main__.",
]
```

**JavaScript (vitest.config.ts):**
```typescript
export default defineConfig({
  test: {
    coverage: {
      provider: "v8",
      thresholds: {
        lines: 80,
        branches: 70,
        functions: 80,
        statements: 80,
      },
    },
  },
});
```

### 9.2 Coverage Targets

| Metric | Minimum | Stretch Goal |
|--------|---------|-------------|
| Line coverage | 80% | 90% |
| Branch coverage | 70% | 85% |
| Function coverage | 80% | 90% |
| Domain layer | 90% | 95% |
| Infrastructure layer | 60% | 75% |

Domain logic (entities, use cases) MUST have higher coverage than infrastructure (DB adapters, external API clients).

---

## STEP 10: Mutation Testing Setup

Configure mutation testing to validate test suite quality:

### 10.1 Python (mutmut)

```toml
# pyproject.toml
[tool.mutmut]
paths_to_mutate = "src/"
tests_dir = "tests/"
runner = "python -m pytest"
```

```bash
# Run mutation testing
mutmut run
mutmut results
# Target: >70% mutation score (killed / total mutants)
```

### 10.2 JavaScript/TypeScript (Stryker)

```json
// stryker.conf.json
{
  "mutate": ["src/**/*.ts", "!src/**/*.test.ts"],
  "testRunner": "vitest",
  "reporters": ["html", "clear-text", "progress"],
  "thresholds": {
    "high": 80,
    "low": 60,
    "break": 50
  }
}
```

### 10.3 Interpreting Results

| Mutation Score | Quality |
|---------------|---------|
| >80% | Excellent — tests catch most bugs |
| 60-80% | Good — review surviving mutants |
| <60% | Weak — tests exist but don't catch bugs |

For surviving mutants, either:
- Add a test that catches the mutant
- Document why the mutation is equivalent (doesn't change behavior)

---

## STEP 11: Snapshot Test Stubs

For projects with UI, generate data and visual snapshot test stubs:

### 11.1 Data Snapshots (Jest/Vitest)

```typescript
// tests/snapshots/api-responses.test.ts

import { describe, test, expect } from "vitest";

describe("API Response Snapshots", () => {
  test("GET /users/:id response shape", async () => {
    const response = await client.get("/users/1");
    // Snapshot locks down the response shape — breaks if fields change
    expect(response.json()).toMatchSnapshot();
  });

  test("error response shape", async () => {
    const response = await client.get("/users/nonexistent");
    expect(response.json()).toMatchSnapshot();
  });
});
```

### 11.2 Data Snapshots (pytest)

```python
# tests/snapshots/test_api_responses.py

def test_user_response_shape(client, snapshot):
    """Snapshot test: GET /users/:id response shape."""
    response = client.get("/users/1")
    assert response.json() == snapshot
```

Requires `pytest-snapshot` or `syrupy`. Generate one snapshot test per API endpoint response shape and per serialized domain entity.

### 11.3 When to Use Snapshot Tests

- **API response shapes** — Lock down JSON structure to catch unintended changes
- **Serialized domain entities** — Ensure serialization format doesn't drift
- **Configuration output** — Generated config files, migration SQL
- **Visual regression** — Delegate to `verify-screenshots` skill (already covered)

Skip snapshot tests for:
- Frequently changing output (timestamps, IDs) — use selective snapshots
- Large binary output — use hash comparison instead

---

## STEP 12: Accessibility Test Stubs

For projects with UI, generate a11y test stubs:

```typescript
// tests/a11y/test_<page>.ts

import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("home page passes WCAG 2.1 AA", async ({ page }) => {
  await page.goto("/");
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa"])
    .analyze();
  expect(results.violations).toEqual([]);
});
```

Generate one a11y test per page/screen identified in the PRD.

---

## STEP 13: Red Phase Gate Verification

After generating all test files, run the test suite to verify every test either FAILS or is SKIPPED (E2E stubs). No test may pass — passing tests indicate implementation already exists or tests are vacuous.

### 13.1 Run Tests

```bash
# Python
pytest tests/unit/ tests/api/ tests/property/ tests/bdd/ -v --tb=short 2>&1 | tail -20

# JavaScript
npx vitest run tests/unit/ tests/api/ tests/property/ --reporter=verbose 2>&1 | tail -20

# Android
./gradlew :app:testDebugUnitTest 2>&1 | tail -20
```

### 13.2 Validate Results

Count results by status:
- **FAILED** — Expected. These are RED tests waiting for implementation.
- **SKIPPED** — Expected for E2E stubs (`@pytest.mark.skip` / `test.skip()`).
- **ERROR** — Acceptable if caused by missing imports (module doesn't exist yet). Fix if caused by syntax errors in test files.
- **PASSED** — NOT acceptable. A passing test means either the implementation already exists or the test asserts nothing. Investigate and fix.

### 13.3 Gate Decision

| Condition | Result |
|-----------|--------|
| All non-skipped tests FAIL or ERROR (missing import) | ✅ PASS — proceed to Step 14 |
| Any test PASSES | ❌ FAIL — investigate and fix the passing test |
| Test files have syntax errors | ❌ FAIL — fix syntax errors |
| Test collection fails entirely | ❌ FAIL — fix framework configuration |

---

## STEP 14: Output Summary & Structured Results

### 14.1 Human-Readable Summary

After generating all test files, present:

```markdown
## Test Generation Summary

**Source:** <PRD / Plan / Schema file>
**Framework:** <detected framework>

| Category | Files | Tests | Coverage Target |
|----------|-------|-------|----------------|
| Unit | 5 | 23 | 80% line |
| API | 3 | 15 | 80% line |
| BDD | 2 features | 8 scenarios | — |
| Property | 2 | 6 | — |
| E2E | 1 | 3 stubs (skipped) | — |
| Snapshot | 2 | 4 | — |
| A11y | 1 | 2 | WCAG 2.1 AA |
| **Total** | **15** | **61** | — |

**Mutation testing:** Configured (mutmut / Stryker)
**Coverage enforcement:** 80% line, 70% branch
**Red phase gate:** ✅ All tests FAIL or SKIPPED (no passing tests)

### Requirement Traceability
| Requirement | Tests | Coverage |
|-------------|-------|----------|
| AC-001 | UT-001, UT-002, AT-001 | ✅ |
| AC-002 | UT-003, AT-002, ET-001 | ✅ |
| NFR-002 | PT-001 | ✅ (stub) |
| NFR-006 | ST-001, ST-002 | ✅ |

### Next Steps
- **`/tdd`** — Start the red-green-refactor cycle with these failing tests
- **Run tests** — `<test command>` (all should FAIL — red phase)
```

### 14.2 Structured JSON Output

Write machine-readable results to `test-results/test-generator.json` for stage gate validation:

```json
{
  "skill": "test-generator",
  "timestamp": "2026-03-14T10:30:00Z",
  "result": "PASSED",
  "summary": {
    "total": 61,
    "passed": 0,
    "failed": 54,
    "skipped": 3,
    "error": 4,
    "flaky": 0
  },
  "quality_gate": "PASSED",
  "contract_check": "SKIPPED",
  "perf_baseline": "SKIPPED",
  "red_phase_gate": {
    "status": "PASSED",
    "passing_tests": [],
    "failing_tests": 54,
    "skipped_stubs": 3,
    "import_errors": 4
  },
  "test_matrix": {
    "requirements_covered": 12,
    "requirements_total": 12,
    "unmapped_requirements": []
  },
  "artifacts": [
    "tests/unit/",
    "tests/api/",
    "tests/e2e/",
    "tests/bdd/",
    "tests/property/",
    "tests/snapshots/",
    "tests/a11y/",
    "tests/conftest.py",
    "tests/factories.py"
  ],
  "failures": [],
  "warnings": [],
  "duration_ms": 8500
}
```

The `result` field is `PASSED` when:
- All non-skipped tests FAIL or ERROR (no passing tests)
- Every requirement in the PRD maps to at least one test
- Test files have no syntax errors

The `result` field is `FAILED` when:
- Any test passes (red phase violation)
- Requirements exist with no mapped tests
- Test files cannot be collected

---

## Contract Test Decision Criteria

Use the `contract-test` skill (Pact) when:
- **Multi-service architecture** — 2+ services communicating via HTTP/gRPC/messaging
- **Separate deploy cycles** — Consumer and provider deploy independently
- **Cross-team API boundaries** — Different teams own consumer vs provider

Skip contract tests for:
- **Monoliths** — Single deployable unit with no service boundaries
- **Internal modules** — Modules within the same service (use unit tests instead)
- **Third-party APIs** — You don't control the provider (use integration tests with recorded responses)

---

## Test File Naming Convention

Follow the project's existing convention. If no convention exists, use:

| Language | Test Files | Test Classes/Functions |
|----------|-----------|----------------------|
| Python | `test_<entity>.py` | `class Test<Entity>:` / `def test_<behavior>():` |
| JavaScript | `<entity>.test.ts` | `describe("<Entity>")` / `test("<behavior>")` |
| Kotlin | `<Entity>Test.kt` | `class <Entity>Test` / `fun \`should <behavior>\`()` |

---

## MUST DO

- Always build a test matrix mapping every requirement to tests (Step 1)
- Always generate shared test infrastructure before test files (Step 3)
- Always generate test data factories (Step 4.3)
- Always include edge case tests (empty, null, boundary, invalid type)
- Always configure coverage thresholds (Step 9) — read from plan/config before using defaults
- Always trace tests back to PRD requirements
- Always generate BDD scenarios for user-facing features (Step 7)
- Always generate E2E stubs with `skip` markers and fully-defined Page Objects (Step 6)
- Always run the red phase gate (Step 13) to verify all tests FAIL
- Always write structured JSON output to `test-results/test-generator.json` (Step 14)

## MUST NOT DO

- MUST NOT generate tests that pass before implementation — they must be RED
- MUST NOT skip the test matrix — untested requirements are undiscovered bugs
- MUST NOT hardcode test data — use factories with overrides
- MUST NOT duplicate `tdd` skill's red-green-refactor workflow — this skill generates stubs, `/tdd` drives the implementation cycle
- MUST NOT duplicate `playwright` skill's E2E patterns — generate stubs that follow its conventions
- MUST NOT generate flaky tests — follow rules from `testing.md` (no sleep, deterministic data, isolated state)
- MUST NOT begin implementation during this skill — this skill produces failing tests, not passing code
- MUST NOT write E2E test bodies — only skipped stubs with Page Objects. Stage 8 fills in assertions
- MUST NOT skip the red phase gate — a passing test at this stage is a bug in the test
