# 8.2 JavaScript/TypeScript (fast-check)

### 8.2 JavaScript/TypeScript (fast-check)

```typescript
// tests/property/user.property.test.ts

import fc from "fast-check";

test("email normalization is idempotent", () => {
  fc.assert(
    fc.property(fc.emailAddress(), (email) => {
      const normalized = normalizeEmail(email);
      expect(normalizeEmail(normalized)).toBe(normalized);
    })
  );
});
```

