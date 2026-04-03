---
name: android-arch
description: >
  Build Android apps with Clean Architecture using Hilt DI, ViewModel + StateFlow,
  offline-first data layer (Room + Retrofit), Kotlin coroutines, and accessibility.
  Use when building, refactoring, or debugging modern Android apps following Google's
  Guide to App Architecture.
allowed-tools: "Bash Read Write Edit Grep Glob"
triggers:
  - android architecture
  - clean architecture
  - viewmodel stateflow
  - room retrofit
  - hilt dependency injection
  - offline-first android
argument-hint: "<feature-name or 'setup' or 'debug' or 'offline-sync'>"
version: "1.0.1"
type: workflow
---

# Android Architecture

Build modern Android applications with Clean Architecture, Hilt DI, offline-first data, and structured concurrency.

**Request:** $ARGUMENTS

---

## Deep-Dive References

For detailed guidance on specific topics, read the relevant reference file:

| Task | Reference File |
|------|----------------|
| Project structure & modules | [modularization.md](references/modularization.md) |
| Architecture layers (UI, Domain, Data) | [architecture.md](references/architecture.md) |
| Jetpack Compose patterns, animations, effects | [compose-patterns.md](references/compose-patterns.md) |
| Navigation3 & type-safe routes | [android-navigation.md](references/android-navigation.md) |
| Testing (unit, integration, screenshot) | [testing.md](references/testing.md) |
| Security (encryption, biometrics, pinning) | [android-security.md](references/android-security.md) |
| Performance & recomposition optimization | [android-performance.md](references/android-performance.md) |
| Material 3 theming & dynamic colors | [android-theming.md](references/android-theming.md) |
| Accessibility & TalkBack | [android-accessibility.md](references/android-accessibility.md) |
| Kotlin idioms & best practices | [kotlin-patterns.md](references/kotlin-patterns.md) |
| Coroutines & Flow deep-dive | [coroutines-patterns.md](references/coroutines-patterns.md) |
| Gradle & build configuration | [gradle-setup.md](references/gradle-setup.md) |
| Dependency management | [dependencies.md](references/dependencies.md) |
| Code quality (Detekt) | [code-quality.md](references/code-quality.md) |
| Code coverage (JaCoCo) | [android-code-coverage.md](references/android-code-coverage.md) |
| Crash reporting (Crashlytics) | [crashlytics.md](references/crashlytics.md) |
| Internationalization & localization | [android-i18n.md](references/android-i18n.md) |
| Notifications & foreground services | [android-notifications.md](references/android-notifications.md) |
| Runtime permissions | [android-permissions.md](references/android-permissions.md) |
| Data sync & offline patterns | [android-data-sync.md](references/android-data-sync.md) |
| Icons, graphics, custom drawing | [android-graphics.md](references/android-graphics.md) |
| StrictMode guardrails | [android-strictmode.md](references/android-strictmode.md) |
| Kotlin delegation patterns | [kotlin-delegation.md](references/kotlin-delegation.md) |
| Design patterns in Kotlin | [design-patterns.md](references/design-patterns.md) |

### Gradle Convention Plugin Templates

Ready-to-use convention plugins in `templates/convention/`. See [QUICK_REFERENCE.md](templates/convention/QUICK_REFERENCE.md) for setup.

### Project Scaffolding Templates

- `templates/libs.versions.toml.template` — Version catalog
- `templates/settings.gradle.kts.template` — Settings with module includes
- `templates/proguard-rules.pro.template` — R8/ProGuard rules
- `templates/detekt.yml.template` — Detekt configuration

## Workflow Decision Tree

**Creating a new project?**
→ Start with `templates/settings.gradle.kts.template` and `templates/libs.versions.toml.template`
→ Copy convention plugins from `templates/convention/` to `build-logic/convention/`
→ Read [modularization.md](references/modularization.md) for structure

**Adding a new feature/module?**
→ Follow patterns in [architecture.md](references/architecture.md)
→ Create Screen + ViewModel + UiState in the feature module

**Building UI screens?**
→ Read [compose-patterns.md](references/compose-patterns.md)
→ Use [android-theming.md](references/android-theming.md) for Material 3

**Setting up navigation?**
→ Read [android-navigation.md](references/android-navigation.md) for Navigation3

**Configuring Gradle?**
→ Use [gradle-setup.md](references/gradle-setup.md) and convention plugin templates

**Debugging or testing?**
→ See [testing.md](references/testing.md) for test strategy
→ See ADB Debugging section below for device testing

---

## STEP 1: Clean Architecture — Layers & Modules

Structure the application into three layers. Dependencies flow strictly inward: UI -> Domain -> Data.

### Layer Responsibilities

| Layer | Components | Depends On |
|-------|-----------|------------|
| **UI (Presentation)** | Activities, Fragments, Composables, ViewModels | Domain only |
| **Domain (Business Logic)** | Use Cases, Domain Models (pure Kotlin) | Repository interfaces (no `android.*` imports) |
| **Data** | Repository implementations, Room DAOs, Retrofit APIs | External sources only |

### Module Structure

```
:app                    # Entry point, wires features together
:core:model             # Shared domain models (pure Kotlin data classes)
:core:data              # Repository implementations, data sources
:core:domain            # Use Cases, Repository interfaces
:core:ui                # Shared Composables, theme, design system
:core:network           # Retrofit setup, interceptors, API definitions
:core:database          # Room database, DAOs, entities
:feature:home           # Feature module — own UI + ViewModel
:feature:settings       # Feature module — depends on :core:domain, :core:ui
```

### Dependency Rules

- Feature modules depend on `:core:domain` and `:core:ui` — NEVER on other feature modules.
- `:core:domain` MUST be pure Kotlin — no Android framework imports.
- `:core:data` implements interfaces defined in `:core:domain`.
- `:app` module wires everything together via Hilt.

---

## STEP 2: Hilt Dependency Injection

Use Hilt for all dependency injection.

### Required Annotations

```kotlin
// Application class
@HiltAndroidApp
class MyApp : Application()

// Activities and Fragments
@AndroidEntryPoint
class MainActivity : ComponentActivity()

// ViewModels — use standard constructor injection
@HiltViewModel
class HomeViewModel @Inject constructor(
    private val getNewsUseCase: GetNewsUseCase
) : ViewModel()
```

### Hilt Modules

```kotlin
@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {
    // Prefer @Binds over @Provides for interface bindings
    @Binds
    abstract fun bindNewsRepository(
        impl: OfflineFirstNewsRepository
    ): NewsRepository
}

@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {
    @Provides
    @Singleton
    fun provideRetrofit(): Retrofit =
        Retrofit.Builder()
            .baseUrl(BuildConfig.API_BASE_URL)
            .addConverterFactory(GsonConverterFactory.create())
            .client(okHttpClient)
            .build()

    @Provides
    @Singleton
    fun provideOkHttpClient(): OkHttpClient =
        OkHttpClient.Builder()
            .addInterceptor(HttpLoggingInterceptor().apply {
                level = HttpLoggingInterceptor.Level.BODY
            })
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(30, TimeUnit.SECONDS)
            .build()
}

@Module
@InstallIn(SingletonComponent::class)
object DatabaseModule {
    @Provides
    @Singleton
    fun provideDatabase(@ApplicationContext context: Context): AppDatabase =
        Room.databaseBuilder(context, AppDatabase::class.java, "app.db")
            .fallbackToDestructiveMigration()
            .build()
}
```

---

## STEP 3: ViewModel & State Management


**Read:** `references/viewmodel-state-management.md` for detailed step 3: viewmodel & state management reference material.

## STEP 4: Offline-First Data Layer


**Read:** `references/offline-first-data-layer.md` for detailed step 4: offline-first data layer reference material.

## STEP 5: Kotlin Coroutines & Structured Concurrency


**Read:** `references/kotlin-coroutines-structured-concurrency.md` for detailed step 5: kotlin coroutines & structured concurrency reference material.

## STEP 6: Accessibility

### Content Descriptions

```kotlin
// Decorative images — hide from screen readers
Image(
    painter = painterResource(R.drawable.banner),
    contentDescription = null  // Decorative
)

// Meaningful images — describe the action or content
IconButton(onClick = { /* delete */ }) {
    Icon(
        Icons.Default.Delete,
        contentDescription = "Delete item"  // Action description
    )
}
```

### Touch Targets

Minimum 48dp touch target for all interactive elements:

```kotlin
IconButton(
    onClick = { /* action */ },
    modifier = Modifier.size(48.dp)  // Minimum 48dp
) {
    Icon(Icons.Default.Star, contentDescription = "Favorite")
}
```

### Contrast & Semantics

- Use `MaterialTheme.colorScheme` — built-in WCAG AA contrast ratios.
- Mark section headings for screen reader navigation:

```kotlin
Text(
    text = "Latest News",
    style = MaterialTheme.typography.headlineMedium,
    modifier = Modifier.semantics { heading() }
)
```

### Focus Management

```kotlin
// Merge child semantics into a single focusable unit
Row(modifier = Modifier.semantics(mergeDescendants = true) { }) {
    Icon(Icons.Default.Info, contentDescription = null)
    Text("Status: Active")
}
```

---

## STEP 7: ADB Debugging

When testing or debugging on an emulator/device via ADB.

### ADB Command Reference

| Action | Command |
|--------|---------|
| UI Dump | `adb exec-out uiautomator dump /dev/tty` |
| Screenshot | `adb exec-out screencap -p > screenshot.png` |
| Tap | `adb shell input tap X Y` |
| Text Input | `adb shell input text "hello"` |
| Back Key | `adb shell input keyevent BACK` |
| Launch App | `adb shell am start -n PACKAGE/ACTIVITY` |
| List Devices | `adb devices` |
| Clear App Data | `adb shell pm clear PACKAGE` |
| Install APK | `adb install -r path/to/app.apk` |
| Logcat Filter | `adb logcat -s TAG:V` |

### ADB Testing Process

1. **Navigate** to the target screen via ADB taps or intent launches.
2. **Dump UI** with `uiautomator dump` to verify expected elements.
3. **Interact** — tap buttons, enter text, press back.
4. **Screenshot** after interaction to verify visual state.
5. **Verify** expected state changes in the UI dump.

### ADB Gotchas

- Compose `testTag()` values do NOT appear in uiautomator XML — search by `text`, `content-desc`, `resource-id`, or `bounds` instead.
- `ExposedDropdownMenu` popups cannot be interacted with via ADB — use backend API to set those values.

---

## Troubleshooting

| Symptom | Likely Cause | Recovery |
|---------|-------------|----------|
| `Hilt_*` class not found | Missing `@HiltAndroidApp` or kapt/ksp not applied | Add `id("dagger.hilt.android.plugin")` to module `build.gradle.kts`; verify `@HiltAndroidApp` on Application class |
| Room compile error `Cannot find setter` | Entity field visibility or naming mismatch | Use `val` for `@PrimaryKey`, ensure field names match column names |
| `StateFlow` not updating UI | Collecting outside lifecycle scope | Use `collectAsStateWithLifecycle()` in Compose or `repeatOnLifecycle` in Views |
| `NetworkOnMainThreadException` | Retrofit call not in IO dispatcher | Ensure repository uses `withContext(Dispatchers.IO)` or suspend functions |
| Recomposition loop | State mutation inside `@Composable` function body | Move state changes to callbacks or `LaunchedEffect` |
| `CancellationException` swallowed | Catch-all `Exception` block without rethrowing | Always rethrow `CancellationException` in catch blocks |
| WorkManager job not executing | Missing network constraint or battery optimization | Check `Constraints`, add `setExpedited()` for critical syncs |
| UI elements not found in ADB dump | Compose `testTag` not visible to uiautomator | Search by `text` or `content-desc` attributes instead |
| Stale data after app restart | Room query not returning Flow | Change DAO return type from `List<T>` to `Flow<List<T>>` |

---

## CRITICAL RULES

### MUST DO

- Structure code into UI / Domain / Data layers with strict dependency direction
- Use Hilt for all dependency injection — `@HiltViewModel`, `@AndroidEntryPoint`, `@Binds`
- Expose UI state via `StateFlow` with sealed interface (Loading / Success / Error)
- Use `collectAsStateWithLifecycle()` in Compose — never plain `collect`
- Make repositories the Single Source of Truth — UI reads from local DB, not network directly
- Return `Flow<T>` from Room DAOs for reactive data
- Inject dispatchers via Hilt — never hardcode `Dispatchers.IO` in ViewModels
- Use `.update { }` for thread-safe StateFlow mutations
- Rethrow `CancellationException` in every catch block
- Set minimum 48dp touch targets on all interactive elements
- Provide meaningful `contentDescription` for non-decorative images and icons
- Handle ALL `UiState` branches — never leave an empty `when` case

### MUST NOT DO

- Access `android.*` APIs in the Domain layer — keep it pure Kotlin
- Use `LiveData` for new code — use `StateFlow` and `SharedFlow` instead
- Assign `MutableStateFlow.value` directly from coroutines — use `.update { }` instead
- Catch `Exception` without rethrowing `CancellationException`
- Call Retrofit from ViewModel directly — route through Repository and UseCase
- Use `GlobalScope` — use `viewModelScope` or inject a supervised scope instead
- Skip error state handling in the UI — always show meaningful error messages
- Hardcode colors or text styles — use `MaterialTheme.colorScheme` and `MaterialTheme.typography`
- Block the main thread with synchronous DB or network calls
- Commit code with unresolved Hilt injection errors — they crash at runtime
