# STEP 12: Accessibility Test Stubs

## STEP 12: Accessibility Test Stubs

For projects with UI, generate a11y test stubs:

```typescript
// tests/a11y/test_<page>.ts

import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("home page passes WCAG 2.1 AA", async ({ page }) => {
  await page.goto("/");
  const results = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa"])
    .analyze();
  expect(results.violations).toEqual([]);
});
```

Generate one a11y test per page/screen identified in the PRD.

---

