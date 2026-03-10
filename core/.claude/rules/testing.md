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

## Documentation

- Add brief comments explaining non-obvious test setups
- Document test fixtures and their purpose
- Keep test helper functions close to where they're used
