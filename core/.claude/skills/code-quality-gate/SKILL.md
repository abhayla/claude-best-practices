---
name: code-quality-gate
description: >
  Post-implementation code quality enforcement: cyclomatic complexity,
  duplication detection, SOLID checklist, structured logging audit, error
  handling strategy audit, TDD refactor phase, and clean architecture
  layer validation.
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
version: "1.1.0"
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

Verify that all changed code follows consistent, stack-appropriate error handling patterns. Exceptions used for control flow, swallowed errors, and missing error boundaries are the top causes of silent production failures.

### 7.1 Universal Rules (All Stacks)

| Rule | Violation | Fix |
|------|-----------|-----|
| Never swallow errors silently | Empty `catch {}` / `except: pass` / `.catch(() => {})` | Log, rethrow, or return typed error |
| Never catch top-level `Exception`/`Throwable`/`Error` | `catch (Exception e)` / `catch (e: Throwable)` | Catch specific types: `IOException`, `HttpException`, `TimeoutException` |
| Never use exceptions for control flow | `throw` to signal "not found" or "invalid input" | Return `null`, `Result`, `Optional`, or sealed type |
| Always propagate error context | `throw new Error("failed")` with no cause | Include original exception as `cause` parameter |
| Always handle all Result/Either branches | `.getOrNull()` without checking null | Use `when` (Kotlin), `match` (Rust), or `fold`/`map` |
| Timeout every external call | HTTP/gRPC/DB call without timeout | Set explicit timeout per call type |

### 7.2 Detection Commands

```bash
# Python: find bare except / empty except
grep -rn "except:" --include="*.py" src/ | grep -v "except.*Error"
grep -rn "except.*:\s*$" --include="*.py" src/
# Find pass-only handlers
grep -A1 "except" --include="*.py" src/ | grep "pass$"

# Kotlin: find empty catch / catch Throwable / !! usage
grep -rn "catch\s*(.*Throwable" --include="*.kt" src/
grep -rn "catch\s*(.*Exception)" --include="*.kt" src/ | grep -v "IOException\|HttpException\|JsonException\|CancellationException"
grep -B1 -A1 "catch" --include="*.kt" src/ | grep -A1 "{" | grep "}"

# TypeScript/JavaScript: find empty catch / catch without type
grep -rn "catch\s*(" --include="*.ts" --include="*.tsx" --include="*.js" src/
grep -rn "\.catch\(\(\)\s*=>" --include="*.ts" --include="*.tsx" src/

# Find missing timeouts on fetch/axios/http calls
grep -rn "fetch(" --include="*.ts" --include="*.tsx" src/ | grep -v "timeout\|signal\|AbortController"
```

### 7.3 Kotlin / Android Error Handling

| Layer | Pattern | Example |
|-------|---------|---------|
| **Repository** | Return `Result<T>` — wrap external calls in `runCatching` | `suspend fun getUser(id: String): Result<User>` |
| **ViewModel** | Map `Result` to sealed `UiState` | `result.fold(onSuccess = { UiState.Success(it) }, onFailure = { UiState.Error(it.message) })` |
| **Composable** | Exhaustive `when` on sealed state — no `else` branch | `when (state) { is Loading -> ..., is Success -> ..., is Error -> ... }` |
| **Coroutines** | Never catch `CancellationException` — always rethrow | `catch (e: Exception) { if (e is CancellationException) throw e; ... }` |
| **WorkManager** | Map errors to `Result.retry()` or `Result.failure()` | Network errors → retry, validation errors → failure |

**Required sealed types:**

```kotlin
// Domain error hierarchy — NOT generic Exception subclasses
sealed interface AppError {
    data class Network(val message: String, val cause: Throwable? = null) : AppError
    data class NotFound(val entity: String, val id: String) : AppError
    data class Validation(val field: String, val reason: String) : AppError
    data class Auth(val reason: String) : AppError
    data class Server(val code: Int, val message: String) : AppError
}
```

**Anti-patterns to flag:**

```kotlin
// ❌ Using !! (crash on null)
val user = repository.getUser()!!

// ❌ Catching Throwable
try { ... } catch (e: Throwable) { Log.e("TAG", "error") }

// ❌ Swallowing CancellationException
try { delay(1000) } catch (e: Exception) { /* swallowed */ }

// ✅ Correct pattern
val result = runCatching { repository.getUser() }
result.fold(
    onSuccess = { _state.value = UiState.Success(it) },
    onFailure = { _state.value = UiState.Error(it.toAppError()) }
)
```

### 7.4 Python / FastAPI Error Handling

| Layer | Pattern | Example |
|-------|---------|---------|
| **Repository** | Raise domain exceptions, not generic `Exception` | `raise UserNotFoundError(user_id=id)` |
| **Service** | Catch and translate infrastructure exceptions | `except SQLAlchemyError as e: raise RepositoryError(...) from e` |
| **Route handler** | Return HTTP errors via `HTTPException` with detail | `raise HTTPException(status_code=404, detail={"error": "user_not_found", "id": id})` |
| **Global** | Register exception handlers for domain errors | `@app.exception_handler(DomainError)` |
| **Background tasks** | Log + retry, never crash the worker | `try: ... except TransientError: retry() except PermanentError: dead_letter()` |

**Required error hierarchy:**

```python
# Domain errors — inherit from a base, not built-in Exception directly
class AppError(Exception):
    """Base for all domain errors."""
    def __init__(self, message: str, code: str, cause: Exception | None = None):
        super().__init__(message)
        self.code = code
        self.__cause__ = cause

class NotFoundError(AppError): ...
class ValidationError(AppError): ...
class AuthError(AppError): ...
class ExternalServiceError(AppError): ...
```

**Anti-patterns to flag:**

```python
# ❌ Bare except
try: ... except: pass

# ❌ Catching Exception without re-raising or logging
try: ... except Exception: return None

# ❌ String-only error messages with no machine-readable code
raise HTTPException(status_code=400, detail="something went wrong")

# ✅ Correct pattern
try:
    user = await user_repo.get(user_id)
except UserNotFoundError:
    raise HTTPException(status_code=404, detail={"error": "user_not_found", "user_id": user_id})
except RepositoryError as e:
    logger.error("repository_failure", user_id=user_id, exc_info=e)
    raise HTTPException(status_code=500, detail={"error": "internal_error"})
```

### 7.5 TypeScript / React / Next.js Error Handling

| Layer | Pattern | Example |
|-------|---------|---------|
| **API client** | Return typed result objects, not thrown errors | `async function getUser(id): Promise<Result<User, ApiError>>` |
| **React components** | Error boundaries for render failures | `<ErrorBoundary fallback={<ErrorPage />}>` |
| **Server actions / API routes** | Return `{ data, error }` shape — never throw across network boundary | `return { data: null, error: { code: "NOT_FOUND", message: "..." } }` |
| **Async operations** | Always handle `.catch()` or use try/catch in async functions | Never leave unhandled promise rejections |
| **Forms** | Field-level + form-level error state | `const [errors, setErrors] = useState<Record<string, string>>({})` |

**Required Result type:**

```typescript
// Discriminated union — forces callers to check before accessing data
type Result<T, E = AppError> =
  | { ok: true; data: T }
  | { ok: false; error: E };

interface AppError {
  code: string;       // machine-readable: "NOT_FOUND", "VALIDATION_ERROR"
  message: string;    // human-readable
  field?: string;     // for validation errors
  cause?: unknown;    // original error
}
```

**Error boundary pattern (React):**

```tsx
// Every major route/feature should have its own error boundary
class ErrorBoundary extends React.Component<Props, State> {
  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }
  componentDidCatch(error: Error, info: ErrorInfo) {
    reportError(error, info); // Send to error reporting service
  }
  render() {
    if (this.state.hasError) return this.props.fallback;
    return this.props.children;
  }
}
```

**Anti-patterns to flag:**

```typescript
// ❌ Unhandled promise
fetchData(); // no .catch(), no await in try/catch

// ❌ Throwing across API boundary
export async function GET() { throw new Error("not found"); }

// ❌ Generic catch with no action
try { ... } catch (e) { console.log(e); }

// ✅ Correct pattern
const result = await getUser(id);
if (!result.ok) {
  if (result.error.code === "NOT_FOUND") return notFound();
  return NextResponse.json({ error: result.error }, { status: 500 });
}
return NextResponse.json({ data: result.data });
```

### 7.6 Cross-Stack Patterns

#### Timeout Strategy

| Call Type | Default Timeout | Retry |
|-----------|----------------|-------|
| HTTP API call | 10s | 3x with exponential backoff |
| Database query | 5s | 1x (connection pool handles reconnect) |
| File I/O | 30s | No retry |
| gRPC call | 5s | 3x with backoff |
| Third-party API | 15s | 2x with backoff, then circuit break |

#### Circuit Breaker (for external dependencies)

Track failure rate per external dependency. When failures exceed threshold:
1. **Closed** (normal) → requests pass through
2. **Open** (failures > threshold) → fail fast, return cached/fallback response
3. **Half-open** (after cooldown) → allow one probe request to test recovery

#### Error Reporting Checklist

- [ ] All unhandled exceptions are reported to error tracking (Sentry, Crashlytics, etc.)
- [ ] Error reports include: stack trace, request context, user context (anonymized), environment
- [ ] Error grouping is configured (by exception type + location, not message string)
- [ ] Alert thresholds are set for new error types and error rate spikes

### 7.7 Audit Checklist

For each changed file, verify:

- [ ] No empty catch/except blocks
- [ ] No generic `Exception`/`Throwable`/`Error` catches (except at top-level handlers)
- [ ] Domain errors use typed hierarchy (sealed class/union), not generic exceptions
- [ ] Error context is preserved (cause chaining)
- [ ] All external calls have explicit timeouts
- [ ] All `Result`/`Either` types are handled exhaustively (no `.get()` without checking)
- [ ] React components near data-fetching boundaries have error boundaries
- [ ] API responses use structured error format (`{ code, message }`)
- [ ] No PII in error messages or stack traces sent to clients
- [ ] Async/coroutine error propagation is correct (no swallowed `CancellationException`, no unhandled promise rejections)

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

Run mutation testing on changed files to validate that the test suite catches real bugs, not just achieves line coverage.

### 8.5.1 Detect Mutation Testing Tool

| Stack | Tool | Detection |
|-------|------|-----------|
| Python | mutmut | `pip show mutmut` or `mutmut` in `pyproject.toml` / `requirements*.txt` |
| JavaScript/TS | Stryker | `npx stryker --version` or `@stryker-mutator/core` in `package.json` |

If the tool is not installed, install it:

```bash
# Python
pip install mutmut

# JavaScript/TypeScript
npx stryker init
```

### 8.5.2 Run Mutation Testing on Changed Files

Scope mutation testing to files changed in the current branch to keep execution time reasonable:

**Python (mutmut):**
```bash
# Get changed source files (exclude tests)
CHANGED=$(git diff --name-only origin/main...HEAD -- '*.py' | grep -v test)

# Run mutmut on each changed file
for f in $CHANGED; do
  mutmut run --paths-to-mutate="$f" 2>&1
done

# View results
mutmut results
```

**JavaScript/TypeScript (Stryker):**
```bash
# Get changed source files (exclude tests)
CHANGED=$(git diff --name-only origin/main...HEAD -- '*.ts' '*.tsx' '*.js' | grep -v test | grep -v spec)

# Run Stryker with file-level scope
npx stryker run --mutate "$CHANGED"
```

### 8.5.3 Evaluate Mutation Score

Calculate the mutation score: `killed mutants / total mutants * 100`.

| Mutation Score | Rating | Gate Action |
|---------------|--------|-------------|
| >= 80% | Excellent | PASS — tests effectively catch bugs |
| 60-79% | Acceptable | PASS with WARNING — review surviving mutants |
| 40-59% | Weak | WARN — tests exist but miss many real bugs |
| < 40% | Inadequate | BLOCK — test suite provides false confidence |

### 8.5.4 Report Surviving Mutants

For each surviving mutant (mutation not caught by tests):

```markdown
## Mutation Testing Report

**Tool:** mutmut / Stryker
**Files tested:** <count>
**Total mutants:** <count>
**Killed:** <count> | **Survived:** <count> | **Timeout:** <count>
**Mutation score:** <percentage>%

### Surviving Mutants (top priority)

| File | Line | Mutation | Why It Survived |
|------|------|----------|-----------------|
| src/domain/<module>.py | 45 | Changed `>` to `>=` | No boundary test for threshold value |
| src/services/<module>.py | 112 | Removed return statement | No test asserts the return value |
```

For each surviving mutant, recommend a specific test to add. If the mutation is equivalent (does not change observable behavior), document it as such.

### 8.5.5 CI Integration Note

For CI pipelines, add mutation testing as a non-blocking check initially. Once the team baseline is established, enforce the threshold:

```yaml
# GitHub Actions example
- name: Mutation testing
  run: |
    mutmut run --paths-to-mutate=src/
    SCORE=$(mutmut results | grep -oP '\d+(?=% killed)')
    if [ "$SCORE" -lt 40 ]; then echo "BLOCK: mutation score $SCORE% < 40%"; exit 1; fi
    if [ "$SCORE" -lt 60 ]; then echo "WARN: mutation score $SCORE% < 60%"; fi
```

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

## STEP 10: Quality Report

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
| Refactoring | ✅ Done | 3 extract-method refactorings applied |

### Gate Decision
- **PASS** — All critical checks pass, 1 minor issue flagged for review
- **BLOCK** — N critical issues must be resolved before merge

### Issues to Address
1. [Minor] `src/presentation/user_handler.py:12` — imports from infrastructure directly (DIP)
   **Fix:** Inject `UserRepository` via constructor
```

## STEP 11: Structured Output

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
- Always run the TDD refactor phase after green
- Always re-run tests after every refactoring step
- Always report results as a structured gate report (Step 10)

## MUST NOT DO

- MUST NOT skip the refactor phase — green-without-refactor accumulates debt
- MUST NOT add new features during the refactor phase
- MUST NOT report subjective "code smell" opinions — only measurable violations
- MUST NOT block on minor SOLID issues — flag them for review, don't fail the gate
- MUST NOT duplicate linting checks — defer to the project's linter for style/formatting
- MUST NOT run this on test files — quality gate applies to production code only
- MUST NOT allow empty catch/except blocks — always log, rethrow, or return typed error
- MUST NOT catch generic Exception/Throwable except at top-level handlers (global error middleware, coroutine exception handler)
