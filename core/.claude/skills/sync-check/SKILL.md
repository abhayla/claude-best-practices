---
name: sync-check
description: >
  Schema drift detector: compares Room entities (Android) with PostgreSQL models (Backend)
  to find mismatches in fields, types, and naming. Also checks EntityMappers and DtoMappers
  for completeness. Use when modifying data models on either platform.
allowed-tools: "Bash Read Grep Glob"
argument-hint: "[--model ModelName] [--full]"
disable-model-invocation: true
---

# Sync Check — Room vs PostgreSQL Schema Drift Detector

Compares Android Room entities with backend PostgreSQL SQLAlchemy models to detect schema drift, missing fields, and mapper gaps.

**Request:** $ARGUMENTS

---

## Input Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `model` | string | all | Check a specific model (e.g., `Recipe`, `MealPlan`) |
| `full` | flag | false | Include mapper analysis (EntityMappers + DtoMappers) |

---

## Model Mapping

These are the known entity pairs between Android and Backend:

| Domain Model | Room Entity (Android) | SQLAlchemy Model (Backend) |
|-------------|----------------------|---------------------------|
| Recipe | RecipeEntity | Recipe |
| MealPlan | MealPlanEntity + MealPlanItemEntity | MealPlan + MealPlanItem |
| GroceryItem | GroceryItemEntity | GroceryItem |
| User | (DataStore prefs) | User |
| FamilyMember | FamilyMemberEntity | FamilyMember (in user.py) |
| RecipeRule | RecipeRuleEntity | RecipeRule |
| NutritionGoal | NutritionGoalEntity | NutritionGoal (in recipe_rule.py) |
| ChatMessage | ChatMessageEntity | ChatMessage |
| Notification | NotificationEntity | Notification |
| Festival | (no local entity) | Festival |
| Stats | StatsEntity | Stats |
| AiRecipeCatalog | (no local entity) | AiRecipeCatalog |

Room-only entities (no backend counterpart): `KnownIngredientEntity`, `OfflineQueueEntity`, `CookedRecipeEntity`, `RecentlyViewedEntity`, `FavoriteEntity`, `CollectionEntity`, `PantryItemEntity`

---

## STEP 1: Extract Room Entity Fields

For each entity, extract column definitions:

```bash
# Find all Room entity files
cd android && grep -rn "@Entity" --include="*.kt" -l src/
```

For each entity file, extract `@ColumnInfo` annotations and field types:

```bash
cd android && grep -E "@ColumnInfo|val |var " src/main/java/com/rasoiai/data/local/entity/*.kt
```

---

## STEP 2: Extract PostgreSQL Model Fields

For each SQLAlchemy model, extract Column definitions:

```bash
cd backend && grep -E "Column\(|relationship\(" app/models/*.py
```

---

## STEP 3: Compare Field-by-Field

For each model pair, compare:

| Check | What to Compare |
|-------|----------------|
| **Field names** | Room column name vs PostgreSQL column name |
| **Field types** | Kotlin type → SQLAlchemy type mapping |
| **Nullability** | `nullable` in Room vs `nullable` in SQLAlchemy |
| **Defaults** | `defaultValue` in Room vs `server_default` in SQLAlchemy |
| **Missing fields** | Fields in one but not the other |

**Type mapping reference:**

| Kotlin (Room) | Python (SQLAlchemy) |
|---------------|-------------------|
| `String` | `Column(String)` or `Column(Text)` |
| `Int` | `Column(Integer)` |
| `Long` | `Column(BigInteger)` |
| `Boolean` | `Column(Boolean)` |
| `Float` / `Double` | `Column(Float)` |
| `String` (UUID) | `Column(UUID)` |
| `Long` (timestamp) | `Column(DateTime)` |
| `List<String>` (JSON) | `Column(JSONB)` |

---

## STEP 4: Check Mappers (if --full)

### EntityMappers (`data/local/mapper/EntityMappers.kt`)

Verify every Room entity field has a corresponding mapping:

```bash
cd android && grep -A 5 "fun.*toDomain\|fun.*toEntity" src/main/java/com/rasoiai/data/local/mapper/EntityMappers.kt
```

### DtoMappers (`data/remote/mapper/DtoMappers.kt`)

Verify every API DTO field maps correctly:

```bash
cd android && grep -A 5 "fun.*toDomain\|fun.*toEntity\|fun.*toDto" src/main/java/com/rasoiai/data/remote/mapper/DtoMappers.kt
```

Check for:
- Fields mapped in Entity but not in DTO (or vice versa)
- Enum mappings that could fail (case sensitivity — Room stores uppercase like `BREAKFAST`)
- Missing null safety handling

---

## STEP 5: Generate Report

**Output Required:**
```
Sync Check Report:
==================

Model: [ModelName]
  Room Entity: [EntityName] ([N] fields)
  PostgreSQL: [ModelName] ([N] fields)

  Matched Fields: [N]
  Mismatched Fields:
    - [field]: Room=[type] vs PG=[type]
  Missing in Room:
    - [field] (PG type: [type])
  Missing in PostgreSQL:
    - [field] (Room type: [type])

  Mapper Coverage (if --full):
    EntityMapper: [N]/[N] fields mapped
    DtoMapper: [N]/[N] fields mapped
    Missing mappings: [list]

Overall Status: IN_SYNC | DRIFT_DETECTED ([N] issues)
```

---

## CRITICAL NOTES

- Room stores enums as UPPERCASE strings (`BREAKFAST`, `LUNCH`, `DINNER`, `SNACKS`)
- DtoMappers must handle case conversion
- `FamilyMember` is defined inside `user.py`, not its own file
- `NutritionGoal` is defined inside `recipe_rule.py`
- Room-only entities (Favorites, Collections, Pantry, etc.) are intentionally local-only
