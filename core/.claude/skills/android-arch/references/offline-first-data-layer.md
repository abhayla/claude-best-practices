# STEP 4: Offline-First Data Layer

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

