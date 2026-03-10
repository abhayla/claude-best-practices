---
paths:
  - "backend/app/models/**/*.py"
  - "backend/app/db/**/*.py"
  - "backend/app/repositories/**/*.py"
  - "backend/alembic/**/*.py"
  - "android/data/src/main/java/com/rasoiai/data/local/**/*.kt"
---

# Database Rules

## PostgreSQL (Backend)
- 5-location model import rule: `models/__init__.py`, `postgres.py` (3 blocks), `conftest.py`
- Always generate Alembic migration after model changes: `alembic revision --autogenerate -m "description"`
- `postgres.py` has connection pool: `pool_size=10`, `max_overflow=20`, `pool_recycle=1800`
- `expire_on_commit=False` and `selectinload()` are required for async
- `firestore.py` is legacy — do not use, do not delete

### Alembic Migrations
8 migrations in `backend/alembic/versions/`: initial schema → meal generation settings → notifications/FCM → recipe rules → AI recipe catalog → recipe rules dedup → email uniqueness → pre-prod hardening. Run `alembic upgrade head` to apply.

### Model Files
13 model files in `backend/app/models/` (plus `__init__.py` re-exporting all). Key locations:
- `FamilyMember` → `user.py` (not separate file)
- `NutritionGoal` → `recipe_rule.py`
- `AiRecipeCatalog` → `ai_recipe_catalog.py`
- `UsageLog` → `usage_log.py`
- `RefreshToken` → `refresh_token.py`

## Room (Android) — Version 11
- 20 entities, 11 DAOs
- Migrations in `RasoiDatabase.kt`: MIGRATION_7_8 through MIGRATION_10_11
- Room stores MealType as uppercase: `BREAKFAST`, `LUNCH`, `DINNER`, `SNACKS`
- Fresh installs seed `known_ingredients` with 40+ Indian cooking ingredients
- Room-only entities (no domain model): `KnownIngredientEntity`, `OfflineQueueEntity`, `CookedRecipeEntity`, `RecentlyViewedEntity`

### Room Patterns
- Use `@Upsert` for insert-or-update operations instead of `@Insert(onConflict=REPLACE)` + `@Update` pairs. `@Upsert` is atomic (Room 2.5+); the separate pair has a race window.
- Every `@TypeConverter` MUST have a unit test with boundary cases (empty list, null, special characters). Incorrect converters cause silent data loss at runtime, not compile time.

### Room DAOs
MealPlan, Recipe, Grocery, Favorite, Collection, Pantry, Stats, RecipeRules, Chat, Notification, OfflineQueue.

### Room Migration History
- `MIGRATION_7_8`: notifications + offline queue
- `MIGRATION_8_9`: recipe rules refactor + cooked recipes
- `MIGRATION_9_10`: known ingredients
- `MIGRATION_10_11`: recreate `meal_plan_items` with proper `id` PK instead of composite PK
