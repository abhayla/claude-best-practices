---
name: compose-ui
description: >
  Jetpack Compose UI development: state hoisting, modifier chains, Material3 theming,
  performance optimization (recomposition, stability, deferred reads), Compose Navigation
  with type-safe routes, and Coil image loading. Use when building or refactoring Compose UI.
triggers: "jetpack compose, compose ui, compose navigation, compose performance, recomposition, compose theming, material3, coil"
allowed-tools: "Bash Read Write Edit Grep Glob"
argument-hint: "<composable-name or 'navigation' or 'performance' or 'theme' or 'images'>"
version: "1.0.0"
type: workflow
---

# Compose UI

Build performant, testable Jetpack Compose interfaces with correct state management, Material3 theming, type-safe navigation, and optimized image loading.

**Request:** $ARGUMENTS

---

## STEP 1: State Hoisting

Make Composables **stateless** whenever possible by moving state to the caller (Unidirectional Data Flow).

### Stateful vs Stateless

```kotlin
// Stateful (internal state -- use only at the top-level screen wrapper)
@Composable
fun SearchBar() {
    var query by remember { mutableStateOf("") }
    SearchBarContent(query = query, onQueryChange = { query = it })
}

// Stateless (reusable, testable, previewable)
@Composable
fun SearchBarContent(
    query: String,                      // State flows down
    onQueryChange: (String) -> Unit,    // Events flow up
    modifier: Modifier = Modifier       // Default modifier parameter
) {
    TextField(
        value = query,
        onValueChange = onQueryChange,
        modifier = modifier
    )
}
```

### ViewModel Integration

The screen-level Composable collects state and passes it down:

```kotlin
@Composable
fun ProfileScreen(viewModel: ProfileViewModel = hiltViewModel()) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    ProfileContent(
        name = uiState.name,
        email = uiState.email,
        onSave = viewModel::onSave
    )
}
```

**Rule:** Push state as high as needed, but no higher. If only one child needs state, keep it there.

### Event Sink Pattern

For complex screens, use a sealed interface for events instead of multiple callback lambdas:

```kotlin
sealed interface ProfileEvent {
    data class UpdateName(val name: String) : ProfileEvent
    data class UpdateEmail(val email: String) : ProfileEvent
    data object Save : ProfileEvent
    data object Delete : ProfileEvent
}

// In ViewModel
fun onEvent(event: ProfileEvent) {
    when (event) {
        is ProfileEvent.UpdateName -> _state.update { it.copy(name = event.name) }
        is ProfileEvent.UpdateEmail -> _state.update { it.copy(email = event.email) }
        is ProfileEvent.Save -> save()
        is ProfileEvent.Delete -> delete()
    }
}

// In Composable — single lambda instead of many
ProfileContent(state = state, onEvent = viewModel::onEvent)
```

Use this when a screen has 4+ distinct user actions. For simple screens with 1-2 callbacks, individual lambdas are clearer.

---

## STEP 2: Modifiers


**Read:** `references/modifiers.md` for detailed step 2: modifiers reference material.

## STEP 3: Theming

### MaterialTheme Access

Use theme tokens instead of hardcoded values:

```kotlin
// GOOD: theme-aware
Text(
    text = title,
    style = MaterialTheme.typography.headlineMedium,
    color = MaterialTheme.colorScheme.onSurface
)

// BAD: hardcoded
Text(text = title, fontSize = 24.sp, color = Color.Black)
```

### ColorScheme.fromSeed

Generate a full Material3 color scheme from a single seed color:

```kotlin
@Composable
fun AppTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    dynamicColor: Boolean = true,
    content: @Composable () -> Unit
) {
    val colorScheme = when {
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val context = LocalContext.current
            if (darkTheme) dynamicDarkColorScheme(context)
            else dynamicLightColorScheme(context)
        }
        darkTheme -> darkColorScheme(
            primary = Color(0xFFD0BCFF),
            secondary = Color(0xFFCCC2DC)
        )
        else -> lightColorScheme(
            primary = Color(0xFF6750A4),
            secondary = Color(0xFF625B71)
        )
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = AppTypography,
        content = content
    )
}
```

### Dynamic Color (Android 12+)

Use `dynamicLightColorScheme(context)` / `dynamicDarkColorScheme(context)` to pick up the user's wallpaper-derived palette. Always provide a static fallback for older API levels.

---

## STEP 4: Previews

### Preview for Every Public Composable

```kotlin
@Preview(name = "Light", showBackground = true)
@Preview(name = "Dark", showBackground = true, uiMode = UI_MODE_NIGHT_YES)
@Composable
private fun UserCardPreview() {
    AppTheme {
        UserCard(
            name = "Jane Doe",
            email = "jane@example.com"
        )
    }
}
```

**Rules:**
- Mark preview functions `private` -- they are not production code.
- Pass static dummy data to the stateless Composable.
- Include both Light and Dark mode previews.
- Use `showBackground = true` so content is visible.

---

## STEP 5: Performance


**Read:** `references/performance.md` for detailed step 5: performance reference material.

## STEP 6: Compose Navigation

Use Navigation Compose with `@Serializable` route objects for type-safe navigation.


**Read:** `references/compose-navigation.md` for detailed step 6: compose navigation reference material.

## STEP 7: Coil Image Loading

Use **Coil** (Coroutines Image Loader) for image loading in Compose.

### AsyncImage (Preferred)

```kotlin
AsyncImage(
    model = ImageRequest.Builder(LocalContext.current)
        .data("https://example.com/photo.jpg")
        .crossfade(true)
        .build(),
    placeholder = painterResource(R.drawable.placeholder),
    error = painterResource(R.drawable.error),
    contentDescription = stringResource(R.string.photo_description),
    contentScale = ContentScale.Crop,
    modifier = Modifier.clip(CircleShape)
)
```

### rememberAsyncImagePainter (Low-Level)

Use only when you need a `Painter` for `Canvas` or `Icon`, not a full composable:

```kotlin
val painter = rememberAsyncImagePainter(
    model = ImageRequest.Builder(LocalContext.current)
        .data(url)
        .size(Size.ORIGINAL)
        .build()
)
Image(painter = painter, contentDescription = null)
```

**Warning:** `rememberAsyncImagePainter` does not detect the on-screen size. It loads the original image dimensions by default. Prefer `AsyncImage`.

### Singleton ImageLoader

Use a single `ImageLoader` for the entire app to share disk and memory caches. Configure in `Application.onCreate()` or via Hilt:

```kotlin
class MyApplication : Application(), ImageLoaderFactory {
    override fun newImageLoader(): ImageLoader {
        return ImageLoader.Builder(this)
            .crossfade(true)
            .memoryCache {
                MemoryCache.Builder(this)
                    .maxSizePercent(0.25)
                    .build()
            }
            .diskCache {
                DiskCache.Builder()
                    .directory(cacheDir.resolve("image_cache"))
                    .maxSizePercent(0.02)
                    .build()
            }
            .build()
    }
}
```

### Rules

- Prefer `AsyncImage` over `SubcomposeAsyncImage` and `rememberAsyncImagePainter`.
- Always enable `crossfade(true)` for smoother transitions.
- Always provide a meaningful `contentDescription` (or `null` for decorative images).
- Avoid `SubcomposeAsyncImage` inside `LazyColumn`/`LazyRow` -- subcomposition is slower.

---

## KMP Platform-Specific Composables

When using Compose Multiplatform, use `expect/actual` for platform-specific UI:

```kotlin
// commonMain
@Composable
expect fun PlatformStatusBar(darkIcons: Boolean)

// androidMain
@Composable
actual fun PlatformStatusBar(darkIcons: Boolean) {
    val systemUiController = rememberSystemUiController()
    SideEffect { systemUiController.setStatusBarColor(Color.Transparent, darkIcons) }
}

// iosMain
@Composable
actual fun PlatformStatusBar(darkIcons: Boolean) {
    // iOS handles via UIKit interop or Info.plist
}
```

Keep shared composables in `commonMain`, platform-specific implementations in `androidMain`/`iosMain`/`desktopMain`.

---

## Common Code Smells and Fixes

| Smell | Problem | Fix |
|-------|---------|-----|
| Inline lambda in `onClick` | Creates new lambda instance each recomposition, may cause child to recompose | Use method reference (`viewModel::onAction`) or `remember { { ... } }` |
| Sorting/filtering in `@Composable` body | Expensive work runs on every recomposition | Wrap in `remember(key)` or `derivedStateOf` |
| `LazyColumn` without `key` | Items recompose unnecessarily on list changes, animations break | Add `key = { item.id }` to `items()` |
| `List<T>` parameter | Compiler treats stdlib collections as unstable | Use `ImmutableList<T>` from `kotlinx-collections-immutable` |
| Allocating objects in Composable body | New instances every recomposition, GC pressure | Move to `remember { }` or outside the Composable |
| `Modifier.offset(x.dp, y.dp)` with state | Reads state in Composition phase, triggers full recomposition | Use `Modifier.offset { IntOffset(x, y) }` to defer to Layout phase |
| Hardcoded colors/text styles | Breaks theme consistency, ignores dark mode | Use `MaterialTheme.colorScheme` and `MaterialTheme.typography` |

---

## MUST DO

- Use `modifier: Modifier = Modifier` as the first optional parameter on every Composable
- Hoist state out of reusable Composables (value + onValueChange pattern)
- Mark data classes with `@Immutable` when all properties are `val` and stable
- Use `ImmutableList` for list parameters to ensure stability
- Use `remember {}` for expensive calculations, `derivedStateOf {}` for derived state
- Use `@Serializable` route objects for Compose Navigation (not string-based routes)
- Use `AsyncImage` with `crossfade(true)` for image loading
- Create `@Preview` (Light + Dark) for every public Composable
- Use `MaterialTheme.colorScheme` and `MaterialTheme.typography` for all styling
- Add `key = { item.id }` to `LazyColumn`/`LazyRow` items
- Profile with Layout Inspector and Perfetto before declaring performance acceptable
- Use `popUpTo` with `launchSingleTop` and `restoreState` for bottom navigation tabs
- Provide `contentDescription` on all images (or explicit `null` for decorative)

## MUST NOT DO

- Pass complex objects as navigation arguments -- pass IDs/primitives only, load data in the destination ViewModel
- Read state in Composition phase when it can be deferred to Layout/Drawing -- use lambda modifier variants instead
- Use `SubcomposeAsyncImage` inside `LazyColumn`/`LazyRow` -- use `AsyncImage` instead
- Use `List<T>` / `Set<T>` / `Map<K,V>` from stdlib as Composable parameters when stability matters -- use kotlinx-collections-immutable instead
- Hardcode colors, font sizes, or dimensions -- use MaterialTheme tokens instead
- Create `NavController` inside `NavHost` -- create it at the caller and pass it in
- Navigate inside `LaunchedEffect` without proper keys -- this causes repeated navigation on recomposition
- Skip `const` on stable widgets or omit `@Immutable`/`@Stable` annotations on data types
- Use string-based route paths (legacy pattern) -- use `@Serializable` objects/data classes instead
- Perform sorting, filtering, or formatting inside a Composable body without `remember` -- this re-executes on every recomposition
- Forget `FLAG_IMMUTABLE` on `PendingIntent` for deep links (required on Android 12+)

---

## Troubleshooting

| Symptom | Likely Cause | Recovery |
|---------|-------------|----------|
| Composable recomposes on every frame | Unstable parameter type or lambda capturing unstable variable | Annotate with `@Immutable`/`@Stable`, use `ImmutableList`, use method references |
| `LazyColumn` items flash or lose state | Missing or non-unique `key` in `items()` | Add `key = { item.uniqueId }` |
| Scroll jank in `LazyColumn` | Heavy work in Composition phase, large images without sizing | Defer state reads, use `remember`, use `AsyncImage` with size constraints |
| Theme not applied in preview | Preview not wrapped in `AppTheme {}` | Wrap preview content in your theme composable |
| Navigation argument crash | Mismatched route type or missing argument | Use `@Serializable` data class, verify `toRoute<T>()` matches declared route |
| Deep link not triggering | Missing intent filter in `AndroidManifest.xml` or scheme mismatch | Add `<intent-filter>` with matching scheme, host, and path |
| Image not loading (Coil) | Missing internet permission or incorrect URL | Add `INTERNET` permission, verify URL, check `ImageLoader` configuration |
| Back button pops wrong screen | `popUpTo` not configured on bottom nav navigation | Use `popUpTo(startDestination) { saveState = true }` with `restoreState = true` |
| `@Preview` crashes | Preview function calls ViewModel or uses runtime-only APIs | Pass static dummy data to stateless Composable, do not call `hiltViewModel()` in preview |
| Layout Inspector shows 0 recompositions | App running in release mode or debuggable not set | Profile in debug build with `debuggable = true` in `build.gradle.kts` |
| Modifier order produces unexpected visuals | Padding/background/clickable applied in wrong sequence | Read modifier chain top-to-bottom as "first applied = outermost"; reorder as needed |
