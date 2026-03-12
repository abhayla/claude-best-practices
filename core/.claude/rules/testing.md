---
description: Testing conventions and best practices.
---

# Testing Rules

## General Principles

1. **Test Isolation** — Each test should be independent; no shared mutable state
2. **Descriptive Names** — Test names should describe the scenario and expected outcome
3. **Arrange-Act-Assert** — Structure tests clearly with setup, action, and verification
4. **One Assertion Focus** — Each test should verify one behavior (multiple asserts OK if related)
5. **No Test Interdependence** — Tests must pass in any order

## Test Categories

| Category | Purpose | Speed |
|----------|---------|-------|
| Unit | Individual functions/methods | Fast (ms) |
| Integration | Component interactions | Medium (seconds) |
| E2E | Full user flows | Slow (minutes) |

## Running Tests

- Run targeted tests first (faster feedback)
- Run full suite before committing
- Use `-x` flag to stop on first failure when debugging

## Fixtures & Test Data

- Use factories/fixtures for test data — don't hardcode
- Clean up test data in teardown
- Use in-memory databases for unit tests where possible
- Mock external services (APIs, email, file systems)

## Handling Failures

- Distinguish real failures from flaky tests
- Fix flaky tests immediately — they erode confidence
- Never `@skip` or `@ignore` a test without a tracking issue
- Re-run flaky tests 2-3 times before investigating

## Flaky Test Prevention

- **Use auto-wait over timeouts** — Never use `sleep(2)` or fixed delays. Use framework-provided waiters: `waitFor`, `eventually`, `toBeVisible`. Fixed delays are the #1 cause of flaky tests.
- **Isolate test state** — Each test gets its own database transaction, browser context, or temp directory. Never share mutable state across tests. Use `beforeEach` setup, not `beforeAll`.
- **Mock external dependencies** — Network calls to third-party APIs, email services, payment providers MUST be mocked. External service flakiness should not fail your tests.
- **Use deterministic test data** — No `random()`, no `Date.now()` in assertions, no reliance on database auto-increment order. Use factories with fixed seeds.
- **Control time** — Use clock mocking (`jest.useFakeTimers`, `freezegun`, `timecop`) for time-dependent logic. Never assert against wall clock time.
- **Avoid order dependence** — Tests MUST pass when run individually, in reverse order, or in random order. Use `--randomize` flag to verify.

## Documentation

- Add brief comments explaining non-obvious test setups
- Document test fixtures and their purpose
- Keep test helper functions close to where they're used
