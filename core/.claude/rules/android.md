---
paths:
  - "android/**/*.kt"
  - "android/**/*.kts"
  - "android/**/*.xml"
description: Android development rules for Kotlin + Jetpack Compose projects.
---

# Android Rules

## Build & Run
- All Gradle commands from `android/` directory using `./gradlew` (Unix syntax)
- Never hardcode dependency versions — use `libs.versions.*` from `gradle/libs.versions.toml`
- Module-level `repositories {}` blocks are forbidden — use `settings.gradle.kts`

## Architecture
- ViewModels extend a base ViewModel class with `updateState {}` helper
- Navigation routes: define in a central `Screen.kt`, use `createRoute()` helpers
- Offline-first: Room is source of truth, sync to backend when online
- Check connectivity before API calls

## Coroutines
- Use `viewModelScope.launch {}` in ViewModels — never `GlobalScope`
- `viewModelScope` auto-cancels on navigation pop, preventing leaks

## Compose Patterns
- `collectAsStateWithLifecycle()` (not `collectAsState()`) — saves battery when backgrounded
- Screen-Route split: `hiltViewModel()` only in Route composable
- `LaunchedEffect(Unit)` for one-time setup, `LaunchedEffect(key)` for key-dependent effects
- Every `LazyColumn`/`LazyRow` item needs `key = { item.id }`
- Use `derivedStateOf` for computed values
- `DisposableEffect` for cleanup (listeners, callbacks)

## Testing
- Unit tests: JUnit 5 with `useJUnitPlatform()`
- Instrumented tests: JUnit 4 rules — don't mix with JUnit 5
- Use API 34 emulator for local testing
- `animationsDisabled = true` for test stability
