# STEP 11: Snapshot Test Stubs

### 11.1 Data Snapshots (Jest/Vitest)

```typescript
// tests/snapshots/api-responses.test.ts

import { describe, test, expect } from "vitest";

describe("API Response Snapshots", () => {
  test("GET /users/:id response shape", async () => {
    const response = await client.get("/users/1");
    // Snapshot locks down the response shape — breaks if fields change
    expect(response.json()).toMatchSnapshot();
  });

  test("error response shape", async () => {
    const response = await client.get("/users/nonexistent");
    expect(response.json()).toMatchSnapshot();
  });
});
```

### 11.2 Data Snapshots (pytest)

```python
