---
name: flutter-dev
description: >
  Flutter 3+ development workflow: widget architecture, Riverpod/BLoC state management,
  GoRouter navigation, Material Design 3 theming, platform-specific implementations,
  testing, and performance optimization. Use for building cross-platform Flutter apps.
allowed-tools: "Bash Read Grep Glob Write Edit"
triggers: "flutter, dart, widget, riverpod, bloc, gorouter, cross-platform mobile"
argument-hint: "<feature-description or 'setup' or 'test' or 'optimize'>"
version: "1.0.0"
type: workflow
---

# Flutter Development

Build cross-platform Flutter 3+ applications with structured architecture, robust state management, and native performance.

**Request:** $ARGUMENTS

---

## STEP 1: Setup

Scaffold or verify the Flutter project structure.

### Project Structure (Feature-Based)

```
lib/
  core/
    constants/        # App-wide constants, enums
    theme/            # Material Design 3 theme data
    utils/            # Shared utilities, extensions
    network/          # HTTP client, interceptors
  features/
    auth/
      data/           # Repositories, data sources, DTOs
      domain/         # Entities, use cases
      presentation/   # Screens, widgets, providers/blocs
    home/
      data/
      domain/
      presentation/
  shared/
    widgets/          # Reusable widgets (buttons, cards, inputs)
    providers/        # App-wide Riverpod providers
  routes/
    app_router.dart   # GoRouter configuration
  main.dart           # Entry point with ProviderScope
```

### Dependencies (pubspec.yaml essentials)

```yaml
dependencies:
  flutter:
    sdk: flutter
  flutter_riverpod: ^2.5.0    # State management (primary)
  riverpod_annotation: ^2.3.0 # Code generation for providers
  go_router: ^14.0.0          # Declarative routing
  freezed_annotation: ^2.4.0  # Immutable data classes
  json_annotation: ^4.9.0     # JSON serialization
  dio: ^5.4.0                 # HTTP client
  cached_network_image: ^3.3.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  build_runner: ^2.4.0
  freezed: ^2.5.0
  riverpod_generator: ^2.4.0
  json_serializable: ^6.7.0
  mocktail: ^1.0.0
  flutter_lints: ^4.0.0
```

### Entry Point

```dart
void main() {
  WidgetsFlutterBinding.ensureInitialized();
  runApp(const ProviderScope(child: MyApp()));
}

class MyApp extends ConsumerWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final router = ref.watch(routerProvider);
    return MaterialApp.router(
      routerConfig: router,
      theme: AppTheme.light(),
      darkTheme: AppTheme.dark(),
      themeMode: ThemeMode.system,
    );
  }
}
```

### Verify Setup

```bash
flutter pub get
flutter analyze
```

Fix all lint issues before proceeding.

---

## STEP 2: State Management

Define state using Riverpod 2.0 (primary) or BLoC/Cubit as the project requires.

### Riverpod 2.0 — Provider Types

| Provider Type | Use Case | Example |
|---------------|----------|---------|
| `Provider` | Computed/derived values | Config, formatted strings |
| `StateProvider` | Simple mutable state | Toggle, counter |
| `FutureProvider` | Async one-shot data | API fetch |
| `StreamProvider` | Reactive streams | WebSocket, Firestore |
| `NotifierProvider` | Complex mutable state | Form state, entities |
| `AsyncNotifierProvider` | Complex async state | CRUD operations |

### Riverpod Notifier Pattern

```dart
@riverpod
class TodoList extends _$TodoList {
  @override
  Future<List<Todo>> build() async {
    return ref.watch(todoRepositoryProvider).fetchAll();
  }

  Future<void> addTodo(Todo todo) async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() async {
      await ref.read(todoRepositoryProvider).create(todo);
      return ref.read(todoRepositoryProvider).fetchAll();
    });
  }
}
```

### ConsumerWidget Usage

```dart
class TodoScreen extends ConsumerWidget {
  const TodoScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final todosAsync = ref.watch(todoListProvider);

    return todosAsync.when(
      data: (todos) => TodoListView(todos: todos),
      loading: () => const Center(child: CircularProgressIndicator()),
      error: (err, stack) => ErrorWidget(message: err.toString()),
    );
  }
}
```

### Selective Rebuilds

```dart
// Watch only the count — widget rebuilds only when count changes
final count = ref.watch(todoListProvider.select((data) => data.value?.length ?? 0));
```

### BLoC/Cubit Pattern (Alternative)

```dart
// Cubit — simpler, no events
class CounterCubit extends Cubit<int> {
  CounterCubit() : super(0);
  void increment() => emit(state + 1);
  void decrement() => emit(state - 1);
}

// Bloc — event-driven, full traceability
sealed class AuthEvent {}
class LoginRequested extends AuthEvent {
  final String email;
  final String password;
  LoginRequested({required this.email, required this.password});
}

class AuthBloc extends Bloc<AuthEvent, AuthState> {
  AuthBloc(this._authRepo) : super(AuthInitial()) {
    on<LoginRequested>(_onLoginRequested);
  }
  final AuthRepository _authRepo;

  Future<void> _onLoginRequested(
    LoginRequested event, Emitter<AuthState> emit,
  ) async {
    emit(AuthLoading());
    try {
      final user = await _authRepo.login(event.email, event.password);
      emit(AuthAuthenticated(user));
    } catch (e) {
      emit(AuthError(e.toString()));
    }
  }
}
```

### Verify State Layer

```bash
flutter analyze
dart run build_runner build --delete-conflicting-outputs
```

---

## STEP 3: Widget Development

Build reusable, const-optimized widgets with GoRouter navigation and Material Design 3 theming.


**Read:** `references/widget-development.md` for detailed step 3: widget development reference material.

## STEP 4: Testing

Write widget tests, unit tests, and integration tests.


**Read:** `references/testing.md` for detailed step 4: testing reference material.

# Unit and widget tests
flutter test

# With coverage
flutter test --coverage

# Integration tests (requires emulator/device)
flutter test integration_test/

# Single test file
flutter test test/features/auth/presentation/login_screen_test.dart
```

---

## STEP 5: Performance Optimization

Profile and eliminate jank. Target: consistent 60 FPS, <16ms per frame.

### Profiling

```bash
# Launch in profile mode
flutter run --profile

# Open DevTools
flutter pub global activate devtools
flutter pub global run devtools
```

### Key Optimizations

**Const Constructors** — prevent unnecessary rebuilds:

```dart
// GOOD: const prevents rebuild when parent rebuilds
return const Padding(
  padding: EdgeInsets.all(16),
  child: Text('Static content'),
);
```

**RepaintBoundary** — isolate expensive paint operations:

```dart
RepaintBoundary(
  child: CustomPaint(
    painter: ChartPainter(data: chartData),
  ),
)
```

**Offload heavy computation** — keep the UI thread free:

```dart
// Use compute() for CPU-intensive work
final result = await compute(parseJsonInBackground, rawJson);

// Top-level or static function required by compute()
List<Item> parseJsonInBackground(String json) {
  return (jsonDecode(json) as List).map((e) => Item.fromJson(e)).toList();
}
```

**Selective Provider Watching** — rebuild only what changed:

```dart
// BAD: rebuilds on any state change
final state = ref.watch(largeStateProvider);

// GOOD: rebuilds only when selectedId changes
final id = ref.watch(largeStateProvider.select((s) => s.selectedId));
```

**Image Optimization:**

```dart
CachedNetworkImage(
  imageUrl: url,
  memCacheWidth: 300,   // Resize in memory cache
  placeholder: (_, __) => const ShimmerPlaceholder(),
  errorWidget: (_, __, ___) => const Icon(Icons.error),
)
```

### DevTools Metrics

| Metric | Target | Red Flag |
|--------|--------|----------|
| Frame build time | <16ms | >16ms consistently |
| Frame raster time | <16ms | >16ms consistently |
| Widget rebuild count | Minimal | Entire tree rebuilding |
| Memory usage | Stable | Monotonic increase |
| Shader compilation | Pre-warmed | Jank on first animation |

---

## Troubleshooting

| Symptom | Likely Cause | Recovery |
|---------|-------------|----------|
| `flutter analyze` errors | Unresolved imports, missing `const`, type mismatches | Fix flagged lines; run `flutter pub get` if imports missing |
| Widget test assertion failures | Widget tree mismatch or async state not settled | Use `tester.pumpAndSettle()`; verify finder selectors |
| Build fails after adding package | Incompatible dependency version | Run `flutter pub upgrade --major-versions` |
| Jank / dropped frames | Expensive `build()`, uncached widgets | Use `RepaintBoundary`, move work to `compute()`, add `const` |
| Hot reload not reflecting changes | State held in Notifier not reset | Use hot restart (`R` in terminal) |
| `RenderFlex overflowed` | Content exceeds available space | Wrap in `SingleChildScrollView` or use `Expanded`/`Flexible` |
| Platform channel `MissingPluginException` | Plugin not registered on target platform | Run `flutter clean && flutter pub get`, rebuild |
| `setState() called after dispose()` | Async callback on unmounted widget | Check `mounted` before `setState`, or use Riverpod instead |

---

## CRITICAL RULES

### MUST DO

- Use `const` constructors on all static widgets
- Implement `Key` (preferably `ValueKey`) for list items
- Use `ConsumerWidget`/`Consumer` for Riverpod state — not raw `StatefulWidget`
- Follow Material Design 3 guidelines (use `ColorScheme.fromSeed`)
- Profile with DevTools before declaring performance "good enough"
- Test widgets with `flutter_test` and `pumpAndSettle()`
- Run `flutter analyze` before every commit — zero warnings
- Use feature-based directory structure under `lib/`
- Handle all `AsyncValue` states (`data`, `loading`, `error`)

### MUST NOT DO

- Build widget instances inside another widget's `build()` method — extract to separate widget classes instead
- Mutate state directly — always create new instances via Riverpod notifiers or BLoC emit
- Use `setState` for app-wide or cross-widget state — use Riverpod providers or BLoC instead
- Skip `const` on widgets with no runtime parameters — the analyzer flags this
- Ignore platform-specific behavior differences — test on both iOS and Android
- Block the UI thread with heavy computation — use `compute()` or `Isolate` instead
- Use string literals for route paths — define route constants or use GoRouter named routes
- Commit code with `flutter analyze` warnings
