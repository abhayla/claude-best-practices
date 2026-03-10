---
paths:
  - "android/**/presentation/**/*.kt"
description: Jetpack Compose UI patterns and conventions.
---

# Compose UI Rules

## Screen Structure
Every screen: `FeatureScreen.kt` + `FeatureViewModel.kt` + optional `components/` subdirectory.

## ViewModel Pattern
```kotlin
@HiltViewModel
class FeatureViewModel @Inject constructor(
    private val repository: Repository
) : BaseViewModel<FeatureUiState>(FeatureUiState()) {
    // Use updateState {} from BaseViewModel
    // Use Channel<NavigationEvent> for one-time navigation
}
```

## State Management
- Single `UiState` data class per screen implementing `BaseUiState`
- Derived state via `get()` properties, not separate StateFlows
- `Resource<T>` sealed class (`Success`, `Error`, `Loading`)

## Test Tags
- Every interactive element needs `Modifier.testTag(TestTags.CONSTANT)`
- Define tags in a central `TestTags.kt` — never use raw strings

## Design System
- Use consistent spacing grid (e.g., 8dp increments)
- Consistent corner radii (small/medium/large)
- Token-based colors from theme, not hardcoded hex values

## Common Anti-Patterns to Avoid
- `collectAsState()` instead of `collectAsStateWithLifecycle()`
- `hiltViewModel()` inside Screen composable
- `LaunchedEffect(true)` — use `LaunchedEffect(Unit)`
- Missing `key` in LazyColumn items
- Direct state derivation instead of `derivedStateOf`
