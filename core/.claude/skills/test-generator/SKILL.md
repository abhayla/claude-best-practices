---
name: test-generator
description: >
  Auto-generate test suites from PRD requirements, schema, or API specs.
  Produces unit, API, E2E stubs with BDD/Gherkin, coverage thresholds,
  property-based testing, and mutation testing setup. Use before implementation (TDD red phase).
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

## STEP 3: Generate Unit Tests

For each domain entity and use case, generate test stubs:

### 3.1 Test Structure

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

### 3.2 Edge Cases to Generate

For each entity, auto-generate tests for:
- **Empty/null inputs** — Every required field with empty/null value
- **Boundary values** — Max length strings, min/max numbers, date boundaries
- **Invalid types** — Wrong type for each field
- **Duplicate handling** — Unique constraint violations
- **Relationship integrity** — FK references that don't exist

### 3.3 Test Data Factories

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

## STEP 4: Generate API Tests

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

## STEP 5: Generate BDD Scenarios

For stakeholder-readable specs, generate Gherkin-style scenarios:

### 5.1 Feature Files

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

### 5.2 Step Definitions

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

### 5.3 Framework Setup

| Language | BDD Framework | Install |
|----------|-------------|---------|
| Python | pytest-bdd | `pip install pytest-bdd` |
| JavaScript | Cucumber.js | `npm install @cucumber/cucumber` |
| Kotlin | Cucumber-JVM | `testImplementation("io.cucumber:cucumber-java")` |

---

## STEP 6: Property-Based Tests

For domain logic with complex input spaces, generate property-based tests:

### 6.1 Python (Hypothesis)

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

### 6.2 JavaScript/TypeScript (fast-check)

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

### 6.3 When to Use Property-Based Tests

Generate property tests for:
- **Serialization roundtrips** — `deserialize(serialize(x)) == x`
- **Idempotent operations** — `f(f(x)) == f(x)`
- **Invariants** — "balance is never negative", "list is always sorted after sort"
- **Commutativity** — `merge(a, b) == merge(b, a)`
- **Domain constraints** — "age is between 0 and 150", "price is non-negative"

---

## STEP 7: Coverage Configuration

### 7.1 Coverage Thresholds

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

### 7.2 Coverage Targets

| Metric | Minimum | Stretch Goal |
|--------|---------|-------------|
| Line coverage | 80% | 90% |
| Branch coverage | 70% | 85% |
| Function coverage | 80% | 90% |
| Domain layer | 90% | 95% |
| Infrastructure layer | 60% | 75% |

Domain logic (entities, use cases) MUST have higher coverage than infrastructure (DB adapters, external API clients).

---

## STEP 8: Mutation Testing Setup

Configure mutation testing to validate test suite quality:

### 8.1 Python (mutmut)

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

### 8.2 JavaScript/TypeScript (Stryker)

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

### 8.3 Interpreting Results

| Mutation Score | Quality |
|---------------|---------|
| >80% | Excellent — tests catch most bugs |
| 60-80% | Good — review surviving mutants |
| <60% | Weak — tests exist but don't catch bugs |

For surviving mutants, either:
- Add a test that catches the mutant
- Document why the mutation is equivalent (doesn't change behavior)

---

## STEP 9: Accessibility Test Stubs

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

## STEP 10: Output Summary

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
| E2E | 1 | 3 stubs | — |
| A11y | 1 | 2 | WCAG 2.1 AA |
| **Total** | **14** | **57** | — |

**Mutation testing:** Configured (mutmut / Stryker)
**Coverage enforcement:** 80% line, 70% branch

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

---

## MUST DO

- Always build a test matrix mapping every requirement to tests (Step 1)
- Always generate test data factories (Step 3.3)
- Always include edge case tests (empty, null, boundary, invalid type)
- Always configure coverage thresholds (Step 7)
- Always trace tests back to PRD requirements
- Always generate BDD scenarios for user-facing features (Step 5)
- Always verify all generated tests FAIL (TDD red phase)

## MUST NOT DO

- MUST NOT generate tests that pass before implementation — they must be RED
- MUST NOT skip the test matrix — untested requirements are undiscovered bugs
- MUST NOT hardcode test data — use factories with overrides
- MUST NOT duplicate `tdd` skill's red-green-refactor workflow — this skill generates stubs, `/tdd` drives the implementation cycle
- MUST NOT duplicate `playwright` skill's E2E patterns — generate stubs that follow its conventions
- MUST NOT generate flaky tests — follow rules from `testing.md` (no sleep, deterministic data, isolated state)
- MUST NOT begin implementation during this skill — this skill produces failing tests, not passing code
