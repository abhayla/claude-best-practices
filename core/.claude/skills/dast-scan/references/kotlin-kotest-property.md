# Kotlin (Kotest Property)

#### Kotlin (Kotest Property)

```kotlin
class UserPropertyTest : FunSpec({
    test("serialization roundtrip preserves data") {
        checkAll(Arb.string(), Arb.int(), Arb.boolean()) { name, age, active ->
            val user = User(name, age, active)
            val restored = User.fromJson(user.toJson())
            restored shouldBe user
        }
    }

    test("repository never returns more items than limit") {
        checkAll(Arb.int(1..100)) { limit ->
            val results = repository.search("test", limit = limit)
            results.size shouldBeLessThanOrEqual limit
        }
    }
})
```

