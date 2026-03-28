---
description: Nudges to e2e-best-practices skill when writing or modifying E2E tests.
globs: ["**/e2e/**", "**/tests/e2e/**", "**/*.e2e.*", "**/integration_test/**"]
---

# E2E Test Writing

When writing or modifying E2E tests, consult `/e2e-best-practices` for:

- **Selector strategy** — Use accessibility role/label before test IDs or CSS
- **Test data isolation** — UUID-based unique data, API-driven seeding, explicit teardown
- **Wait strategy** — Auto-wait assertions, never `sleep()` or `waitForTimeout()`
- **Mock decisions** — Mock external APIs, keep internal services real
- **Auth patterns** — Login once, reuse state for non-auth tests
- **Anti-patterns** — Read `e2e-best-practices/references/anti-patterns.md`

MUST NOT use fixed delays, shared test accounts, or hardcoded primary keys in E2E tests.
