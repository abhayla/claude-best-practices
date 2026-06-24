# Web-First Assertions & Wait Strategy

### Framework Auto-Wait Equivalents

| Framework | Auto-Wait Assertion | Explicit Wait | NEVER Use |
|-----------|-------------------|---------------|-----------|
| Playwright | `expect(locator).toBeVisible()` | `page.waitForResponse()` | `page.waitForTimeout()` |
| Flutter | `tester.pumpAndSettle()` | `pump(Duration(...))` | `Future.delayed()` |
| Detox | `waitFor(el).toBeVisible()` | `.withTimeout(5000)` | `sleep()` |
| Cypress | `cy.get().should('be.visible')` | `cy.intercept().wait()` | `cy.wait(5000)` |
| Maestro | Implicit (auto-waits) | `waitForAnimationToEnd` | N/A |

### Wait Strategy Decision Tree

1. **Element visibility?** → Use auto-wait assertion (`toBeVisible()`, `pumpAndSettle()`)
2. **API response needed?** → Wait for specific response (`waitForResponse('/api/data')`)
3. **Animation completing?** → Wait for animation end or disable animations in test config
4. **State transition?** → Poll for condition with timeout (see Message Queue section)
5. **Nothing else works?** → You likely have a test design problem, not a timing problem

### Content Assertions Beyond Visual

Screenshots catch visual bugs but miss data correctness. Pair every visual
check with content assertions:

| Check | What It Catches |
|-------|----------------|
| Element visible | Layout rendering |
| Text content present | Data loaded (not empty state) |
| No error messages visible | No server errors or validation failures |
| Correct count of items | Data completeness (not truncated) |
| No placeholder text visible | Data replaced loading states |

### Calculation Verification — use the API as the oracle

For apps that render **computed values** (totals, projections, scores, rates),
scraping the rendered number is the wrong oracle — it couples the test to display
formatting and Vuetify/render timing, and it tests the formatter, not the
calculation. Instead, fetch the computed value from the **API** and compare:

- **Fetch from the API, not the DOM** — request the calculated value directly
  (the test runner's HTTP client carries auth); this tests the actual calculation
  logic and sidesteps render-timing flake.
- **Compare with a tolerance, not equality** — floating-point and cross-module
  rounding make exact equality flaky. Use a percentage tolerance (e.g. 1% within
  a module, up to ~5% across modules where rounding accumulates).
- **Validate empty/error states explicitly — never `test.skip()`** — assert the
  empty shape or the error status; skipping hides regressions.
- **Normalize units at the boundary** — an endpoint may return a rate as `3.5`
  or `0.035`; normalize before comparing so the test isn't unit-fragile.
- Reserve DOM-scraping for verifying the *formatter* (that `1500000` renders as
  the expected localized string) — a separate, smaller concern from "is the
  number correct."

This pairs with `core/.claude/rules/output-plausibility-verification.md`: the API
oracle confirms the value matches the computation; a plausibility bound confirms
the computation itself is domain-sane.

---

