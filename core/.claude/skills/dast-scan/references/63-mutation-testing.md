# 6.3 Mutation Testing

### 6.3 Mutation Testing

Verify that tests actually catch bugs by injecting small mutations into source code and checking if tests fail.

| Stack | Tool | Command |
|-------|------|---------|
| Python | mutmut | `mutmut run --paths-to-mutate=src/` |
| TypeScript/JS | Stryker | `npx stryker run` |
| Kotlin/JVM | PIT (pitest) | `./gradlew pitest` |
| Go | go-mutesting | `go-mutesting ./...` |
| Rust | cargo-mutants | `cargo mutants` |

