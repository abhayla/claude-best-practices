# 6.2 Property-Based Testing

### 6.2 Property-Based Testing

Use generative testing to find edge cases that hand-written tests miss. Property-based tests generate thousands of random inputs and verify invariants hold.

| Stack | Library | Install |
|-------|---------|---------|
| Python | Hypothesis | `pip install hypothesis` |
| TypeScript/JS | fast-check | `npm install fast-check` |
| Kotlin/JVM | Kotest Property | `testImplementation("io.kotest:kotest-property")` |
| Go | rapid | `go get pgregory.net/rapid` |
| Rust | proptest | `cargo add proptest --dev` |

