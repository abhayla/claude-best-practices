---
description: Test-driven development workflow rules for red-green-refactor cycle.
globs: ["**/test_*", "**/*_test.*", "**/tests/**", "**/*.test.*", "**/*.spec.*", "src/**", "lib/**", "app/**"]
---

# TDD Rules

## Red-Green-Refactor Cycle

1. **Red** — Write a failing test BEFORE writing production code. The test MUST fail for the right reason (missing function, wrong return value) — not because of a syntax error.
2. **Green** — Write the MINIMUM production code to make the failing test pass. Do not optimize, do not generalize, do not handle edge cases yet.
3. **Refactor** — Improve code structure while keeping all tests green. Run tests after every refactoring step. Commit refactorings separately from feature commits.

## When Test-First is Mandatory

- New features with clear acceptance criteria
- Bug fixes (write a test that reproduces the bug FIRST, then fix)
- API endpoints (write request/response assertions before implementing handlers)
- Data transformations (write input/output assertions before implementing logic)

## When Test-After is Acceptable

- Spike/prototype work (exploratory code that will be rewritten)
- Pure UI layout changes with no logic (verified visually or via screenshots)
- Generated code (migrations, OpenAPI stubs, scaffolding)
- Configuration changes (environment variables, CI/CD files)

## Refactoring Constraints

- Tests MUST stay green throughout the refactor phase — if a refactoring breaks a test, revert immediately
- One refactoring per commit — do not mix structural changes with behavioral changes
- No new features during refactoring — refactoring changes structure, not behavior
- Use the refactoring catalog in `/code-quality-gate` Step 9 for systematic refactoring

## Test Granularity

| Change Scope | Test Level | Example |
|-------------|-----------|---------|
| Single function/method | Unit test | `test_calculate_discount()` |
| Service/repository interaction | Integration test | `test_create_user_persists_to_db()` |
| Full request → response | API test | `test_post_users_returns_201()` |
| Multi-page user flow | E2E test (Stage 8) | `test_login_then_checkout()` |

Write the most specific test that covers the behavior. Prefer unit tests over integration tests when possible.

## Anti-Patterns

- **Test-after-the-fact** — Writing tests after implementation to hit a coverage target misses the design feedback that TDD provides. The test should drive the interface.
- **Testing implementation details** — Tests should assert behavior (inputs → outputs), not internal structure (method calls, private state). Implementation-coupled tests break on every refactor.
- **Gold-plating in green phase** — During the green phase, resist the urge to handle edge cases or optimize. That belongs in the next red-green cycle or the refactor phase.
