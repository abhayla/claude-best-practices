# STEP 5: Kotlin Coroutines & Structured Concurrency

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

