# TypeScript (fast-check)

#### TypeScript (fast-check)

```typescript
import fc from 'fast-check';

// Test: encode/decode roundtrip
fc.assert(
  fc.property(fc.string(), (input) => {
    expect(decode(encode(input))).toEqual(input);
  })
);

// Test: sorted output is always sorted
fc.assert(
  fc.property(fc.array(fc.integer()), (arr) => {
    const sorted = sortFunction(arr);
    for (let i = 1; i < sorted.length; i++) {
      expect(sorted[i]).toBeGreaterThanOrEqual(sorted[i - 1]);
    }
  })
);

// Test: API validates all inputs (no 500s)
fc.assert(
  fc.property(fc.record({ name: fc.string(), email: fc.emailAddress() }), async (input) => {
    const res = await fetch('/api/users', { method: 'POST', body: JSON.stringify(input) });
    expect(res.status).not.toBe(500); // Must validate, not crash
  }),
  { numRuns: 1000 }
);
```

