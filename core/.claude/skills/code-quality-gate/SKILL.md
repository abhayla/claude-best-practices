---
name: code-quality-gate
description: >
  Enforce code quality standards including cyclomatic complexity, duplication detection,
  SOLID checklist, error handling audit, and dead code detection. Use after implementing
  a feature or refactoring to validate code meets quality thresholds before merging.
triggers:
  - code quality
  - quality gate
  - quality check
  - complexity check
  - duplication check
  - SOLID check
  - refactor phase
allowed-tools: "Bash Read Write Edit Grep Glob Agent"
argument-hint: "<file paths, directory, or 'all changed files'>"
version: "1.2.0"
type: workflow
---

# Code Quality Gate — Post-Implementation Quality Enforcement

Run automated and manual quality checks on implementation code. Use after tests pass (TDD green phase) to catch technical debt before review.

**Scope:** $ARGUMENTS

---

## STEP 1: Identify Changed Files

Determine what code to analyze:

```bash
# If specific files provided, use those
# If "all changed files", use git diff:
git diff --name-only origin/main...HEAD -- '*.py' '*.ts' '*.tsx' '*.kt' '*.go' '*.rs'
```

Exclude generated files, test files, and configuration from quality analysis:
```
EXCLUDE: **/generated/**, **/*.test.*, **/tests/**, **/migrations/**, **/*.config.*
```

---

## STEP 2: Cyclomatic Complexity

### 2.1 Thresholds

| Complexity | Rating | Action |
|-----------|--------|--------|
| 1-5 | Simple | ✅ Pass |
| 6-10 | Moderate | ⚠️ Review — consider simplifying |
| 11-20 | Complex | ❌ MUST refactor — extract methods |
| >20 | Very complex | ❌ BLOCK — cannot merge |

### 2.2 Stack-Specific Tools

| Stack | Tool | Command |
|-------|------|---------|
| Python | radon | `radon cc <path> -s -n C` (show C+ complexity) |
| Python | flake8 | `flake8 --max-complexity 10 <path>` |
| JavaScript/TS | eslint | ESLint rule `complexity: ["error", 10]` |
| Go | gocyclo | `gocyclo -over 10 .` |
| Rust | clippy | `cargo clippy -- -W clippy::cognitive_complexity` |
| Kotlin | detekt | `detekt --config detekt.yml` (complexity ruleset) |

### 2.3 Manual Review for Functions >10

For any function with complexity >10, analyze and suggest refactoring:

```markdown
**Function:** `process_order()` in `src/application/order_service.py:45`
**Complexity:** 14 (EXCEEDS threshold of 10)
**Cause:** 3 nested if/else + 2 loops
**Suggestion:** Extract `validate_inventory()` and `calculate_discount()` as separate methods
```

---

## STEP 3: Duplication Detection

### 3.1 Tools

| Stack | Tool | Command |
|-------|------|---------|
| Any | jscpd | `jscpd --min-lines 5 --min-tokens 50 --reporters console src/` |
| Python | pylint | `pylint --disable=all --enable=duplicate-code <path>` |
| JavaScript/TS | jscpd | `npx jscpd --min-lines 5 src/` |

### 3.2 Thresholds

| Metric | Threshold | Action |
|--------|-----------|--------|
| Duplicate blocks | ≤3% of total lines | ✅ Pass |
| Duplicate blocks | 3-5% | ⚠️ Review — extract shared logic |
| Duplicate blocks | >5% | ❌ Refactor — DRY violation |

### 3.3 Reporting

For each duplicate block found:

```markdown
**Duplicate:** 12 lines duplicated across 2 locations
- `src/services/user_service.py:23-34`
- `src/services/order_service.py:45-56`
**Suggestion:** Extract to `src/domain/validators.py:validate_email()`
```

---

## STEP 4: SOLID Principles Checklist

Review each changed file/class against SOLID:

### 4.1 Single Responsibility (SRP)

- [ ] Each class/module has one reason to change
- [ ] No "God classes" with mixed concerns (DB + HTTP + business logic)
- [ ] File length < 300 lines (excluding tests)

**Red flags:** Class with both `save_to_db()` and `send_email()`, route handler with inline SQL

### 4.2 Open/Closed (OCP)

- [ ] New behavior added via extension, not modification of existing code
- [ ] Strategy/plugin patterns used for variable behavior
- [ ] No switch/if chains that must be edited to add new types

**Red flags:** `if type == "A" ... elif type == "B" ... elif type == "C"` growing chains

### 4.3 Liskov Substitution (LSP)

- [ ] Subtypes are substitutable for their base types
- [ ] No methods that throw "not implemented" exceptions
- [ ] Overridden methods don't strengthen preconditions or weaken postconditions

### 4.4 Interface Segregation (ISP)

- [ ] Interfaces are small and focused
- [ ] No "fat interfaces" where implementers must stub unused methods
- [ ] Clients depend only on the methods they use

### 4.5 Dependency Inversion (DIP)

- [ ] High-level modules don't import low-level modules directly
- [ ] Dependencies flow inward: presentation → application → domain
- [ ] Infrastructure depends on domain abstractions, not vice versa

**Red flags:** `from src.infrastructure.postgres_repo import PostgresUserRepo` in domain layer

### 4.6 Reporting

```markdown
## SOLID Analysis: <file>

| Principle | Status | Notes |
|-----------|--------|-------|
| SRP | ✅ | Single purpose: user authentication |
| OCP | ⚠️ | Payment method selection uses if/elif chain |
| LSP | ✅ | No inheritance violations |
| ISP | ✅ | Interfaces are focused |
| DIP | ❌ | Domain imports PostgreSQL repo directly |
```

---

## STEP 5: Clean Architecture Layer Validation

> **Orchestrator note:** When this skill is invoked as part of `/review-gate`, SKIP this entire Step 5. The `/architecture-fitness` skill runs a deeper version of this check (adding coupling metrics, circular dependency detection, and ADR lifecycle review). Running both duplicates findings. Only execute Step 5 when `code-quality-gate` is invoked standalone.

Verify dependency direction follows Clean Architecture rules:

```
ALLOWED:
  presentation → application → domain
  infrastructure → domain (implements interfaces)
  infrastructure → application (implements ports)

FORBIDDEN:
  domain → infrastructure
  domain → presentation
  application → infrastructure (use ports/interfaces)
```

### 5.1 Automated Check

Search for forbidden imports:

```bash
# Python: domain should not import from infrastructure
grep -rn "from.*infrastructure" src/domain/ && echo "❌ VIOLATION" || echo "✅ Clean"

# Python: application should not import from infrastructure
grep -rn "from.*infrastructure" src/application/ && echo "❌ VIOLATION" || echo "✅ Clean"
```

### 5.2 Report Violations

```markdown
**Layer violation:** `src/domain/user.py:5`
  `from src.infrastructure.database import SessionLocal`
**Fix:** Define a `UserRepository` protocol in `src/domain/ports.py` and inject it
```

---

## STEP 6: Structured Logging Audit

### 6.1 Requirements

- [ ] All log calls use structured format (JSON or key=value), not f-strings
- [ ] Each log entry includes: timestamp, level, message, correlation_id
- [ ] Sensitive data (passwords, tokens, PII) is NEVER logged
- [ ] Logs go to stdout (12-factor Factor XI)
- [ ] Log levels used correctly: DEBUG (dev), INFO (events), WARN (recoverable), ERROR (failures)

### 6.2 Anti-patterns to Flag

```python
# ❌ Bad: unstructured, leaks PII
logger.info(f"User {user.email} logged in with token {token}")

# ✅ Good: structured, no PII
logger.info("user_login", extra={"user_id": user.id, "method": "oauth2"})
```

### 6.3 Stack-Specific Setup

| Stack | Library | Pattern |
|-------|---------|---------|
| Python | structlog | `structlog.get_logger().info("event", key=value)` |
| Node | pino | `logger.info({key: value}, "event")` |
| Go | slog | `slog.Info("event", "key", value)` |
| Kotlin | kotlin-logging | `logger.info { "event key=$value" }` |

---

## STEP 7: Error Handling Strategy Audit

For the full audit checklist covering Python/FastAPI, Kotlin/Android,
TypeScript/React patterns, timeout strategies, and circuit breakers:

Read: `references/error-handling-audit.md`

Produce a per-file checklist result (PASS/WARN/BLOCK) for the Step 11 report.

---

## STEP 8: Coverage Diff Analysis

Measure test coverage specifically on changed/new code — not just overall. A PR can maintain 80% overall coverage while adding 500 lines with 0% coverage.

### 8.1 Generate Diff Coverage

| Stack | Tool | Command |
|-------|------|---------|
| Python | diff-cover | `diff-cover coverage.xml --compare-branch=origin/main --fail-under=80` |
| JavaScript/TS | diff-cover (via nyc) | `nyc report --reporter=json && diff-cover coverage/coverage-final.json --compare-branch=origin/main` |
| Kotlin/Android | JaCoCo + diff-cover | `./gradlew jacocoTestReport && diff-cover build/reports/jacoco/test/jacocoTestReport.xml --compare-branch=origin/main` |
| Go | go-cover-diff | `go test -coverprofile=cover.out ./... && go-cover-diff cover.out` |

```bash
# Python: full workflow
pytest --cov=src --cov-report=xml tests/
pip install diff-cover
diff-cover coverage.xml --compare-branch=origin/main --fail-under=80 --html-report=diff-coverage.html

# JavaScript: full workflow
npx jest --coverage --coverageReporters=json
npx diff-cover coverage/coverage-final.json --compare-branch=origin/main --fail-under=80

# Generic: get list of changed lines and check coverage
git diff origin/main...HEAD --unified=0 -- '*.py' '*.ts' '*.kt' | grep "^++" | grep -v "test"
```

### 8.2 Thresholds

| Metric | Threshold | Action |
|--------|-----------|--------|
| Diff coverage ≥ 80% | ✅ Pass | New code is well-tested |
| Diff coverage 60-79% | ⚠️ Review | Identify untested paths, add tests for critical logic |
| Diff coverage < 60% | ❌ Block | New code lacks tests — add before merge |
| Overall coverage drop > 2% | ❌ Block | PR is diluting test coverage |
| New file with 0% coverage | ❌ Block | Every new file needs at least happy-path tests |

### 8.3 Reporting

```markdown
## Coverage Diff Report

**Branch:** feature/user-auth → main
**Changed files:** 8 (324 new lines, 45 modified)

| File | New Lines | Covered | Diff Coverage |
|------|-----------|---------|---------------|
| src/auth/login.py | 89 | 78 | 87% ✅ |
| src/auth/oauth.py | 124 | 62 | 50% ❌ |
| src/models/user.py | 45 | 45 | 100% ✅ |
| src/api/routes.py | 66 | 48 | 73% ⚠️ |

**Diff coverage: 72%** ⚠️ (threshold: 80%)
**Overall coverage: 83% → 82%** ✅ (within 2% tolerance)

### Untested Lines (high-risk)
- `src/auth/oauth.py:45-67` — OAuth token refresh error handling
- `src/auth/oauth.py:89-112` — Token revocation flow
- `src/api/routes.py:34-42` — Rate limiting bypass path
```

### 8.4 CI Integration

```yaml
# GitHub Actions: coverage diff check
- name: Run tests with coverage
  run: pytest --cov=src --cov-report=xml
- name: Check diff coverage
  run: |
    pip install diff-cover
    diff-cover coverage.xml --compare-branch=origin/main --fail-under=80
```

---

## STEP 8.5: Mutation Testing

For the full mutation testing workflow covering mutmut (Python), Stryker (JS/TS),
evaluation thresholds, and CI integration:

Read: `references/mutation-testing.md`

Include mutation score in the Step 11 report. Gate: <40% = BLOCK, 40-59% = WARN.

---

## STEP 9: TDD Refactor Phase

After all tests pass (green), execute the refactor phase:

### 7.1 Refactoring Checklist

- [ ] Extract methods for any function > 20 lines
- [ ] Rename variables/functions for clarity
- [ ] Remove dead code and unused imports
- [ ] Consolidate duplicate logic
- [ ] Simplify conditional expressions
- [ ] Apply design patterns where appropriate

### 7.2 Refactoring Rules

1. **Tests must stay green** — Run tests after every refactoring step
2. **One refactoring at a time** — Don't change behavior and structure simultaneously
3. **Commit after each refactoring** — Separate refactor commits from feature commits
4. **No new features** — Refactoring changes structure, not behavior

### 7.3 Common Refactoring Catalog

| Smell | Refactoring | When to Apply |
|-------|------------|---------------|
| Long method | Extract Method | Function > 20 lines |
| Duplicate code | Extract Function/Class | Same code in 2+ places |
| Long parameter list | Introduce Parameter Object | > 3 parameters |
| Feature envy | Move Method | Method uses another class's data more than its own |
| God class | Extract Class | Class has > 5 responsibilities |
| Primitive obsession | Value Object | Primitives used for domain concepts (email, money) |

---

## STEP 10: Dead Code Detection

For the full dead code detection workflow covering vulture (Python), ts-prune (JS/TS),
classification, and gate behavior:

Read: `references/dead-code-detection.md`

Dead code is WARN only (non-blocking). Include count in Step 12 structured output.

---

## STEP 11: Quality Report

Present a summary gate report:

```markdown
## Code Quality Gate Report

**Scope:** 12 files changed (487 lines added, 23 removed)
**Date:** <date>

### Results

| Check | Status | Details |
|-------|--------|---------|
| Complexity | ✅ Pass | Max: 8 (in `order_service.py`) |
| Duplication | ✅ Pass | 1.2% duplicate (under 3% threshold) |
| SOLID | ⚠️ 1 issue | DIP violation in `user_handler.py` |
| Layer deps | ✅ Pass | No forbidden imports |
| Logging | ✅ Pass | All structured, no PII |
| Error handling | ✅ Pass | Typed errors, no swallowed exceptions, timeouts set |
| Coverage diff | ✅ Pass | 85% diff coverage (threshold: 80%) |
| Dead code | ⚠️ Warn | 2 unused functions detected (non-blocking) |
| Refactoring | ✅ Done | 3 extract-method refactorings applied |

### Gate Decision
- **PASS** — All critical checks pass, 1 minor issue flagged for review
- **BLOCK** — N critical issues must be resolved before merge

### Issues to Address
1. [Minor] `src/presentation/user_handler.py:12` — imports from infrastructure directly (DIP)
   **Fix:** Inject `UserRepository` via constructor
```

## STEP 12: Structured Output

Write machine-readable results to `test-results/code-quality-gate.json`:

```json
{
  "skill": "code-quality-gate",
  "timestamp": "<ISO-8601>",
  "result": "PASSED|FAILED",
  "checks": {
    "complexity": "PASS|WARN|BLOCK",
    "duplication": "PASS|WARN|BLOCK",
    "solid": "PASS|WARN|BLOCK",
    "layer_deps": "PASS|BLOCK",
    "logging": "PASS|WARN",
    "error_handling": "PASS|WARN|BLOCK",
    "coverage_diff": "PASS|WARN|BLOCK",
    "dead_code": "PASS|WARN",
    "dead_code_count": 0,
    "refactoring": "DONE|SKIPPED"
  },
  "gate_decision": "PASS|BLOCK",
  "issues": [],
  "duration_ms": "<elapsed>"
}
```

Create `test-results/` directory if it doesn't exist. This JSON is consumed by stage gates and downstream stages.

---

## Gate Decision Matrix

Use this matrix to determine the `gate_decision` value. Any single BLOCK → overall gate is BLOCK.

| Check | PASS | WARN (non-blocking) | BLOCK (must fix before merge) |
|-------|------|---------------------|-------------------------------|
| Complexity | ≤10 per function | — | >10 per function |
| Duplication | ≤3% of changed lines | 3-5% of changed lines | >5% of changed lines |
| SOLID | 0 violations | 1-2 minor issues (e.g., slightly long class) | Any critical violation (God class, domain importing infrastructure) |
| Layer deps | 0 forbidden imports | — | Any forbidden import (domain→infra, domain→presentation) |
| Logging | All structured, no PII | Missing correlation ID on some logs | PII detected in log output |
| Error handling | Typed errors, timeouts set, no swallowed exceptions | Missing circuit breaker for external deps | Empty catch/except block, generic Exception catch at non-top-level |
| Coverage diff | ≥80% on new/changed code | 60-79% on new/changed code | <60% on new code OR new file with 0% coverage |
| Dead code | 0 items found | 1+ items found (informational) | — (dead code is never BLOCK) |
| Refactoring | Refactor phase completed | — | — (refactoring is always DONE or SKIPPED, never BLOCK) |

**Overall gate:**
- `PASS` — All checks are PASS or WARN
- `BLOCK` — One or more checks are BLOCK

WARN items are reported for Stage 9 (Review) to address but do not block the implementation gate.

---

## MUST DO

- Always run complexity analysis on all changed files
- Always check for duplication (threshold: 3% of changed lines)
- Always validate Clean Architecture layer dependencies
- Always audit logging for PII leaks
- Always audit error handling: no swallowed exceptions, typed error hierarchies, timeouts on external calls
- Always check diff coverage on changed/new code (threshold: 80% on new lines)
- Always run dead code detection on changed files (non-blocking, informational only)
- Always run the TDD refactor phase after green
- Always re-run tests after every refactoring step
- Always report results as a structured gate report (Step 11)

## MUST NOT DO

- MUST NOT skip the refactor phase — green-without-refactor accumulates debt
- MUST NOT add new features during the refactor phase
- MUST NOT report subjective "code smell" opinions — only measurable violations
- MUST NOT block on minor SOLID issues — flag them for review, don't fail the gate
- MUST NOT duplicate linting checks — defer to the project's linter for style/formatting
- MUST NOT run this on test files — quality gate applies to production code only
- MUST NOT allow empty catch/except blocks — always log, rethrow, or return typed error
- MUST NOT catch generic Exception/Throwable except at top-level handlers (global error middleware, coroutine exception handler)
