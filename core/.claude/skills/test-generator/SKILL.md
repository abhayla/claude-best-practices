---
name: test-generator
description: >
  Generate test suites from PRD requirements, schema, or API specs. Produces shared
  test infrastructure, unit, API, E2E stubs, BDD/Gherkin, property-based, snapshot
  tests, coverage thresholds, and mutation testing setup. Use when starting TDD red
  phase before implementation.
triggers:
  - generate tests
  - test stubs
  - test generation
  - pre-implementation tests
  - write tests from requirements
  - test matrix
allowed-tools: "Bash Read Write Edit Grep Glob Agent"
argument-hint: "<PRD file path, plan file path, schema file path, feature description, or coverage gap report>"
version: "1.2.0"
type: workflow
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
5. **Coverage gap report** — File paths with uncovered lines from `/coverage-analysis` output. Parse the gap report to extract file paths, line ranges, and branch coverage gaps. Generate targeted tests that exercise the specific uncovered code paths identified in the report. Prioritize gaps in domain and service layers over infrastructure code

Build the test matrix:

```markdown
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

## STEP 9: Coverage Configuration


**Read:** `references/coverage-configuration.md` for detailed step 9: coverage configuration reference material.

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

## STEP 11: Snapshot Test Stubs

For projects with UI, generate data and visual snapshot test stubs:


**Read:** `references/snapshot-test-stubs.md` for detailed step 11: snapshot test stubs reference material.

# tests/snapshots/test_api_responses.py

def test_user_response_shape(client, snapshot):
    """Snapshot test: GET /users/:id response shape."""
    response = client.get("/users/1")
    assert response.json() == snapshot
```

Requires `pytest-snapshot` or `syrupy`. Generate one snapshot test per API endpoint response shape and per serialized domain entity.

## STEP 12: Accessibility Test Stubs

**Read:** `references/accessibility-test-stubs.md` for detailed step 12: accessibility test stubs reference material.

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

## STEP 14: Output Summary & Structured Results

### 14.1 Human-Readable Summary

After generating all test files, present:

```markdown
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
- After implementation, re-validate the test matrix by scanning test docstrings and comments for requirement IDs (AC-xxx, NFR-xxx). Flag any requirement that has lost its test mapping — a requirement without a corresponding test is a coverage regression that must be fixed before the PR merges

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
