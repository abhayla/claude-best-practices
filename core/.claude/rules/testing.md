---
paths:
  - "backend/tests/**/*.py"
  - "android/app/src/test/**/*.kt"
  - "android/app/src/androidTest/**/*.kt"
---

# Testing Rules

## Test Distribution

| Platform | Tests (approx.) | Framework |
|----------|-----------------|-----------|
| Backend | ~538 | pytest |
| Android Unit | ~580 | JUnit + MockK |
| Android UI | ~750+ | Compose UI Testing |
| Android E2E | ~67+ | Compose UI Testing + Hilt + Real API |

*Run `PYTHONPATH=. pytest --collect-only -q` (backend) or `./gradlew test` (Android) for current totals.*

## Backend Test Fixtures
| Fixture | Use when |
|---------|----------|
| `client` | Most tests — pre-authenticated endpoint calls |
| `unauthenticated_client` | Testing 401 responses |
| `authenticated_client` | Testing actual JWT verification flow |
| `db_session` | Direct service/repository unit tests |

- 4 pre-existing failures in `test_auth.py` are known — don't try to fix the global auth override
- New models MUST be imported in `conftest.py` or SQLite won't create the table
- `pytest.ini` has `asyncio_mode = "auto"` — async tests work without explicit marks
- All backend tests in `backend/tests/`, named `test_{feature}.py` (43 test files)
- Some files use class-based test organization (e.g., `test_ai_meal_service.py`, `test_chat_api.py`)

## Android Unit Tests
- Use `TestDispatcherRule` for coroutine tests
- Use `Fake*Repository` classes (in-memory implementations)
- JUnit 5 with `useJUnitPlatform()`
- Located in `app/src/test/java/com/rasoiai/app/presentation/`

## Android UI Tests

Tests use **Compose UI Testing** (not Espresso). Located in `app/src/androidTest/`.

| Test Type | Pattern | Purpose |
|-----------|---------|---------|
| UI Tests | `*ScreenTest.kt` | Test composable with mock UiState |
| Integration Tests | `*IntegrationTest.kt` | Full app with Hilt DI |
| E2E Tests | `*FlowTest.kt` | Complete user flows |

## E2E Test Infrastructure

**Key files** in `app/src/androidTest/java/com/rasoiai/app/e2e/`:

| File | Purpose |
|------|---------|
| `base/BaseE2ETest.kt` | Base class with Hilt setup, meal plan generation |
| `base/ComposeTestExtensions.kt` | Compose test extension functions |
| `base/TestDataFactory.kt` | Test data creation helpers |
| `util/BackendTestHelper.kt` | Backend API calls with retry |
| `di/FakePhoneAuthClient.kt` | Fake auth (returns `fake-firebase-token`) |
| `robots/` | Robot pattern classes (HomeRobot, GroceryRobot, etc.) |
| `rules/RetryRule.kt` | JUnit rule for retrying flaky tests |
| `E2ETestSuite.kt` | Test suite runner (runs CoreDataFlowTest first) |
| `presentation/common/TestTags.kt` | All semantic test tags |

**E2E backend URL:** `http://10.0.2.2:8000` (Android emulator maps `10.0.2.2` → host `localhost`).

**E2E auth bypass:** `FakePhoneAuthClient` sends `"fake-firebase-token"` to backend (`DEBUG=true` required). See `android/app/src/androidTest/CLAUDE.md` for full auth flow details.

## Android E2E Tests
- Extend `BaseE2ETest`, use Robot pattern
- `CoreDataFlowTest` runs first in `E2ETestSuite` — sets up auth state for all others
- Backend must run at `http://10.0.2.2:8000` with `DEBUG=true`
- `setUpAuthenticatedState()` for tests needing Home screen
- `setUpAuthenticatedStateWithoutMealPlan()` to skip Gemini AI call
- `RetryRule` is disabled (maxRetries=0) — use `RetryUtils` for action-level retries
- 2-second Splash timing: auth tokens must be in DataStore before SplashViewModel checks

## Test Documentation
- Each test file needs KDoc/docstring header: `/** Requirement: #XX - Description */`
- E2E tests go in `e2e/flows/`, UI tests in `presentation/`
