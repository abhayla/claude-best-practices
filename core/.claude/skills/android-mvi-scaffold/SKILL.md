---
name: android-mvi-scaffold
description: >
  Scaffold a complete MVI (Model-View-Intent) feature module with Contract (State/Intent/Effect),
  ViewModel, Screen composable, UseCase, Repository, and DI module. Use when creating new feature
  modules in Android projects using MVI architecture.
triggers: "mvi, scaffold feature, create feature, new feature module, android mvi"
allowed-tools: "Read Write Edit Grep Glob Bash"
argument-hint: "<feature name to scaffold, e.g., 'ItemList' or 'UserProfile'>"
---

# MVI Feature Scaffolder

Scaffold a complete MVI feature module following clean architecture conventions.

**Request:** $ARGUMENTS

---

## STEP 1: Analyze Existing Project

Before generating files, understand the project's conventions:

1. Read `build.gradle.kts` or `settings.gradle.kts` for module structure
2. Check for existing feature modules to match package naming and patterns
3. Detect DI framework: Hilt (`@HiltViewModel`, `@Inject`) or Koin (`koinViewModel`, `module {}`)
4. Check for base classes: `BaseViewModel`, `BaseUiState`, or custom contracts

If the project has an existing MVI or MVVM pattern, **follow that pattern** instead of the templates below.

---

## STEP 2: Generate Feature Structure

Create this directory structure for the feature:

```
feature/{featureName}/
    presentation/
        {FeatureName}Screen.kt
        {FeatureName}ViewModel.kt
        {FeatureName}Contract.kt
    domain/
        model/{FeatureName}.kt
        usecase/Get{FeatureName}UseCase.kt
    data/
        repository/{FeatureName}Repository.kt      (interface)
        repository/{FeatureName}RepositoryImpl.kt
    di/
        {FeatureName}Module.kt
```

---

## STEP 3: Generate Contract File

The contract defines the MVI triad — State, Intent, and Effect:

```kotlin
package com.app.feature.{featurename}.presentation

import androidx.compose.runtime.Immutable

@Immutable
data class {FeatureName}State(
    val isLoading: Boolean = true,
    val error: String? = null,
    val data: List<{FeatureName}Item> = emptyList(),
)

sealed interface {FeatureName}Intent {
    data object LoadData : {FeatureName}Intent
    data object Refresh : {FeatureName}Intent
    data class OnItemClick(val id: String) : {FeatureName}Intent
}

sealed interface {FeatureName}Effect {
    data class ShowError(val message: String) : {FeatureName}Effect
    data class NavigateTo(val route: String) : {FeatureName}Effect
}
```

**Rules:**
- State is `@Immutable` data class — all properties are `val`
- Intents represent user actions — named from the user's perspective
- Effects are one-time events (navigation, snackbar, toast) — not persistent state

---

## STEP 4: Generate ViewModel

```kotlin
class {FeatureName}ViewModel(
    private val get{FeatureName}UseCase: Get{FeatureName}UseCase,
) : ViewModel() {

    private val _state = MutableStateFlow({FeatureName}State())
    val state: StateFlow<{FeatureName}State> = _state.asStateFlow()

    private val _effect = Channel<{FeatureName}Effect>(Channel.BUFFERED)
    val effect: Flow<{FeatureName}Effect> = _effect.receiveAsFlow()

    init { handleIntent({FeatureName}Intent.LoadData) }

    fun handleIntent(intent: {FeatureName}Intent) {
        when (intent) {
            is {FeatureName}Intent.LoadData -> loadData()
            is {FeatureName}Intent.Refresh -> loadData()
            is {FeatureName}Intent.OnItemClick -> onItemClick(intent.id)
        }
    }

    private fun loadData() {
        viewModelScope.launch {
            _state.update { it.copy(isLoading = true, error = null) }
            get{FeatureName}UseCase()
                .onSuccess { data -> _state.update { it.copy(isLoading = false, data = data) } }
                .onFailure { e ->
                    _state.update { it.copy(isLoading = false, error = e.message) }
                    _effect.send({FeatureName}Effect.ShowError(e.message ?: "Unknown error"))
                }
        }
    }

    private fun onItemClick(id: String) {
        viewModelScope.launch {
            _effect.send({FeatureName}Effect.NavigateTo("detail/$id"))
        }
    }
}
```

**Rules:**
- Effects use `Channel` (not `SharedFlow`) — guarantees delivery even if no collector at emit time
- State uses `StateFlow` with `.update {}` for thread-safe mutations
- ViewModel never exposes `suspend` functions — only `handleIntent()`
- `when` on Intent must be exhaustive (no `else` branch)

---

## STEP 5: Generate Screen Composable

```kotlin
@Composable
fun {FeatureName}Screen(
    viewModel: {FeatureName}ViewModel = koinViewModel(),  // or hiltViewModel()
    onNavigate: (String) -> Unit = {},
) {
    val state by viewModel.state.collectAsStateWithLifecycle()

    LaunchedEffect(Unit) {
        viewModel.effect.collect { effect ->
            when (effect) {
                is {FeatureName}Effect.ShowError -> { /* show snackbar */ }
                is {FeatureName}Effect.NavigateTo -> onNavigate(effect.route)
            }
        }
    }

    {FeatureName}Content(state = state, onIntent = viewModel::handleIntent)
}

@Composable
private fun {FeatureName}Content(
    state: {FeatureName}State,
    onIntent: ({FeatureName}Intent) -> Unit,
) {
    // TODO: implement UI
}
```

**Rules:**
- Screen composable is the ONLY place that touches the ViewModel
- Content composable is stateless — receives state, emits intents via `onIntent`
- Use `collectAsStateWithLifecycle()` (not `collectAsState()`)
- Effects collected in `LaunchedEffect(Unit)` — one-time setup

---

## STEP 6: Generate Domain + Data Layers

UseCase:
```kotlin
class Get{FeatureName}UseCase(private val repository: {FeatureName}Repository) {
    suspend operator fun invoke(): Result<List<{FeatureName}Item>> {
        return repository.getAll()
    }
}
```

Repository interface (domain layer):
```kotlin
interface {FeatureName}Repository {
    suspend fun getAll(): Result<List<{FeatureName}Item>>
    suspend fun getById(id: String): Result<{FeatureName}Item>
}
```

Repository implementation (data layer):
```kotlin
class {FeatureName}RepositoryImpl(
    private val api: {FeatureName}Api,  // or local data source
) : {FeatureName}Repository {
    override suspend fun getAll(): Result<List<{FeatureName}Item>> = runCatching { api.fetchAll() }
    override suspend fun getById(id: String): Result<{FeatureName}Item> = runCatching { api.fetchById(id) }
}
```

---

## STEP 7: Generate DI Module

**Koin:**
```kotlin
val {featureName}Module = module {
    factory { Get{FeatureName}UseCase(get()) }
    single<{FeatureName}Repository> { {FeatureName}RepositoryImpl(get()) }
    viewModelOf(::{FeatureName}ViewModel)
}
```

**Hilt:**
```kotlin
@Module
@InstallIn(SingletonComponent::class)
abstract class {FeatureName}Module {
    @Binds
    abstract fun bindRepository(impl: {FeatureName}RepositoryImpl): {FeatureName}Repository
}
```

---

## STEP 8: Verify

After generating all files:
1. Check that imports compile: `./gradlew :feature:{featurename}:compileDebugKotlin`
2. Verify no circular dependencies between modules
3. Confirm DI module is registered in the app's DI configuration

---

## MUST DO

- Read existing project conventions before generating (Step 1)
- Use `@Immutable` on State data class
- Use `Channel` for Effects, `StateFlow` for State
- Generate exhaustive `when` blocks (no `else` on sealed types)
- Match existing package name convention
- Generate DI module matching the project's DI framework

## MUST NOT DO

- Generate files without reading existing project patterns first
- Use `SharedFlow` for one-time effects — use `Channel` instead
- Expose `suspend` functions from ViewModel — only `handleIntent()`
- Put framework imports in domain layer
- Skip the DI module — every feature needs one
