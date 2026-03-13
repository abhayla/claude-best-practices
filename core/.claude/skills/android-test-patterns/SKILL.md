---
name: android-test-patterns
description: >
  Android test writing patterns: JUnit 5 unit tests, Compose UI tests,
  Espresso instrumented tests, Hilt test modules, coroutine test utilities,
  Room database testing, and test fixture factories. Use when writing new
  Android tests or setting up test infrastructure for an Android project.
triggers:
  - android test
  - write android tests
  - compose test
  - espresso test
  - android unit test
  - android test patterns
allowed-tools: "Bash Read Write Edit Grep Glob"
argument-hint: "<feature-name|test-type> [--unit|--ui|--e2e|--all]"
---

# Android Test Patterns

Write Android tests following project conventions: JUnit 5 for unit, Compose Test for UI, Espresso for E2E.

**Target:** $ARGUMENTS

---

## STEP 1: Assess Test Scope

Determine what needs testing and which test type applies:

| Layer | Test Type | Framework | Emulator? |
|-------|-----------|-----------|-----------|
| ViewModel / UseCase / Repository | Unit | JUnit 5 + MockK + Turbine | No |
| Composable screens | UI (Compose) | `compose-ui-test` + JUnit 4 | No (Robolectric) or Yes |
| Full user flows | Instrumented E2E | Espresso or Compose Test on device | Yes |
| Database (Room) | Integration | JUnit + Room in-memory DB | No |
| Network (Retrofit) | Unit | MockWebServer + JUnit | No |

Read the feature's source files to identify:
- ViewModels → unit tests
- Screen composables → Compose UI tests
- Repository/DataSource → integration tests
- User journeys → E2E instrumented tests

## STEP 2: Set Up Test Dependencies

Verify `build.gradle.kts` includes required test dependencies:

```kotlin
// Unit tests
testImplementation("org.junit.jupiter:junit-jupiter:5.10.+")
testImplementation("io.mockk:mockk:1.13.+")
testImplementation("app.cash.turbine:turbine:1.1.+")
testImplementation("org.jetbrains.kotlinx:kotlinx-coroutines-test:1.8.+")
testImplementation("com.google.truth:truth:1.4.+")

// Compose UI tests
testImplementation("org.robolectric:robolectric:4.12.+")
androidTestImplementation("androidx.compose.ui:ui-test-junit4")
debugImplementation("androidx.compose.ui:ui-test-manifest")

// Espresso (instrumented)
androidTestImplementation("androidx.test.espresso:espresso-core:3.5.+")
androidTestImplementation("androidx.test.ext:junit-ktx:1.1.+")
androidTestImplementation("androidx.test:runner:1.5.+")
androidTestImplementation("androidx.test:rules:1.5.+")

// Hilt testing
testImplementation("com.google.dagger:hilt-android-testing:2.51.+")
kaptTest("com.google.dagger:hilt-android-compiler:2.51.+")
androidTestImplementation("com.google.dagger:hilt-android-testing:2.51.+")
kaptAndroidTest("com.google.dagger:hilt-android-compiler:2.51.+")

// Room testing
testImplementation("androidx.room:room-testing:2.6.+")
```

## STEP 3: Write Unit Tests (ViewModel / UseCase / Repository)

### 3.1 ViewModel Test Pattern

```kotlin
@ExtendWith(MockKExtension::class)
class FeatureViewModelTest {

    @MockK private lateinit var useCase: GetFeatureUseCase
    @MockK private lateinit var savedStateHandle: SavedStateHandle

    private lateinit var viewModel: FeatureViewModel

    @BeforeEach
    fun setup() {
        // Configure mocks BEFORE creating ViewModel
        every { savedStateHandle.get<String>("id") } returns "test-id"
        viewModel = FeatureViewModel(useCase, savedStateHandle)
    }

    @Test
    fun `initial state is Loading`() = runTest {
        viewModel.state.test {
            assertThat(awaitItem()).isEqualTo(FeatureState.Loading)
        }
    }

    @Test
    fun `successful load emits Content state`() = runTest {
        val data = FeatureData(id = "1", name = "Test")
        coEvery { useCase("test-id") } returns flowOf(Result.success(data))

        viewModel.onIntent(FeatureIntent.Load)

        viewModel.state.test {
            skipItems(1) // Skip Loading
            val content = awaitItem()
            assertThat(content).isInstanceOf(FeatureState.Content::class.java)
            assertThat((content as FeatureState.Content).data).isEqualTo(data)
        }
    }

    @Test
    fun `error emits Error state`() = runTest {
        coEvery { useCase("test-id") } returns flowOf(Result.failure(IOException("Network error")))

        viewModel.onIntent(FeatureIntent.Load)

        viewModel.state.test {
            skipItems(1) // Skip Loading
            val error = awaitItem()
            assertThat(error).isInstanceOf(FeatureState.Error::class.java)
        }
    }
}
```

### 3.2 UseCase Test Pattern

```kotlin
class GetFeatureUseCaseTest {

    @MockK private lateinit var repository: FeatureRepository

    private lateinit var useCase: GetFeatureUseCase

    @BeforeEach
    fun setup() {
        MockKAnnotations.init(this)
        useCase = GetFeatureUseCase(repository)
    }

    @Test
    fun `maps repository data to domain model`() = runTest {
        val entity = FeatureEntity(id = "1", name = "Raw")
        coEvery { repository.getById("1") } returns flowOf(entity)

        val result = useCase("1").first()

        assertThat(result.isSuccess).isTrue()
        assertThat(result.getOrNull()?.name).isEqualTo("Raw")
    }
}
```

### 3.3 Repository Test Pattern (with Room)

```kotlin
@RunWith(AndroidJUnit4::class)
class FeatureRepositoryTest {

    private lateinit var db: AppDatabase
    private lateinit var dao: FeatureDao
    private lateinit var repository: FeatureRepositoryImpl

    @Before
    fun setup() {
        db = Room.inMemoryDatabaseBuilder(
            ApplicationProvider.getApplicationContext(),
            AppDatabase::class.java
        ).allowMainThreadQueries().build()
        dao = db.featureDao()
        repository = FeatureRepositoryImpl(dao, mockWebServer.toRetrofitService())
    }

    @After
    fun teardown() {
        db.close()
    }

    @Test
    fun `getById returns cached data when available`() = runTest {
        dao.insert(FeatureEntity(id = "1", name = "Cached"))

        val result = repository.getById("1").first()

        assertThat(result.name).isEqualTo("Cached")
    }
}
```

## STEP 4: Write Compose UI Tests

### 4.1 Screen Test Pattern

```kotlin
@RunWith(AndroidJUnit4::class)
class FeatureScreenTest {

    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun `loading state shows progress indicator`() {
        composeTestRule.setContent {
            FeatureScreen(state = FeatureState.Loading, onIntent = {})
        }

        composeTestRule.onNodeWithTag("loading_indicator").assertIsDisplayed()
    }

    @Test
    fun `content state shows data`() {
        val data = FeatureData(id = "1", name = "Test Feature")
        composeTestRule.setContent {
            FeatureScreen(
                state = FeatureState.Content(data),
                onIntent = {}
            )
        }

        composeTestRule.onNodeWithText("Test Feature").assertIsDisplayed()
    }

    @Test
    fun `clicking action button sends intent`() {
        var receivedIntent: FeatureIntent? = null
        composeTestRule.setContent {
            FeatureScreen(
                state = FeatureState.Content(testData),
                onIntent = { receivedIntent = it }
            )
        }

        composeTestRule.onNodeWithContentDescription("Action").performClick()

        assertThat(receivedIntent).isEqualTo(FeatureIntent.ActionClicked)
    }

    @Test
    fun `error state shows retry button`() {
        composeTestRule.setContent {
            FeatureScreen(
                state = FeatureState.Error("Something went wrong"),
                onIntent = {}
            )
        }

        composeTestRule.onNodeWithText("Retry").assertIsDisplayed()
        composeTestRule.onNodeWithText("Something went wrong").assertIsDisplayed()
    }
}
```

### 4.2 Compose Test Finders Reference

| Finder | Usage |
|--------|-------|
| `onNodeWithText("label")` | Find by visible text |
| `onNodeWithContentDescription("desc")` | Find by a11y description |
| `onNodeWithTag("tag")` | Find by `Modifier.testTag("tag")` |
| `onAllNodesWithText("item")` | Find multiple matches |
| `onNodeWithTag("list").onChildren()` | Navigate child nodes |

### 4.3 Compose Test Actions Reference

| Action | Usage |
|--------|-------|
| `.performClick()` | Tap |
| `.performTextInput("text")` | Type text |
| `.performScrollTo()` | Scroll to node |
| `.performTouchInput { swipeUp() }` | Gesture |
| `.performImeAction()` | Submit keyboard action |

## STEP 5: Write Hilt-Injected Tests

```kotlin
@HiltAndroidTest
@RunWith(AndroidJUnit4::class)
class FeatureIntegrationTest {

    @get:Rule(order = 0)
    val hiltRule = HiltAndroidRule(this)

    @get:Rule(order = 1)
    val composeTestRule = createAndroidComposeRule<MainActivity>()

    @Inject lateinit var repository: FeatureRepository

    @Before
    fun setup() {
        hiltRule.inject()
    }

    @Module
    @InstallIn(SingletonComponent::class)
    object TestModule {
        @Provides
        @Singleton
        fun provideTestDatabase(@ApplicationContext context: Context): AppDatabase =
            Room.inMemoryDatabaseBuilder(context, AppDatabase::class.java).build()
    }
}
```

## STEP 6: Write Test Fixtures / Factories

Create reusable test data in `test/fixtures/` or `test/factory/`:

```kotlin
object FeatureTestFactory {

    fun createFeatureData(
        id: String = "test-id",
        name: String = "Test Feature",
        status: Status = Status.ACTIVE,
        createdAt: Instant = Instant.parse("2024-01-01T00:00:00Z")
    ) = FeatureData(id = id, name = name, status = status, createdAt = createdAt)

    fun createFeatureEntity(
        id: String = "test-id",
        name: String = "Test Feature"
    ) = FeatureEntity(id = id, name = name)

    fun createFeatureList(count: Int = 5) =
        (1..count).map { createFeatureData(id = "id-$it", name = "Feature $it") }
}
```

## STEP 7: Coroutine Test Utilities

### 7.1 TestDispatcherRule

```kotlin
class TestDispatcherRule(
    private val dispatcher: TestDispatcher = UnconfinedTestDispatcher()
) : TestWatcher() {
    override fun starting(description: Description) {
        Dispatchers.setMain(dispatcher)
    }
    override fun finished(description: Description) {
        Dispatchers.resetMain()
    }
}
```

Usage in tests:
```kotlin
class MyViewModelTest {
    @get:Rule
    val dispatcherRule = TestDispatcherRule()

    // Tests automatically use TestDispatcher for Dispatchers.Main
}
```

### 7.2 Flow Testing with Turbine

```kotlin
@Test
fun `state flow emits correct sequence`() = runTest {
    viewModel.state.test {
        assertThat(awaitItem()).isEqualTo(State.Initial)

        viewModel.onIntent(Intent.Load)

        assertThat(awaitItem()).isEqualTo(State.Loading)
        assertThat(awaitItem()).isInstanceOf(State.Content::class.java)

        cancelAndConsumeRemainingEvents()
    }
}
```

## STEP 8: Run Tests

```bash
# Unit tests (no emulator)
cd android && ./gradlew :app:testDebugUnitTest

# Single test class
cd android && ./gradlew :app:testDebugUnitTest --tests "*.FeatureViewModelTest"

# Compose UI tests on device
cd android && ./gradlew :app:connectedDebugAndroidTest \
  -Pandroid.testInstrumentationRunnerArguments.class=com.example.feature.FeatureScreenTest

# All instrumented tests
cd android && ./gradlew :app:connectedDebugAndroidTest

# Coverage report
cd android && ./gradlew :app:testDebugUnitTest :app:jacocoTestReport
```

Delegate to `/android-run-tests` or `/android-run-e2e` for execution with auto-fix.

---

## MUST DO

- Use `runTest` for all coroutine tests — never `runBlocking` in test code
- Use Turbine's `.test {}` for Flow assertions — never `.first()` with delay
- Use `Room.inMemoryDatabaseBuilder` for database tests — never real DB
- Use MockK `coEvery` / `coVerify` for suspend functions
- Add `Modifier.testTag("name")` to composables that need test access
- Use factories with default parameters for test data — never hardcode
- Follow AAA pattern (Arrange-Act-Assert) in every test
- Keep UI tests focused on one behavior per test

## MUST NOT DO

- MUST NOT use `Thread.sleep()` or fixed delays — use Compose `waitUntil` or Turbine `awaitItem`
- MUST NOT share mutable state between tests — each test gets fresh ViewModel/DB
- MUST NOT test implementation details (private methods, internal state)
- MUST NOT mock composables — test them via `composeTestRule.setContent`
- MUST NOT use `@LargeTest` for unit tests — only for full E2E flows
- MUST NOT skip `@After` cleanup for Room databases — causes test pollution
