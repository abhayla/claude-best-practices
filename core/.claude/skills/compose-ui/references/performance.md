# STEP 5: Performance

### Three Phases

Every frame goes through three phases. State reads in each phase only trigger work for that phase and later ones:

| Phase | What Happens | State Read Impact |
|-------|-------------|-------------------|
| **Composition** | Executes `@Composable` functions, builds UI tree | Triggers recomposition of the enclosing scope |
| **Layout** | Calculates size and position (`measure` / `layout`) | Triggers relayout only, skips composition |
| **Drawing** | Emits draw commands (`Canvas`, `DrawScope`) | Triggers redraw only, skips composition and layout |

### remember and derivedStateOf

```kotlin
// Cache expensive calculations across recompositions
val sorted = remember(items) { items.sortedBy { it.name } }

// Derive state that changes less often than its inputs
val showButton by remember {
    derivedStateOf { listState.firstVisibleItemIndex > 0 }
}
```

Use `derivedStateOf` when a frequently-changing state (scroll position, text input) should only trigger recomposition at a coarser granularity (threshold crossed, filtered result changed). Do NOT use it for cheap operations -- it adds overhead.

### Stability

The Compose compiler generates `$changed` bitmasks to skip recomposition when parameters have not changed. A type is **stable** if its public properties are all stable and `equals` is consistent.

| Category | Examples | Stable? |
|----------|----------|---------|
| Primitives | `Int`, `Float`, `Boolean`, `String` | Yes |
| `@Immutable` data classes | `data class User(val id: Int, val name: String)` | Yes |
| `@Stable` annotated classes | ViewModels, state holders with `MutableState` fields | Yes |
| `List<T>`, `Set<T>`, `Map<K,V>` (stdlib) | `List<User>` | **No** -- use `ImmutableList` from kotlinx-collections |
| Classes with `var` properties | Mutable POJOs | **No** |
| Lambda capturing unstable vars | `{ viewModel.doSomething(unstableObj) }` | **No** (without Strong Skipping) |

### Strong Skipping Mode (AGP 8.0+ / Compose Compiler 1.5.0+)

Strong Skipping makes lambdas stable when all captured variables are stable. Enabled by default in modern projects. Verify in `build.gradle.kts`:

```kotlin
android {
    composeOptions {
        kotlinCompilerExtensionVersion = "1.5.0"
    }
}
```

### ImmutableList

Replace `List<T>` parameters with `ImmutableList<T>` from `kotlinx-collections-immutable` so the compiler can skip recomposition:

```kotlin
@Composable
fun UserList(
    users: ImmutableList<User>,      // Stable
    modifier: Modifier = Modifier
) { /* ... */ }

// At call site
UserList(users = users.toImmutableList())
```

### Deferred State Reads

Push state reads from Composition into Layout or Drawing phase to avoid recomposition:

```kotlin
// BAD: reads in Composition, triggers recomposition on every change
Box(modifier = Modifier.offset(offsetX.value.dp, 0.dp))

// GOOD: reads in Layout phase, skips recomposition
Box(modifier = Modifier.offset { IntOffset(offsetX.value.toInt(), 0) })
```

Use lambda variants: `Modifier.offset { }`, `Modifier.graphicsLayer { }`, `Modifier.drawBehind { }`.

### Method References for Lambda Stability

Prefer method references over inline lambdas to help the compiler treat them as stable:

```kotlin
// Unstable lambda (new instance each recomposition)
Button(onClick = { viewModel.submit() }) { Text("Submit") }

// Stable method reference (same reference across recompositions)
Button(onClick = viewModel::submit) { Text("Submit") }
```

### Recomposition Detection

- **Layout Inspector** in Android Studio: shows recomposition counts per Composable.
- **Recomposition Highlights**: enable in Compose tooling to see which scopes recompose.
- **Perfetto / System Trace**: frame timing analysis for jank investigation.
- **Macrobenchmark**: measure startup and scroll performance in release builds.

---

