# Common Properties to Test

#### Common Properties to Test

| Property | Description | Example |
|----------|-------------|---------|
| **Roundtrip** | encode(decode(x)) == x | Serialization, encryption, compression |
| **Invariant** | f(x) satisfies condition for ALL x | Total >= 0, list length preserved |
| **Idempotent** | f(f(x)) == f(x) | Formatting, normalization, dedup |
| **Commutative** | f(a, b) == f(b, a) | Merge, union, max |
| **No crash** | f(x) doesn't throw for any valid x | API validation, parser |
| **Monotonic** | x <= y -> f(x) <= f(y) | Pricing, sorting |

