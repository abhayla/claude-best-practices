---
paths:
  - "android/**/*.kt"
  - "android/**/*.kts"
  - "android/**/*.xml"
---

# Android Rules

## Build & Run
- All Gradle commands run from `android/` directory using `./gradlew` (Unix syntax, not `.\gradlew`)
- Never hardcode dependency versions in module `build.gradle.kts` — use `libs.versions.*` from `gradle/libs.versions.toml`
- Module-level `repositories {}` blocks are forbidden (`FAIL_ON_PROJECT_REPOS`) — add repos in `settings.gradle.kts` only

## Architecture
- ViewModels extend `BaseViewModel<T : BaseUiState>` — use `updateState {}` not raw `_uiState.update {}`
- Navigation routes: define in `Screen.kt` only, use `createRoute()` helpers, never construct route strings manually
- All features must be offline-first: Room is source of truth, sync to backend when online
- Use `NetworkMonitor.isOnline` to check connectivity before API calls

## Navigation Routes

Routes with arguments use `createRoute()` helper in `presentation/navigation/Screen.kt`:

| Group | Screens |
|-------|---------|
| Auth flow | Splash, Auth, Onboarding |
| Main (bottom nav) | Home, Grocery, Chat (`?context`), Favorites, Stats |
| Main (other) | Settings, Notifications |
| Detail | RecipeDetail (`{recipeId}`), CookingMode (`{recipeId}`) |
| Feature | Pantry, RecipeRules, Achievements |
| Settings sub-screens | DietaryRestrictions, DislikedIngredients, CuisinePreferences, SpiceLevelSettings, CookingTimeSettings, FamilyMembersSettings, NotificationSettings, UnitsSettings, EditProfile, FriendsLeaderboard, ConnectedAccounts |

## Domain Models

Located in `domain/src/main/java/com/rasoiai/domain/model/`:

| Model | Key Fields |
|-------|-----------|
| `Recipe` | id, name, cuisineType, dietaryTags, prepTimeMinutes, ingredients, instructions |
| `MealPlan` | id, weekStartDate, weekEndDate, days |
| `MealPlanDay` | date, breakfast, lunch, dinner, snacks, festival |
| `RecipeRule` | id, type, action, targetId, frequency, enforcement, mealSlot |
| `NutritionGoal` | id, foodCategory (FoodCategory enum), weeklyTarget, currentProgress, enforcement (RuleEnforcement), isActive |
| `FamilyMember` | id, name, type (MemberType enum), age, specialNeeds (List\<SpecialDietaryNeed\>) |
| `AiRecipeCatalog` | id, display_name, normalized_name, dietary_tags, cuisine, usage_count |

**Key Enums:**
- `DietaryTag` (Recipe): VEGETARIAN, NON_VEGETARIAN, VEGAN, JAIN, SATTVIC, HALAL, EGGETARIAN
- `PrimaryDiet` (User): VEGETARIAN, EGGETARIAN, NON_VEGETARIAN
- `CuisineType`: NORTH, SOUTH, EAST, WEST
- `MealType`: BREAKFAST, LUNCH, SNACKS, DINNER
- `RuleAction`: INCLUDE, EXCLUDE
- `RuleEnforcement`: REQUIRED, PREFERRED
- `MemberType`: ADULT, CHILD, SENIOR
- `SpecialDietaryNeed`: DIABETIC, LOW_OIL, NO_SPICY, SOFT_FOOD, LOW_SALT, HIGH_PROTEIN, LOW_CARB
- `FoodCategory`: GREEN_LEAFY, CITRUS_VITAMIN_C, IRON_RICH, HIGH_PROTEIN, CALCIUM_RICH, FIBER_RICH, OMEGA_3, ANTIOXIDANT

**Room-only entities** (no domain model counterpart):
`KnownIngredientEntity`, `OfflineQueueEntity`, `CookedRecipeEntity`, `RecentlyViewedEntity`

## Coroutines
- Every coroutine in a ViewModel MUST use `viewModelScope.launch {}`. Never use `GlobalScope` or manual `CoroutineScope` — `viewModelScope` auto-cancels on nav pop, preventing leaks.

## Compose
- Use `TestTags` constants from `presentation/common/TestTags.kt` for all `testTag()` modifiers — UI tests break if tags are missing
- `RasoiBottomNavigation` lives in `home/components/`, not `common/`
- Adding a bottom-nav screen requires updating both `Screen.kt` AND the `NavigationItem` enum

## Reference Implementations

| Pattern | Reference | Key Features |
|---------|-----------|--------------|
| Tabs + Bottom Sheets | `presentation/reciperules/` | 2-tab layout (Rules, Nutrition), modal sheets |
| Form-based Settings | `presentation/settings/` | Sections, toggles |
| Bottom Navigation | `presentation/home/` | RasoiBottomNavigation |
| List with Filtering | `presentation/favorites/` | Tab/list pattern |

## India-Specific Domain Knowledge

| Aspect | Details |
|--------|---------|
| **Dietary Tags** | JAIN (no root vegetables), SATTVIC (no onion/garlic) |
| **Cuisine Zones** | NORTH, SOUTH, EAST, WEST with distinct ingredients |
| **Measurements** | Support metric and traditional: katori (bowl), chammach (spoon) |
| **Family Size** | 3-8 members, multi-generational support |

## Testing
- Unit tests use JUnit 5 (`useJUnitPlatform()`), instrumented tests use JUnit 4 rules — don't mix
- Custom test runner: `com.rasoiai.app.HiltTestRunner`
- Emulator: API 34 locally (API 36 has Espresso issues, CI uses API 29)
- `animationsDisabled = true` is set intentionally for test stability

## Do Not Remove
- `androidx.tracing:tracing:1.2.0` pin — fixes `NoSuchMethodError: forceEnableAppTracing`
- `applicationIdSuffix` comment-out — matches Firebase config
- Test Orchestrator disabled state — re-enabling breaks Compose isolation
