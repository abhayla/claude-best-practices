---
name: android-test-patterns
description: >
  Apply Android test writing patterns including JUnit 5 unit tests, Compose UI tests,
  Espresso instrumented tests, Hilt test modules, coroutine test utilities,
  Room database testing, and test fixture factories. Use when writing new
  Android tests or setting up test infrastructure. For raw ADB-based testing
  without frameworks (uiautomator, screencap, monkey), use /android-adb-test.
triggers:
  - android test
  - write android tests
  - compose test
  - espresso test
  - android unit test
  - android test patterns
allowed-tools: "Bash Read Write Edit Grep Glob"
argument-hint: "<feature-name|test-type> [--unit|--ui|--e2e|--all]"
version: "1.0.0"
type: workflow
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


**Read:** `references/write-unit-tests-viewmodel-usecase-repository.md` for detailed step 3: write unit tests (viewmodel / usecase / repository) reference material.

## STEP 4: Write Compose UI Tests


**Read:** `references/write-compose-ui-tests.md` for detailed step 4: write compose ui tests reference material.

## Compose Preview Screenshot Testing

Google's official host-side screenshot testing for Compose — runs WITHOUT an emulator, generates HTML diff reports.

### Setup

```kotlin
// build.gradle.kts (app module)
plugins {
    id("com.google.android.compose.screenshot") version "0.0.1-alpha07"
}

android {
    experimentalProperties["android.experimental.enableScreenshotTest"] = true
}
```

### Writing Screenshot Tests

Annotate existing `@Preview` composables with `@PreviewTest`:

```kotlin
import com.google.android.screenshottesting.PreviewTest

@PreviewTest
@Preview(showBackground = true)
@Composable
fun LoginScreenPreview() {
    AppTheme {
        LoginScreen(state = LoginState.Idle, onIntent = {})
    }
}

@PreviewTest
@Preview(showBackground = true, uiMode = Configuration.UI_MODE_NIGHT_YES)
@Composable
fun LoginScreenDarkPreview() {
    AppTheme(darkTheme = true) {
        LoginScreen(state = LoginState.Idle, onIntent = {})
    }
}

// Test multiple states
@PreviewTest
@Preview(showBackground = true)
@Composable
fun LoginScreenErrorPreview() {
    AppTheme {
        LoginScreen(state = LoginState.Error("Invalid credentials"), onIntent = {})
    }
}
```

### Running Tests

```bash
# Validate screenshots against baselines (CI mode)
./gradlew validateDebugScreenshotTest

# Update baselines after intentional UI changes
./gradlew updateDebugScreenshotTest

# Results: app/build/reports/screenshotTest/
```

### Alternative: Paparazzi (JVM-based, no emulator)

```kotlin
// build.gradle.kts
plugins {
    id("app.cash.paparazzi") version "1.3.4"
}

// Test file
class LoginScreenTest {
    @get:Rule
    val paparazzi = Paparazzi(
        deviceConfig = DeviceConfig.PIXEL_6,
        theme = "android:Theme.Material3.Light",
    )

    @Test
    fun loginScreen_idle() {
        paparazzi.snapshot {
            AppTheme {
                LoginScreen(state = LoginState.Idle, onIntent = {})
            }
        }
    }
}
```

```bash
# Validate against golden files
./gradlew :app:testDebugUnitTest --tests "*LoginScreenTest*"

# Record new golden files
./gradlew :app:recordPaparazziDebug

# Verify against recorded golden files
./gradlew :app:verifyPaparazziDebug
```

### Alternative: Roborazzi (Robolectric-based)

```kotlin
// build.gradle.kts
plugins {
    id("io.github.takahirom.roborazzi") version "1.26.0"
}

// Test file (runs on JVM via Robolectric)
@RunWith(RobolectricTestRunner::class)
@GraphicsMode(GraphicsMode.Mode.NATIVE)
class HomeScreenRoborazziTest {
    @get:Rule
    val composeTestRule = createComposeRule()

    @Test
    fun homeScreen() {
        composeTestRule.setContent {
            AppTheme { HomeScreen() }
        }
        composeTestRule.onRoot().captureRoboImage()
    }
}
```

```bash
./gradlew recordRoborazziDebug    # Record baselines
./gradlew verifyRoborazziDebug    # Verify against baselines
./gradlew compareRoborazziDebug   # Generate diff report
```

### Which Tool to Use

| Tool | Emulator Required | Speed | Best For |
|------|-------------------|-------|----------|
| Compose Preview Screenshot | No | Fast | Preview-annotated composables |
| Paparazzi | No | Fast | Compose + View screenshots, device configs |
| Roborazzi | No (Robolectric) | Medium | Full screen tests, interaction-based captures |
| Espresso + Dropshots | Yes | Slow | Integration tests with real device rendering |

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
