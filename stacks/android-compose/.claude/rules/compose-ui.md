---
paths:
  - "android/app/src/main/java/com/rasoiai/app/presentation/**/*.kt"
---

# Compose UI Rules

## Screen Structure
Every screen directory follows: `FeatureScreen.kt` + `FeatureViewModel.kt` + optional `components/` subdirectory.

## ViewModel Pattern
```kotlin
@HiltViewModel
class FeatureViewModel @Inject constructor(
    private val repository: Repository
) : BaseViewModel<FeatureUiState>(FeatureUiState()) {
    // Use updateState {} — provided by BaseViewModel
    // Use Channel<NavigationEvent> for one-time navigation
}
```

## State Management
- Single `UiState` data class per screen implementing `BaseUiState`
- Derived state via `get()` computed properties, not separate StateFlows
- `Resource<T>` sealed class (`Success`, `Error`, `Loading`) in `common/UiState.kt`

## Bottom Navigation
- Screens with bottom nav use `RasoiBottomNavigation(selectedItem, onItemSelected)`
- Items: HOME, GROCERY, CHAT, FAVORITES, STATS
- Adding new items: update `NavigationItem` enum AND `Screen.kt` `bottomNavScreens`

## Test Tags
- Every interactive/assertable element needs `Modifier.testTag(TestTags.CONSTANT)`
- Tags defined in `presentation/common/TestTags.kt` — never use raw strings

## Design System

| Element | Light | Dark |
|---------|-------|------|
| Primary | `#FF6838` (Orange) | `#FFB59C` |
| Secondary | `#5A822B` (Green) | `#A8D475` |
| Background | `#FDFAF4` (Cream) | `#1C1B1F` |

| Token | Value |
|-------|-------|
| Spacing | 8dp grid (4, 8, 16, 24, 32, 48dp) |
| Shapes | Rounded corners (8dp small, 16dp medium, 24dp large) |

## Compose Patterns (Prevent Common Bugs)

**State collection:**
- ALWAYS use `collectAsStateWithLifecycle()`, never `collectAsState()`. The latter continues collecting when the app is backgrounded, wasting CPU/battery. Requires `androidx.lifecycle:lifecycle-runtime-compose`.

**Screen-Route split:**
- NEVER inject `hiltViewModel()` inside a Screen composable — only in the Route composable. Screen composables receive UiState and lambda callbacks only. This keeps screens previewable and testable.

**LaunchedEffect keys:**
- `LaunchedEffect(Unit)` for one-time setup only. Use `LaunchedEffect(someId)` when the effect must restart on id change. NEVER use `LaunchedEffect(true)`.

**Lazy list keys:**
- Every `LazyColumn`/`LazyRow` item MUST specify `key = { item.id }`. Never use list index as key — causes state loss on reorder/insert.

**derivedStateOf:**
- Wrap computed values from state in `remember { derivedStateOf { ... } }`. Direct derivation recalculates on every recomposition; `derivedStateOf` only notifies when the result changes.

**DisposableEffect for cleanup:**
- Use `DisposableEffect` (not `LaunchedEffect`) when registering listeners/callbacks that need explicit release. `DisposableEffect` guarantees `onDispose {}` runs on exit.

## Reference Implementations

| Pattern | Reference | Key Features |
|---------|-----------|--------------|
| Tabs + Bottom Sheets | `presentation/reciperules/` | 2-tab layout (Rules, Nutrition), modal sheets |
| Form-based Settings | `presentation/settings/` | Sections, toggles |
| Bottom Navigation | `presentation/home/` | RasoiBottomNavigation |
| List with Filtering | `presentation/favorites/` | Tab/list pattern |
