---
paths:
  - "**/*.kt"
  - "**/*.kts"
description: Kotlin language idioms, null safety, scope functions, and KMP-specific patterns for Android projects.
---

# Kotlin Rules

## Null Safety

- NEVER use `!!` — prefer `?.`, `?:`, `requireNotNull()`, or `checkNotNull()`
- Use `?.let {}` for scoped null-safe operations
- Return nullable types from functions that can legitimately have no result

```kotlin
// BAD
val name = user!!.name

// GOOD
val name = user?.name ?: "Unknown"
val name = requireNotNull(user) { "User must be set before accessing name" }.name
```

## Immutability

- Prefer `val` over `var` — default to `val` and only use `var` when mutation is required
- Use `data class` for value types; use immutable collections (`List`, `Map`, `Set`) in public APIs
- Copy-on-write for state updates: `state.copy(field = newValue)`

## Naming

- `camelCase` for functions and properties
- `PascalCase` for classes, interfaces, objects, and type aliases
- `SCREAMING_SNAKE_CASE` for constants (`const val`)
- Name interfaces by behavior, not prefix: `Clickable` not `IClickable`

## Scope Functions

- `let` — null check + transform: `user?.let { greet(it) }`
- `run` — compute a result using receiver: `service.run { fetch(config) }`
- `apply` — configure an object: `builder.apply { timeout = 30 }`
- `also` — side effects: `result.also { log(it) }`
- Avoid nesting scope functions beyond 2 levels

## Extension Functions

- Place in a file named after the receiver type (`StringExt.kt`, `FlowExt.kt`)
- Keep scope limited — don't add extensions to `Any` or overly generic types

## Error Handling

- Use `Result<T>` or custom sealed types — not exceptions for control flow
- Use `runCatching {}` for wrapping throwable code
- NEVER catch `CancellationException` — always rethrow it

## DSL Builder Pattern

```kotlin
class HttpClientConfig {
    var baseUrl: String = ""
    var timeout: Long = 30_000
    private val interceptors = mutableListOf<Interceptor>()
    fun interceptor(block: () -> Interceptor) { interceptors.add(block()) }
}

fun httpClient(block: HttpClientConfig.() -> Unit): HttpClient {
    val config = HttpClientConfig().apply(block)
    return HttpClient(config)
}
```

## Sealed Types

Use sealed classes/interfaces for closed state hierarchies. Always use exhaustive `when` — no `else` branch:

```kotlin
sealed interface UiState<out T> {
    data object Loading : UiState<Nothing>
    data class Success<T>(val data: T) : UiState<T>
    data class Error(val message: String) : UiState<Nothing>
}
```

## KMP Testing

- Use backtick-quoted descriptive test names: `` fun `search with empty query returns all items`() ``
- Ktor: Use `MockEngine` for HTTP client testing
- SQLDelight: Use `JdbcSqliteDriver(JdbcSqliteDriver.IN_MEMORY)` for JVM tests
- Organize: `commonTest/` for shared, `androidUnitTest/` for Android, `iosTest/` for iOS

## Style Enforcement

- Use **ktlint** or **Detekt** for automated style checks
- Set `kotlin.code.style=official` in `gradle.properties`
