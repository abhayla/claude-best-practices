# STEP 2: Modifiers

### Default Parameter

Always provide `modifier: Modifier = Modifier` as the first optional parameter and apply it to the root layout element:

```kotlin
@Composable
fun UserCard(
    name: String,
    modifier: Modifier = Modifier   // MUST be present
) {
    Card(modifier = modifier) {      // Apply to root element
        Text(name)
    }
}
```

### Order Matters

Modifiers are applied sequentially. The order changes behavior:

```kotlin
// Padding is clickable (click area includes padding)
Modifier
    .clickable { onClick() }
    .padding(16.dp)

// Padding is NOT clickable (click area excludes padding)
Modifier
    .padding(16.dp)
    .clickable { onClick() }

// Background behind padding
Modifier
    .background(Color.Red)
    .padding(16.dp)

// Background inside padding
Modifier
    .padding(16.dp)
    .background(Color.Red)
```

### Chaining

Chain modifiers fluently. Extract repeated chains into extension functions:

```kotlin
fun Modifier.cardStyle() = this
    .fillMaxWidth()
    .padding(horizontal = 16.dp, vertical = 8.dp)
    .clip(RoundedCornerShape(12.dp))
```

### Slot-Based APIs

Design reusable composables with slot parameters for maximum flexibility:

```kotlin
@Composable
fun AppCard(
    modifier: Modifier = Modifier,
    header: @Composable () -> Unit = {},
    content: @Composable ColumnScope.() -> Unit,
    actions: @Composable RowScope.() -> Unit = {}
) {
    Card(modifier = modifier) {
        Column {
            header()
            Column(content = content)
            Row(horizontalArrangement = Arrangement.End, content = actions)
        }
    }
}
```

Slot parameters let callers inject arbitrary composables without the component needing to know their structure.

---

