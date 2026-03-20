# STEP 3: ViewModel & State Management

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

