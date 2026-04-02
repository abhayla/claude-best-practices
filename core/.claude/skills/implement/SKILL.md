---
name: implement
description: >
  Implement a feature or fix following a structured workflow: requirements analysis,
  test creation, implementation, test execution, fix-loop delegation, and verification.
  Use when user requests new functionality or structured bug fixes. Use /fix-issue
  for GitHub Issues, /tdd for strict red-green-refactor, /development-loop for
  full ideation-to-commit orchestration.
triggers:
  - implement
  - implement feature
  - build feature
  - add feature
  - create feature
  - implement fix
  - implement the
  - structured implementation
allowed-tools: "Bash Read Grep Glob Write Edit Skill"
argument-hint: "<feature-description>"
version: "2.2.0"
type: workflow
---

# Implement Feature/Fix

Tests are mandatory. If tests fail, delegate to `/fix-loop` — do not proceed
without passing tests. If no test framework exists, note it and proceed.

**Request:** $ARGUMENTS

If no arguments are provided, ask the user what to implement before proceeding.

---

## STEP 1: Analyze Requirements

1. Read the feature request / issue description carefully
2. Identify affected files and components
3. Check existing tests and code patterns in the area
4. Review any related documentation
5. **Cross-layer impact analysis** — If the change touches one layer, check if other layers need updating:

| Changed Layer | Also Check |
|--------------|-----------|
| Backend API (routes, controllers) | Frontend callers, API docs, integration tests, OpenAPI spec |
| Database (schema, migrations) | ORM models, queries, seed data, backup scripts |
| Frontend (components, pages) | API contracts match, E2E tests, accessibility |
| Shared types/interfaces | All importers across frontend + backend |
| Config/environment | Deployment scripts, CI/CD, documentation, .env.example |

List all affected layers before proceeding. If 3+ layers are affected, suggest using `/writing-plans` first to plan the cross-layer changes.

## STEP 2: Create/Update Tests

Before implementing, write or update tests that define the expected behavior:

1. Detect the project's test framework (check CLAUDE.md, pyproject.toml,
   package.json, build.gradle). If no test framework is configured, log
   "WARN: No test framework detected — skipping test-first step. Recommend
   adding tests as a follow-up." and proceed to Step 3.
2. Identify the appropriate test file(s)
3. Write tests that will FAIL before implementation (TDD approach)
4. Follow existing test patterns and conventions in the project

## STEP 3: Implement the Feature

1. Make minimal, focused changes
2. Follow existing code patterns and conventions
3. Keep changes reversible where possible
4. Add comments only where logic isn't self-evident

## STEP 4: Run Tests

Run the relevant test suite to verify implementation:

1. Run targeted tests for the changed area first
2. If targeted tests pass, run broader test suite
3. If tests fail, proceed to fix-loop

## STEP 5: Fix Loop (if tests fail)

Delegate to `/fix-loop` with the failing test command:

```
Skill("fix-loop", args="retest_command: <the failing test command>")
```

Continue until all tests pass.

## STEP 6: Verification (Mandatory Gate)

Do NOT report completion until ALL checks pass. This is a hard gate, not advisory.

### 6.1 Multi-Layer Verification Checklist

| Check | Command/Action | Status |
|-------|---------------|--------|
| Unit tests | Run targeted test suite | ⬜ |
| Integration tests | Run broader test suite | ⬜ |
| Regression check | Run full test suite | ⬜ |
| Linting/formatting | Run project linter | ⬜ |
| Type checking | Run type checker if applicable | ⬜ |
| Build succeeds | Run build command | ⬜ |
| Edge cases | Verify boundary conditions in tests | ⬜ |

Skip checks that don't apply (e.g., no type checker configured), but never skip tests.

### 6.2 Partial Failure Protocol

If verification partially passes (e.g., 1 flaky test, lint warning):
1. **Flaky test** — Re-run 2x. If it passes on retry, note it but don't block. Flag to user.
2. **Lint/format warning** — Fix before proceeding. These are deterministic.
3. **Unrelated test failure** — Verify it fails on the base branch too (`git stash && run tests && git stash pop`). If pre-existing, note it and proceed.
4. **Type error in unchanged code** — Note and proceed. Don't fix unrelated type issues.

### 6.3 Verification Report

After all checks pass, output:
```
Verification: PASSED
- Tests: X passed, 0 failed
- Lint: clean
- Build: success
- Regressions: none detected
```

If any check fails after fix attempts, escalate to user with the report showing what passed and what failed.

### 6.4 Post-Fix Review

If significant changes were made (3+ files or complex logic), review with `/post-fix-pipeline`.

## STEP 7: Post-Implementation (Optional)

1. If running standalone (not inside `/executing-plans`), invoke `/learn-n-improve session` to capture learnings
2. Provide summary of changes to the user

## STEP 8: Structured Output

Write machine-readable results to `test-results/implement.json`:

```json
{
  "skill": "implement",
  "timestamp": "<ISO-8601>",
  "result": "PASSED|FAILED",
  "summary": {
    "total_tests": "<count>",
    "passed": "<count>",
    "failed": "<count>",
    "fix_iterations": "<count>"
  },
  "quality_gate": "PASSED|WARNED|SKIPPED",
  "failures": [],
  "warnings": [],
  "duration_ms": "<elapsed>"
}
```

Create `test-results/` directory if it doesn't exist. This JSON is consumed by stage gates.

---

## CRITICAL RULES

- MUST write tests before or alongside implementation — skip only if no test framework is detected
- MUST NOT apply fixes directly when tests fail — delegate to `/fix-loop`
- MUST NOT proceed past Step 6 without all verification checks passing or explicitly noted
- MUST ask for clarification if `$ARGUMENTS` is empty — do not guess what to implement
- Follow existing project conventions (check CLAUDE.md and .claude/rules/)
- Make minimal changes — don't refactor unrelated code
- If stuck after 3 fix-loop iterations, ask the user for guidance
