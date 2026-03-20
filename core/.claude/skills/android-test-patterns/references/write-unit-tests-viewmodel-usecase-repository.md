# STEP 3: Write Unit Tests (ViewModel / UseCase / Repository)

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

