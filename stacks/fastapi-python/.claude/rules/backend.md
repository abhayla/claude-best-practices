---
paths:
  - "backend/**/*.py"
---

# Backend Rules

## Commands
- Always prefix with `PYTHONPATH=.` when running from `backend/`
- Clear stale cache after fixes: `find . -name "*.pyc" -delete && find . -name "__pycache__" -type d -exec rm -rf {} +`

## Adding Models (5 mandatory import locations)
When adding a new SQLAlchemy model, ALL of these must be updated:
1. `app/models/your_model.py` — define the model
2. `app/models/__init__.py` — re-export
3. `app/db/postgres.py` `init_db()` — import
4. `app/db/postgres.py` `create_tables()` — import
5. `app/db/postgres.py` `drop_tables()` — import
6. `tests/conftest.py` — import (so SQLite creates the table)
7. Generate Alembic migration

Items 2-6 are the "5 import locations." Missing any causes silent test/migration failures.

## Model Location Gotchas
- `FamilyMember` → `models/user.py` (not its own file)
- `NutritionGoal` → `models/recipe_rule.py` (not its own file)
- `recipe_rules.py` endpoint has TWO routers (recipe rules + nutrition goals)

## API Structure

12 router files in `app/api/v1/endpoints/`: auth, chat, family_members, festivals, grocery, meal_plans, notifications, photos, recipe_rules, recipes, stats, users. 13 routers total (~44 endpoints). Swagger UI at `/docs` (DEBUG=true only).

**Router gotchas:**
- `recipe_rules.py` defines **two routers**: recipe rules + nutrition goals. Don't create a separate `nutrition_goals.py`.
- `family_members.py` is registered under `/users` prefix — full path is `/api/v1/users/family-members/`.

**Key files with gotchas:**

| File | Why it matters |
|------|----------------|
| `app/db/postgres.py` | Has 3 model import blocks (init_db, create_tables, drop_tables) — must update all 3 when adding models |
| `app/config.py` | Pydantic Settings — env vars, CORS (default `[]`), JWT secret (no default — required), sql_echo, usage limits, Sentry DSN |
| `app/ai/chat_assistant.py` | Tool calling orchestration (`MAX_TOOL_ITERATIONS=5`) — ties Claude API to preference/rule services |
| `app/ai/gemini_client.py` | Google Gemini client wrapper (google-genai SDK). `MODEL_NAME = "gemini-2.5-flash"` — change it here only |
| `app/ai/tools/` | Chat tool definitions (`preference_tools.py`). `ALL_CHAT_TOOLS` — add new tools here AND in `chat_assistant.py` |
| `app/cache/recipe_cache.py` | In-memory recipe cache, warmed on startup via `warm_recipe_cache()` (non-fatal) |
| `app/services/` | 20 service files; all follow same async pattern with `db: AsyncSession` param |
| `app/main.py` | SecurityHeadersMiddleware, rate limiting (slowapi), Sentry init |

## SQLAlchemy Async
- Use `selectinload()` for eager loading — `joinedload`/lazy loading raises `MissingGreenlet`
- `expire_on_commit=False` is required — removing it breaks post-commit attribute access
- Compare recipe IDs as strings — `uuid.UUID` vs `String(36)` mismatch causes 500 errors

## Services Pattern
- Services take `db: AsyncSession` as parameter (not creating own sessions)
- Exception: `auth_service.py` uses `async_session_maker` directly (token rotation/logout) — must be patched in test fixtures
- `family_constraints.py` is shared by both `ai_meal_service.py` AND `recipe_rules.py` endpoint — changes affect both
- `ai_meal_service.py` has a local `UserPreferences` that shadows `app.models.user.UserPreferences`
- Chat context limited to last 6 messages via `ChatRepository.get_context_for_claude(limit=6)`

## AI Module
- Uses `google-genai` SDK (NOT `google-generativeai`) with `client.aio` for native async — do NOT revert
- Model name constant in `gemini_client.py` — change it there only
- When adding chat tools: add definition in `tools/preference_tools.py` AND handling in `chat_assistant.py`

## Meal Generation

AI-powered meal planning using Gemini (`gemini-2.5-flash` via `google-genai` SDK, native async).

**Config files** in `backend/config/`:
- `meal_generation.yaml` - Pairing rules, meal structure
- `reference_data/ingredients.yaml` - Ingredient aliases
- `reference_data/dishes.yaml` - Common dishes with pairings
- `reference_data/cuisines.yaml` - Regional cuisine definitions

**Key concepts:**
| Concept | Description |
|---------|-------------|
| Items per slot | 2 minimum (e.g., Dal + Rice) |
| INCLUDE rule | Forces item into meal slot, paired with complementary item |
| EXCLUDE rule | Replaces only excluded item, keeps its pair |

**Chat Tool Calling:**
| Tool | Description |
|------|-------------|
| `update_recipe_rule` | ADD/REMOVE INCLUDE/EXCLUDE rules |
| `update_allergy` | Manage food allergies |
| `update_dislike` | Manage disliked ingredients |
| `update_preference` | Cooking time, dietary tags, cuisine |

## Startup & Security

**Startup sequence:** `main.py` lifespan: Sentry init (`send_default_pii=False`) → `init_db()` → `warm_recipe_cache()` (non-fatal) → app ready.

**Rate limiting:** `slowapi` with per-endpoint decorators. Endpoints must have `request: Request` as first parameter. Key limits: auth 10/min, chat 30/min, meal generation 5/hr, photo analysis 10/hr.

**Security headers:** `SecurityHeadersMiddleware` adds X-Content-Type-Options, X-Frame-Options, X-XSS-Protection, Referrer-Policy, X-API-Version, Strict-Transport-Security (non-debug only).

## FastAPI Patterns (Prevent Common Bugs)

**No blocking in async routes:**
- Never use blocking I/O in `async def` handlers: no `time.sleep()` (use `await asyncio.sleep()`), no synchronous HTTP (use `httpx.AsyncClient`), no synchronous file reads (use `aiofiles`). One blocking call stalls ALL concurrent requests on the same worker.

**Exception discipline:**
- Services raise domain exceptions (e.g., `UserNotFoundError`, `DuplicateRuleError`). Routers catch domain exceptions and map to `HTTPException`. Never raise `HTTPException` inside a service — services must not know about HTTP.

**No `__future__` annotations in routers:**
- Do NOT add `from __future__ import annotations` to FastAPI router files. This makes type hints strings at runtime (PEP 563), breaking `Annotated + Depends()` schema generation and OpenAPI docs. Safe in non-router files.

## Auth Debug Bypass
- `DEBUG=true` makes `firebase.py` accept `"fake-firebase-token"` for E2E tests
- E2E tests fail against non-debug backend
