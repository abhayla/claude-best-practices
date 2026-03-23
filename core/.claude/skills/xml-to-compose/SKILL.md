---
name: xml-to-compose
description: >
  Convert Android XML layouts to idiomatic Jetpack Compose. Covers layout/widget/attribute
  mapping, interop bridges (ComposeView, AndroidView), LiveData-to-StateFlow migration,
  include/merge extraction, and incremental screen-by-screen adoption strategy. Use when
  migrating Android UI from XML to Jetpack Compose.
triggers: "xml to compose, migrate xml, convert layout, xml migration, view to compose"
allowed-tools: "Bash Read Write Edit Grep Glob"
argument-hint: "<xml-file-path or 'plan' or 'audit' or 'interop'>"
version: "1.0.0"
type: workflow
---

# XML to Compose Migration

Systematically convert Android XML layouts to idiomatic Jetpack Compose, preserving functionality while embracing Compose patterns.

**Request:** $ARGUMENTS

---

## STEP 1: Analyze the XML Layout

Before writing any Compose code, inventory the XML source.

1. Identify the root layout type (`ConstraintLayout`, `LinearLayout`, `FrameLayout`, etc.).
2. List all View widgets and their key attributes.
3. Map data binding expressions (`@{}`) or view binding references.
4. Identify custom views that need special handling.
5. Note any `include`, `merge`, or `ViewStub` usage.
6. Catalog click listeners, animations, and drawable references.

```bash
# Find all XML layout files in the project
find app/src/main/res/layout -name "*.xml" | sort
```

---

## STEP 2: Plan the Migration

- Decide: **Full rewrite** or **incremental migration** (using `ComposeView`/`AndroidView`).
- Identify state sources (ViewModel, LiveData, savedInstanceState).
- List reusable components to extract as separate Composables.
- Plan navigation integration if using Navigation component.

### Migration Strategy

| Approach | When to Use |
|----------|------------|
| **Screen-by-screen** | Preferred default; migrate one screen at a time starting with leaf screens |
| **Bottom-up (leaf views first)** | Replace inner widgets with Composables via `ComposeView`, then work outward |
| **Interop bridge** | Use `ComposeView` in XML or `AndroidView` in Compose for gradual cutover |

**Always migrate bottom-up**: start with leaf views (buttons, cards, list items), then containers, then full screens. This minimizes risk and keeps the app shippable at every step.

---

## STEP 3: Convert Using Mapping Tables

### Container Layout Mapping

| XML Layout | Compose Equivalent | Notes |
|------------|-------------------|-------|
| `LinearLayout (vertical)` | `Column` | Use `Arrangement` and `Alignment` |
| `LinearLayout (horizontal)` | `Row` | Use `Arrangement` and `Alignment` |
| `FrameLayout` | `Box` | Children stack on top of each other |
| `ConstraintLayout` | `ConstraintLayout` (Compose) | Use `createRefs()` and `constrainAs` |
| `RelativeLayout` | `Box` or `ConstraintLayout` | Prefer `Box` for simple overlap |
| `ScrollView` | `Column` + `Modifier.verticalScroll()` | Or use `LazyColumn` for long lists |
| `HorizontalScrollView` | `Row` + `Modifier.horizontalScroll()` | Or use `LazyRow` for long lists |
| `RecyclerView` | `LazyColumn` / `LazyRow` / `LazyGrid` | Most common migration |
| `ViewPager2` | `HorizontalPager` | From Compose Foundation |
| `CoordinatorLayout` | Custom + `Scaffold` | Use `TopAppBar` with scroll behavior |
| `NestedScrollView` | `Column` + `Modifier.verticalScroll()` | Prefer Lazy variants for lists |

### Widget Mapping

| XML Widget | Compose Equivalent | Notes |
|------------|-------------------|-------|
| `TextView` | `Text` | Use `style` parameter with `TextStyle` |
| `EditText` | `TextField` / `OutlinedTextField` | Requires state hoisting |
| `Button` | `Button` | Use `onClick` lambda |
| `ImageView` | `Image` | Use `painterResource()` or Coil `AsyncImage` |
| `ImageButton` | `IconButton` | Use `Icon` inside |
| `CheckBox` | `Checkbox` | Requires `checked` + `onCheckedChange` |
| `RadioButton` | `RadioButton` | Use with `Row` for groups |
| `Switch` | `Switch` | Requires state hoisting |
| `ProgressBar (circular)` | `CircularProgressIndicator` | |
| `ProgressBar (horizontal)` | `LinearProgressIndicator` | |
| `SeekBar` | `Slider` | Requires state hoisting |
| `Spinner` | `DropdownMenu` + `ExposedDropdownMenuBox` | More complex pattern |
| `CardView` | `Card` | From Material 3 |
| `Toolbar` | `TopAppBar` | Use inside `Scaffold` |
| `BottomNavigationView` | `NavigationBar` | Material 3 |
| `FloatingActionButton` | `FloatingActionButton` | Use inside `Scaffold` |
| `Divider` | `HorizontalDivider` / `VerticalDivider` | |
| `Space` | `Spacer` | Use `Modifier.size()` |
| `WebView` | `AndroidView { WebView(it) }` | No native Compose equivalent |
| `MapView` | `AndroidView { MapView(it) }` | No native Compose equivalent |
| `TabLayout` | `TabRow` / `ScrollableTabRow` | Material 3 |
| `ChipGroup` | `FlowRow` + `FilterChip`/`AssistChip` | Material 3 |

### Attribute Mapping

| XML Attribute | Compose Modifier / Property |
|---------------|-----------------------------|
| `android:layout_width="match_parent"` | `Modifier.fillMaxWidth()` |
| `android:layout_height="match_parent"` | `Modifier.fillMaxHeight()` |
| `android:layout_width="wrap_content"` | Default (implicit wrap) |
| `android:layout_weight` | `Modifier.weight(1f)` |
| `android:padding` | `Modifier.padding()` |
| `android:layout_margin` | `Modifier.padding()` on parent, or `Arrangement.spacedBy()` |
| `android:background` | `Modifier.background()` |
| `android:visibility="gone"` | Conditional composition (do not emit the composable) |
| `android:visibility="invisible"` | `Modifier.alpha(0f)` (keeps space in layout) |
| `android:clickable` | `Modifier.clickable { }` |
| `android:contentDescription` | `Modifier.semantics { contentDescription = "..." }` |
| `android:elevation` | `Modifier.shadow()` or component's `elevation` param |
| `android:alpha` | `Modifier.alpha()` |
| `android:rotation` | `Modifier.rotate()` |
| `android:scaleX/Y` | `Modifier.scale()` |
| `android:gravity` | `Alignment` parameter or `Arrangement` |
| `android:layout_gravity` | `Modifier.align()` |

---

## STEP 4: Code Examples

### Weighted Layouts (LinearLayout with layout_weight)

```xml
<!-- XML -->
<LinearLayout android:orientation="horizontal"
    android:layout_width="match_parent"
    android:layout_height="wrap_content">
    <View android:layout_weight="1"
        android:layout_width="0dp"
        android:layout_height="48dp" />
    <View android:layout_weight="2"
        android:layout_width="0dp"
        android:layout_height="48dp" />
</LinearLayout>
```

```kotlin
// Compose
Row(modifier = Modifier.fillMaxWidth()) {
    Box(modifier = Modifier.weight(1f).height(48.dp))
    Box(modifier = Modifier.weight(2f).height(48.dp))
}
```

### RecyclerView to LazyColumn

```xml
<!-- XML -->
<androidx.recyclerview.widget.RecyclerView
    android:id="@+id/recyclerView"
    android:layout_width="match_parent"
    android:layout_height="match_parent" />
```

```kotlin
// Compose — replaces RecyclerView + Adapter + ViewHolder
LazyColumn(modifier = Modifier.fillMaxSize()) {
    items(items, key = { it.id }) { item ->
        ItemRow(item = item, onClick = { onItemClick(item) })
    }
}
```

### EditText with Two-Way Data Binding

```xml
<!-- XML with Data Binding -->
<EditText
    android:text="@={viewModel.username}"
    android:hint="@string/username_hint"
    android:layout_width="match_parent"
    android:layout_height="wrap_content" />
```

```kotlin
// Compose
val username by viewModel.username.collectAsState()

OutlinedTextField(
    value = username,
    onValueChange = { viewModel.updateUsername(it) },
    label = { Text(stringResource(R.string.username_hint)) },
    modifier = Modifier.fillMaxWidth()
)
```

### ConstraintLayout Migration

```xml
<!-- XML -->
<androidx.constraintlayout.widget.ConstraintLayout
    android:layout_width="match_parent"
    android:layout_height="wrap_content">
    <TextView
        android:id="@+id/title"
        app:layout_constraintTop_toTopOf="parent"
        app:layout_constraintStart_toStartOf="parent" />
    <TextView
        android:id="@+id/subtitle"
        app:layout_constraintTop_toBottomOf="@id/title"
        app:layout_constraintStart_toStartOf="@id/title" />
</androidx.constraintlayout.widget.ConstraintLayout>
```

```kotlin
// Compose
ConstraintLayout(modifier = Modifier.fillMaxWidth()) {
    val (title, subtitle) = createRefs()

    Text(
        text = "Title",
        modifier = Modifier.constrainAs(title) {
            top.linkTo(parent.top)
            start.linkTo(parent.start)
        }
    )
    Text(
        text = "Subtitle",
        modifier = Modifier.constrainAs(subtitle) {
            top.linkTo(title.bottom)
            start.linkTo(title.start)
        }
    )
}
```

---

## STEP 5: Interop (Gradual Migration)

### Embedding Compose in XML (ComposeView)

Use this to migrate individual widgets or sections inside an existing XML layout.

```xml
<!-- In your XML layout -->
<androidx.compose.ui.platform.ComposeView
    android:id="@+id/compose_view"
    android:layout_width="match_parent"
    android:layout_height="wrap_content" />
```

```kotlin
// In Fragment or Activity
binding.composeView.apply {
    setViewCompositionStrategy(ViewCompositionStrategy.DisposeOnViewTreeLifecycleDestroyed)
    setContent {
        MaterialTheme {
            MyComposable()
        }
    }
}
```

### Embedding XML Views in Compose (AndroidView)

Use this for views with no Compose equivalent (MapView, WebView, custom native views).

```kotlin
@Composable
fun MapViewComposable(modifier: Modifier = Modifier) {
    AndroidView(
        factory = { context ->
            MapView(context).apply {
                // Initialize the view
            }
        },
        update = { mapView ->
            // Update the view when state changes
        },
        modifier = modifier
    )
}
```

---

## STEP 6: State Migration

### LiveData to StateFlow

```kotlin
// BEFORE: ViewModel with LiveData
class MyViewModel : ViewModel() {
    private val _uiState = MutableLiveData<UiState>()
    val uiState: LiveData<UiState> = _uiState
}

// AFTER: ViewModel with StateFlow
class MyViewModel : ViewModel() {
    private val _uiState = MutableStateFlow(UiState())
    val uiState: StateFlow<UiState> = _uiState.asStateFlow()
}
```

```kotlin
// BEFORE: Observing in Fragment
viewModel.uiState.observe(viewLifecycleOwner) { state ->
    binding.title.text = state.title
}

// AFTER: Collecting in Compose
@Composable
fun MyScreen(viewModel: MyViewModel = hiltViewModel()) {
    val uiState by viewModel.uiState.collectAsStateWithLifecycle()

    Text(text = uiState.title)
}
```

### Click Listeners

```kotlin
// BEFORE: XML + setOnClickListener
binding.submitButton.setOnClickListener {
    viewModel.submit()
}

// AFTER: Lambda in Compose
Button(onClick = { viewModel.submit() }) {
    Text("Submit")
}
```

### include/merge to Extracted Composable

```xml
<!-- XML: layout_header.xml -->
<merge>
    <ImageView android:id="@+id/avatar" />
    <TextView android:id="@+id/name" />
</merge>

<!-- Usage -->
<include layout="@layout/layout_header" />
```

```kotlin
// Compose: Extract as a reusable Composable
@Composable
fun HeaderSection(
    avatarUrl: String,
    name: String,
    modifier: Modifier = Modifier
) {
    Row(modifier = modifier) {
        AsyncImage(model = avatarUrl, contentDescription = null)
        Text(text = name)
    }
}

// Usage
HeaderSection(avatarUrl = user.avatar, name = user.name)
```

---

## STEP 7: Verify

- Compare visual output between XML and Compose versions side-by-side.
- Test accessibility (content descriptions, touch targets >=48dp).
- Verify state preservation across configuration changes.
- Run `./gradlew assembleDebug` to confirm compilation.
- Delete migrated XML files and remove unused ViewBinding/DataBinding references.

### Migration Checklist

- [ ] All layouts converted (no `include` or `merge` left)
- [ ] State hoisted properly (no internal mutable state for user input)
- [ ] Click handlers converted to lambdas
- [ ] RecyclerView adapters removed (using LazyColumn/LazyRow)
- [ ] ViewBinding/DataBinding removed
- [ ] Navigation integrated (NavHost or interop)
- [ ] Theming applied (MaterialTheme)
- [ ] Accessibility preserved (content descriptions, touch targets)
- [ ] Preview annotations added for development
- [ ] Old XML layout files deleted

---

## Common Pitfalls

| Pitfall | Problem | Fix |
|---------|---------|-----|
| Modifier order matters | `.padding().clickable()` pads then adds click area; `.clickable().padding()` clicks then pads | Put `.clickable()` before `.padding()` so the entire padded area is tappable |
| Missing `key` in LazyColumn | Items recompose incorrectly on list changes | Always provide `key = { it.id }` to `items()` |
| State in ViewModel as `MutableState` | Compose state tied to UI layer leaks into ViewModel | Use `StateFlow` in ViewModel, collect with `collectAsStateWithLifecycle()` in Compose |
| Forgetting `ViewCompositionStrategy` | ComposeView leaks or recomposes after Fragment view destroyed | Set `DisposeOnViewTreeLifecycleDestroyed` on every `ComposeView` |
| Nesting scrollable in scrollable | `LazyColumn` inside `Column(verticalScroll)` crashes | Give `LazyColumn` a fixed height, or use a single `LazyColumn` with mixed item types |
| Converting `visibility="gone"` to `alpha(0f)` | Element still occupies space and receives clicks | Use conditional composition: `if (visible) { MyComposable() }` |
| Hardcoding colors/dimensions | Breaks theme support and dark mode | Use `MaterialTheme.colorScheme` and `MaterialTheme.typography` |
| Ignoring recomposition scope | Passing unstable lambdas causes unnecessary recomposition | Use `remember { { viewModel.action() } }` or method references |

---

## CRITICAL RULES

### MUST DO

- Hoist all state out of composables — pass state down, events up (unidirectional data flow)
- Use `collectAsStateWithLifecycle()` instead of `collectAsState()` for lifecycle-aware collection
- Set `ViewCompositionStrategy.DisposeOnViewTreeLifecycleDestroyed` on every `ComposeView`
- Provide stable `key` parameters in `LazyColumn`/`LazyRow` `items()` calls
- Use `Modifier.semantics { contentDescription = "..." }` to preserve accessibility from XML
- Apply `MaterialTheme` at the root of every `ComposeView.setContent` block
- Test with TalkBack after migration to verify accessibility parity
- Add `@Preview` annotations to every new Composable for visual verification

### MUST NOT DO

- Do not wrap `LazyColumn` inside a vertically scrollable parent — use a single `LazyColumn` with mixed content types instead
- Do not use `MutableState` in ViewModels — use `StateFlow` and collect in Compose instead
- Do not convert `visibility="gone"` to `alpha(0f)` — use conditional composition (omit the composable) instead
- Do not ignore Modifier ordering — `.clickable()` before `.padding()` is different from `.padding()` before `.clickable()`
- Do not keep dead XML layout files after migration — delete them to avoid confusion
- Do not migrate all screens at once — migrate one screen at a time, validate, then proceed
- Do not skip the interop layer for complex custom views — use `AndroidView` until a Compose equivalent exists
