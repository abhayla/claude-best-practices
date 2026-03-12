---
name: android-arch
description: >
  Android Clean Architecture with Hilt DI, ViewModel + StateFlow, offline-first data layer
  (Room + Retrofit), Kotlin coroutines/concurrency, accessibility, and ADB debugging.
  Use for building, refactoring, or debugging modern Android apps following Google's
  Guide to App Architecture.
allowed-tools: "Bash Read Write Edit Grep Glob"
triggers: "android architecture, clean architecture, viewmodel, stateflow, room, retrofit, repository pattern, kotlin coroutines, offline-first, hilt, android debug"
argument-hint: "<feature-name or 'setup' or 'debug' or 'offline-sync'>"
---

# Android Architecture

Build modern Android applications with Clean Architecture, Hilt DI, offline-first data, and structured concurrency.

**Request:** $ARGUMENTS

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

### UI State with StateFlow

```kotlin
// Sealed interface for exhaustive when-expressions
sealed interface HomeUiState {
    data object Loading : HomeUiState
    data class Success(val items: List<NewsItem>) : HomeUiState
    data class Error(val message: String) : HomeUiState
}

@HiltViewModel
class HomeViewModel @Inject constructor(
    private val getNewsUseCase: GetNewsUseCase
) : ViewModel() {

    // Private mutable, public read-only
    private val _uiState = MutableStateFlow<HomeUiState>(HomeUiState.Loading)
    val uiState: StateFlow<HomeUiState> = _uiState.asStateFlow()

    // One-off events (toasts, navigation) — replay = 0 prevents re-triggering
    private val _uiEvent = MutableSharedFlow<HomeUiEvent>(replay = 0)
    val uiEvent: SharedFlow<HomeUiEvent> = _uiEvent.asSharedFlow()

    init {
        loadNews()
    }

    fun loadNews() {
        viewModelScope.launch {
            _uiState.update { HomeUiState.Loading }
            getNewsUseCase()
                .catch { e -> _uiState.update { HomeUiState.Error(e.message ?: "Unknown error") } }
                .collect { news -> _uiState.update { HomeUiState.Success(news) } }
        }
    }

    fun onItemClicked(id: String) {
        viewModelScope.launch {
            _uiEvent.emit(HomeUiEvent.NavigateToDetail(id))
        }
    }
}
```

### Collecting State in Compose

```kotlin
@Composable
fun HomeScreen(viewModel: HomeViewModel = hiltViewModel()) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    // Collect one-off events
    val lifecycleOwner = LocalLifecycleOwner.current
    LaunchedEffect(lifecycleOwner) {
        lifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
            viewModel.uiEvent.collect { event ->
                when (event) {
                    is HomeUiEvent.NavigateToDetail -> { /* navigate */ }
                    is HomeUiEvent.ShowSnackbar -> { /* show snackbar */ }
                }
            }
        }
    }

    when (val state = uiState) {
        is HomeUiState.Loading -> LoadingIndicator()
        is HomeUiState.Success -> NewsList(items = state.items)
        is HomeUiState.Error -> ErrorMessage(message = state.message, onRetry = viewModel::loadNews)
    }
}
```

### State Update Rules

- Use `.update { }` on MutableStateFlow for thread-safe updates — NEVER assign `.value` directly from coroutines.
- Use `sealed interface` (not `sealed class`) for UiState — enables exhaustive `when` without `else`.
- Handle ALL states (Loading, Success, Error) in the UI — never leave a `when` branch empty.

---

## STEP 4: Offline-First Data Layer

### Repository as Single Source of Truth

```kotlin
class OfflineFirstNewsRepository @Inject constructor(
    private val newsDao: NewsDao,
    private val newsApi: NewsApi,
    @IoDispatcher private val ioDispatcher: CoroutineDispatcher
) : NewsRepository {

    // Expose local DB as SSOT — UI always reads from here
    override fun getNewsStream(): Flow<List<News>> = newsDao.getAllNews()

    // Stale-While-Revalidate: show local immediately, refresh in background
    override suspend fun refreshNews(): Result<Unit> = withContext(ioDispatcher) {
        runCatching {
            val remoteNews = newsApi.fetchLatest()
            newsDao.upsertAll(remoteNews.map { it.toEntity() })
        }
    }
}
```

### Room Entities & DAOs

```kotlin
@Entity(tableName = "news")
data class NewsEntity(
    @PrimaryKey val id: String,
    val title: String,
    val content: String,
    @ColumnInfo(name = "updated_at") val updatedAt: Long
)

@Dao
interface NewsDao {
    @Query("SELECT * FROM news ORDER BY updated_at DESC")
    fun getAllNews(): Flow<List<NewsEntity>>  // Returns Flow for reactive updates

    @Upsert
    suspend fun upsertAll(news: List<NewsEntity>)

    @Query("DELETE FROM news WHERE id = :id")
    suspend fun deleteById(id: String)
}
```

### Retrofit API Definitions

```kotlin
interface NewsApi {
    @GET("news")
    suspend fun fetchLatest(): List<NewsDto>

    @GET("news/{id}")
    suspend fun getById(@Path("id") id: String): NewsDto

    @GET("news/search")
    suspend fun search(
        @Query("q") query: String,
        @Query("page") page: Int = 1
    ): PaginatedResponse<NewsDto>

    @POST("news")
    suspend fun create(@Body request: CreateNewsRequest): NewsDto

    @PUT("news/{id}")
    suspend fun update(
        @Path("id") id: String,
        @Body request: UpdateNewsRequest
    ): NewsDto
}
```

### Error Handling with runCatching

```kotlin
suspend fun fetchSafely(): Result<List<News>> = runCatching {
    newsApi.fetchLatest().map { it.toDomain() }
}

// In ViewModel
viewModelScope.launch {
    repository.fetchSafely()
        .onSuccess { news -> _uiState.update { HomeUiState.Success(news) } }
        .onFailure { e -> _uiState.update { HomeUiState.Error(e.message ?: "Network error") } }
}
```

### Outbox Pattern for Writes

For offline write support, save changes locally and sync later with WorkManager:

```kotlin
// 1. Save locally with "unsynced" flag
suspend fun createDraft(news: News) {
    newsDao.insert(news.toEntity().copy(syncStatus = SyncStatus.PENDING))
    enqueueSyncWork()
}

// 2. Schedule sync via WorkManager
private fun enqueueSyncWork() {
    val request = OneTimeWorkRequestBuilder<SyncWorker>()
        .setConstraints(Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED)
            .build())
        .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 30, TimeUnit.SECONDS)
        .build()
    workManager.enqueueUniqueWork("sync", ExistingWorkPolicy.REPLACE, request)
}
```

---

## STEP 5: Kotlin Coroutines & Structured Concurrency

### Dispatcher Injection

```kotlin
// Define qualifier annotations
@Qualifier @Retention(AnnotationRetention.BINARY) annotation class IoDispatcher
@Qualifier @Retention(AnnotationRetention.BINARY) annotation class DefaultDispatcher

// Provide in Hilt module
@Module
@InstallIn(SingletonComponent::class)
object DispatcherModule {
    @Provides @IoDispatcher fun provideIoDispatcher(): CoroutineDispatcher = Dispatchers.IO
    @Provides @DefaultDispatcher fun provideDefaultDispatcher(): CoroutineDispatcher = Dispatchers.Default
}
```

### Coroutine Patterns

```kotlin
// Parallel loading with async
viewModelScope.launch {
    val newsDeferred = async { repository.getNews() }
    val weatherDeferred = async { repository.getWeather() }
    val news = newsDeferred.await()
    val weather = weatherDeferred.await()
    _uiState.update { HomeUiState.Success(news, weather) }
}

// Lifecycle-safe collection in Fragment/Activity
lifecycleScope.launch {
    repeatOnLifecycle(Lifecycle.State.STARTED) {
        viewModel.uiState.collect { state ->
            updateUI(state)
        }
    }
}
```

### CancellationException Rule

ALWAYS rethrow `CancellationException` — swallowing it breaks structured concurrency:

```kotlin
try {
    riskyOperation()
} catch (e: CancellationException) {
    throw e  // MUST rethrow
} catch (e: Exception) {
    handleError(e)
}
```

### Testing Coroutines

```kotlin
@Test
fun `loadNews emits Success state`() = runTest {
    val fakeRepo = FakeNewsRepository(testNews)
    val viewModel = HomeViewModel(GetNewsUseCase(fakeRepo))

    viewModel.uiState.test {
        assertEquals(HomeUiState.Loading, awaitItem())
        assertEquals(HomeUiState.Success(testNews), awaitItem())
        cancelAndIgnoreRemainingEvents()
    }
}
```

---

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
