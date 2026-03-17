# Error Handling Strategy Audit — Reference

Extracted from `/code-quality-gate` Step 7 for size management.
This file is loaded on-demand when Step 7 executes.

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
