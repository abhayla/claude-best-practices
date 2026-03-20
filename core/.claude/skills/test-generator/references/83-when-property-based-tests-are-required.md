# 8.3 When Property-Based Tests Are Required

### 8.3 When Property-Based Tests Are Required

Property-based tests are **mandatory** for domain logic with these patterns:
- **Serialization roundtrips** — `deserialize(serialize(x)) == x`
- **Idempotent operations** — `f(f(x)) == f(x)`
- **Invariants** — "balance is never negative", "list is always sorted after sort"
- **Commutativity** — `merge(a, b) == merge(b, a)`
- **Domain constraints** — "age is between 0 and 150", "price is non-negative"

Skip property-based tests for:
- Simple CRUD with no domain logic (pass-through to DB)
- UI rendering (use visual snapshot tests instead)
- External API wrappers (use contract tests instead)

---

