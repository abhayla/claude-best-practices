# Test Knowledge Base

Persistent, searchable testing knowledge for RasoiAI. Each entry has an ID, date, source, tags, and content. Entries are grouped by category. Append new entries at the end of the relevant category section.

---

## Fixtures (FIX)

### [FIX-001] Backend test fixture selection guide (2026-02-04)
**Source:** backend/tests/CLAUDE.md
**Tags:** #pytest #client #auth #fixture
Use `client` for most tests (pre-authenticated, overrides `get_current_user` to return `test_user`). Use `unauthenticated_client` for testing 401 responses. Use `authenticated_client` for testing real JWT verification flow. Use `db_session` for direct service/repository unit tests.

### [FIX-002] Never duplicate fixtures in subdirectory conftest (2026-02-04)
**Source:** backend/tests/CLAUDE.md
**Tags:** #pytest #conftest #fixture
All standard fixtures (`client`, `unauthenticated_client`, `authenticated_client`, `auth_token`) live in root `conftest.py`. Do NOT re-define them in subdirectory conftest files. For custom setups (e.g., two users), use `make_api_client()` from `tests/api/conftest.py`.

### [FIX-003] Session patching for direct async_session_maker usage (2026-02-04)
**Source:** backend/tests/CLAUDE.md
**Tags:** #pytest #session #patching #sqlalchemy
Both `user_repository.async_session_maker` and `auth_service.async_session_maker` are patched in `make_api_client()`. If you add a new service that calls `async_session_maker` directly (instead of using the `db: AsyncSession` parameter), you must also patch it in `make_api_client()`.

---

## Platform (PLT)

### [PLT-001] SQLite vs PostgreSQL UUID handling (2026-02-04)
**Source:** backend/tests/CLAUDE.md
**Tags:** #sqlite #postgresql #uuid
`conftest.py` registers `sqlite3.register_adapter(uuid.UUID, str)` to handle UUID columns because SQLite doesn't support native UUID comparison. Some PostgreSQL-specific features (array columns, JSON operators) may behave differently in SQLite tests.

### [PLT-002] API 36 emulator has Espresso compatibility issues (2026-02-04)
**Source:** CLAUDE.md troubleshooting
**Tags:** #emulator #api36 #espresso
Use API 34 for local testing. API 36 has Espresso compatibility problems. CI uses API 29. Always test on API 34 locally.

### [PLT-003] Recipe ID type mismatch causes silent 500s (2026-02-21)
**Source:** CLAUDE.md troubleshooting
**Tags:** #postgresql #uuid #recipe #500
Always compare recipe IDs as strings in queries. `uuid.UUID` vs `String(36)` column type mismatch causes silent 500 errors in PostgreSQL.

---

## Timing (TMG)

### [TMG-001] Auth race condition in E2E tests (2026-03-01)
**Source:** CLAUDE.md troubleshooting
**Tags:** #e2e #auth #splash #timing
SplashViewModel has a 2-second delay before checking `phoneAuthClient.isSignedIn`. Tokens must be in DataStore before this fires. `FakePhoneAuthClient` handles this automatically, but custom auth setups need to account for the timing.

### [TMG-002] Auth flow timeout on cold emulator (2026-03-09)
**Source:** J01 journey test failure analysis
**Tags:** #e2e #auth #timeout #emulator #cold-start
On cold emulator, FakePhoneAuth → backend auth → navigation can take >10s. Use 15000ms timeout for `assertNavigatedToOnboarding()` and 10000ms for `waitForGeneratingScreen()`. Default 5000ms is too short for auth-dependent flows. The 2-second SplashViewModel delay + backend HTTP roundtrip + Compose recomposition adds up.

### [TMG-003] Meal generation timeout configuration (2026-03-06)
**Source:** docs/design/Meal-Generation-Algorithm.md
**Tags:** #timeout #gemini #mealgen
Endpoint uses `asyncio.wait_for(180)` in `meal_plans.py`. Previous 120s was too tight for retries + thinking tokens. Gemini AI takes ~30-40s with `response_json_schema` + `thinking_budget=0`. E2E tests use 30-second timeout for waiting.

---

## Flaky (FLK)

### [FLK-001] Use waitUntil in E2E tests, not Thread.sleep (2026-02-04)
**Source:** CLAUDE.md troubleshooting
**Tags:** #e2e #flaky #compose #waituntil
Use `waitUntil {}` blocks in E2E tests for UI state changes. `Thread.sleep()` causes flakiness. See `RetryUtils.kt` for retry patterns at the action level.

### [FLK-002] FullJourneyFlowTest setUp static state interference (2026-03-09)
**Source:** J03 journey test failure analysis
**Tags:** #e2e #auth #static #setup #fulljourney
FullJourneyFlowTest must call `clearAllState()` + `fakePhoneAuthClient.setSignInSuccess()` in `@Before setUp()`. Without this, `FakePhoneAuthClient.initialSignedIn` static state from previous tests persists across JVM, causing splash to skip auth screen. Also must handle both new-user (→Onboarding) and returning-user (→Home) paths since backend user may already be onboarded from previous test runs.

### [FLK-003] Back navigation from Settings sub-screens unreliable (2026-03-09)
**Source:** J03 FullJourneyFlowTest step7 failure
**Tags:** #e2e #navigation #settings #pressback
`uiDevice.pressBack()` from Recipe Rules or other Settings sub-screens doesn't reliably reach Home. Bottom nav is NOT visible on sub-screens. Use multiple pressBack() with fallback checks, or navigate back to Home at the end of each step that enters Settings sub-screens. The MealPlanGenerationFlowTest had the same issue (removed Recipe Rules navigation entirely).

---

## Data (DAT)

### [DAT-001] Sharma Family test profile (2026-02-04)
**Source:** docs/testing/E2E-Testing-Prompt.md
**Tags:** #testdata #sharma #profile #e2e
Standard test family: 3 members (Ramesh 45 DIABETIC/LOW_OIL, Sunita 42 LOW_SALT, Aarav 12 NO_SPICY). Vegetarian + Sattvic. North/South cuisine, Medium spice. Allergies: Peanuts (SEVERE), Cashews (MILD). Dislikes: Karela, Baingan, Mushroom. Weekday 30min, Weekend 60min. Busy: Mon/Wed/Fri.

### [DAT-002] Room stores MealType as uppercase (2026-02-04)
**Source:** CLAUDE.md troubleshooting
**Tags:** #room #enum #mealtype #case
Room stores MealType as uppercase strings: `BREAKFAST`, `LUNCH`, `DINNER`, `SNACKS`. Tests must match this casing when comparing or querying.

---

## ADB (ADB)

### [ADB-001] Do NOT use screencap -d 0 flag (2026-02-22)
**Source:** memory/MEMORY.md
**Tags:** #adb #screencap #emulator #display
`screencap -d 0 -p` fails with "Display Id '0' is not valid" producing 79-byte error files. Use plain `screencap -p` and rely on `post-screenshot-resize.sh` hook for auto-recovery. The hook strips `[Warning] Multiple displays...` text prepended before PNG magic bytes.

### [ADB-002] Screenshots must go to docs/testing/screenshots/ (2026-02-04)
**Source:** CLAUDE.md Rule #3
**Tags:** #adb #screenshots #path
ALL screenshots MUST be saved to `docs/testing/screenshots/`. No exceptions. The folder is gitignored. Use descriptive filenames: `{feature}_{context}.png`. PNG format, limit to 1280x720.

---

## Errors (ERR)

### [ERR-001] MissingGreenlet means eager loading needed (2026-02-04)
**Source:** CLAUDE.md troubleshooting
**Tags:** #sqlalchemy #async #greenlet #eager
MissingGreenlet errors in SQLAlchemy async require `selectinload()` for eager loading. Lazy loading is not supported in async context.

### [ERR-002] Stale .pyc cache causes phantom behavior (2026-02-04)
**Source:** CLAUDE.md troubleshooting
**Tags:** #python #cache #pyc #stale
Backend changes not reflected? Stale `.pyc` cache. Fix: `find backend -name "*.pyc" -delete && find backend -name "__pycache__" -type d -exec rm -rf {} +`

---

## Infrastructure (INF)

### [INF-001] Test Orchestrator breaks E2E state sharing (2026-03-01)
**Source:** CLAUDE.md troubleshooting
**Tags:** #e2e #orchestrator #datastore #state
Test Orchestrator is intentionally disabled. Re-enabling clears DataStore between tests, breaking `BaseE2ETest.backendMealPlanGenerated` state sharing across test classes.

---

## Running (RUN)

### [RUN-001] PYTHONPATH=. required for backend tests (2026-02-04)
**Source:** backend/CLAUDE.md
**Tags:** #pytest #pythonpath #import
Always run backend tests with `PYTHONPATH=. pytest`. Running without it causes import errors. Use `-v` for verbose, `-x` to stop on first failure.

---

## Migration (MIG)

### [MIG-001] 5-location model import rule (2026-02-04)
**Source:** CLAUDE.md
**Tags:** #sqlalchemy #model #import #migration
When adding a new SQLAlchemy model, ALL 5 locations must be updated or tests/migrations silently fail: (1) `app/models/your_model.py`, (2) `app/models/__init__.py`, (3) `app/db/postgres.py` (3 blocks: init_db, create_tables, drop_tables), (4) `tests/conftest.py`, (5) Alembic migration.
