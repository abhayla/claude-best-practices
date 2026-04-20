# Scope: global

# Error Handling & Defensive Coding

Universal constraints for surfacing, propagating, and recovering from errors, independent of language or framework. Stack-specific error patterns (FastAPI exception handlers, Android `Result<T>`, Vue error boundaries) extend these — they do not replace them.

## Top-Level MUST NOTs

- MUST NOT swallow exceptions silently — every caught error MUST be logged, re-raised, or transformed into an explicit result value
- MUST NOT continue execution on unrecoverable invalid state — fail at the earliest detection point
- MUST NOT use exceptions for normal control flow — reserve exceptions for exceptional conditions

## Fail Fast

MUST detect and surface errors at the earliest possible point rather than allowing invalid state to propagate. A crash at the root cause is exponentially cheaper to diagnose than a silent corruption discovered hours later.

- Validate preconditions at function entry — reject invalid arguments before doing work
- Assert invariants in long-running loops and recursive calls — catch drift before it compounds
- Prefer crashing a single request over corrupting shared state — let a supervisor restart rather than patch broken data

## No Silent Failures

Every error path MUST be observable. If an error is caught and handled, the handling MUST produce a log entry, metric, or explicit result — never an invisible recovery.

- Empty `catch` / `except` blocks are forbidden — at minimum, log with full stack trace and context
- When transforming exceptions to result types (`Result<T, E>`, `Either<L, R>`), preserve the original cause and stack
- Retries MUST be logged per attempt with the backoff reason — "it worked eventually" hides systemic flakiness

## Explicit over Implicit

Make behavior, dependencies, and error paths explicit rather than relying on side effects or convention. Implicit behavior creates bugs that only manifest under specific execution conditions.

- Return typed result values (`Result`, `Option`, sealed types) instead of `null` / sentinel values when failure is expected
- Declare which exceptions a function can throw (via annotations, docstrings, or effect types) — callers should not discover them at runtime
- Name error variants by failure mode (`NotFound`, `PermissionDenied`, `RateLimited`) — never a generic `Error("something went wrong")`

## Validate at Boundaries

Treat all data crossing a trust boundary as untrusted until validated. Trust boundaries include: user input, external APIs, file I/O, message queues, IPC, database reads of externally-written rows, deserialized data (JSON/YAML/protobuf).

- Validate at the boundary once; internal functions MAY assume validated types
- Use typed schemas at boundaries (language-native types plus a schema validator — Pydantic, Zod, JSON Schema, kotlinx.serialization, etc.) rather than ad-hoc checks
- Reject and log invalid payloads with enough context to diagnose the sender — never silently coerce

## Resource Cleanup

Resources (files, network connections, database transactions, locks, subprocesses, memory buffers) MUST be released deterministically, as close to acquisition as possible. Leaks only manifest under load or after long uptimes — they are expensive to find in production.

- Use language-native scoped-cleanup constructs — `with` (Python), `try-with-resources` (Java/Kotlin), `using` (C#/TypeScript), `defer` (Go), RAII destructors (C++/Rust)
- MUST NOT rely on garbage collection to close external resources — GC is non-deterministic
- Cleanup MUST run on the error path too — wrap acquisition + use in a construct that guarantees release on exception

## Error Messages

Error messages MUST tell the operator what went wrong, where, and what to do next. A message like "Operation failed" is a bug — it hides information the operator needs.

- Include the failing input (redacted if sensitive), the expected value, and the observed value
- Identify the subsystem and the operation (`[db.users.insert] unique constraint violated on email`)
- Avoid leaking secrets, PII, or internal paths in user-facing errors — detailed traces belong in logs, not HTTP responses

## CRITICAL RULES

- MUST NOT write empty `catch` / `except` blocks
- MUST NOT use `null` / `None` as a generic failure signal — return typed results instead
- MUST validate all data crossing a trust boundary before it reaches business logic
- MUST release resources on every exit path — success and failure alike
- MUST include actionable context in every error message — subsystem, operation, input, expected vs. observed
- MUST NOT catch `CancellationException` (Kotlin), `BaseException` (Python), `KeyboardInterrupt` — always rethrow
