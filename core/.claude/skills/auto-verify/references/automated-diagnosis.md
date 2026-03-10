# Automated Diagnosis Table

KKB-specific error patterns and their automated diagnosis actions for auto-verify Step 4.

---

## Backend Errors (Python / FastAPI / SQLAlchemy)

| Error Pattern | Automated Action | Rationale |
|---|---|---|
| `AssertionError: assert X == Y` | Check if test expectation outdated after refactoring; compare with actual API response | Common after changing return values or adding fields |
| `ImportError: cannot import name` | Check for circular imports, renamed modules, missing `__init__.py` | Module restructuring often breaks imports |
| `IntegrityError: duplicate key` | Check upsert vs insert logic, unique constraints, test isolation | DB constraint violation — common in concurrent tests |
| `IntegrityError: NOT NULL constraint` | Check model defaults, required fields, migration state | Missing field in test data or new required column |
| `sqlalchemy.exc.MissingGreenlet` | Add `selectinload()` or `joinedload()` for relationship access | Async SQLAlchemy requires explicit eager loading |
| `asyncio.TimeoutError` | Check if Gemini/external API call is blocking event loop | Known KKB issue — Gemini blocks uvicorn ~45s |
| `Timeout` (generic) | Check test timeout settings, mock external services | External API dependencies in test environment |
| `FileNotFoundError` | Check PYTHONPATH, working directory, fixture file paths | Path issues common across Windows/Unix |
| `ModuleNotFoundError` | Check PYTHONPATH prefix, virtual environment activation | Missing `PYTHONPATH=.` in test command |
| `httpx.HTTPStatusError: 401` | Check auth fixture, token generation, test user setup | Auth dependency override may be missing |
| `httpx.HTTPStatusError: 404` | Check route registration, URL path, router prefix | Endpoint may not be registered in `main.py` |
| `httpx.HTTPStatusError: 422` | Check request body schema, Pydantic validation | Request payload doesn't match expected schema |
| `TypeError: unexpected keyword` | Check function signature changes, Pydantic model updates | Constructor params changed but callers not updated |

## Android Errors (Kotlin / Compose / Hilt)

| Error Pattern | Automated Action | Rationale |
|---|---|---|
| `CompilationError` | Check missing constructor params, type mismatches, import changes | Kotlin compilation — often after interface changes |
| `Hilt` / `@Inject` / `MissingBinding` | Run `./gradlew clean :app:kspDebugKotlin` | KSP codegen cache invalidation needed |
| `Room migration` / `Schema mismatch` | Check Room version in `@Database`, verify migration exists | DB schema drift between app and test |
| `IllegalStateException: LifecycleOwner` | Check test setup — use `createComposeRule()` not `createAndroidComposeRule()` | Compose test lifecycle mismatch |
| `AssertionError.*assertIsDisplayed` | Check testTag values, verify UI state is set before assertion | UI element not rendered or wrong testTag |
| `TimeoutException.*waitUntil` | Increase timeout, check if background work completes | Async operations in ViewModel not completing |
| `NoSuchElementException` | Check collection/list population in test state | Empty collections in mock UiState |
| `ClassCastException` | Check DI module bindings, type mapping in fakes | Wrong type bound in test DI configuration |

## Build Errors

| Error Pattern | Automated Action | Rationale |
|---|---|---|
| `Could not resolve dependency` | Check `libs.versions.toml`, run `./gradlew --refresh-dependencies` | Dependency version conflict |
| `Execution failed for task ':app:ksp'` | Run `./gradlew clean :app:kspDebugKotlin` | KSP annotation processor failure |
| `Out of memory` / `GC overhead` | Add `-Xmx` flag, check gradle.properties heap size | Build requires more memory |
| `AAPT: error` | Check XML resources, drawable references, theme attributes | Android resource compilation error |
