# Cross-Framework Selector Philosophy

### The Intent Hierarchy

| Priority | Selector Type | Survives | Example Concept |
|----------|--------------|----------|-----------------|
| 1 | Accessibility role + name | Refactors, redesigns | "the Submit button" |
| 2 | Label / visible text | Most refactors | "the Email field" |
| 3 | Explicit test ID | All refactors | `data-testid="checkout-btn"` |
| 4 | CSS class / type | Nothing | `.btn-primary`, `ElevatedButton` |

### Framework Equivalents

| Priority | Playwright | Flutter | Detox | Maestro |
|----------|-----------|---------|-------|---------|
| 1 (Role) | `getByRole('button', {name})` | `bySemanticsLabel('Submit')` | `by.label('Submit')` | `tapOn: "Submit"` |
| 2 (Label) | `getByLabel('Email')` | `bySemanticsLabel('Email')` | `by.label('Email')` | `tapOn: "Email"` |
| 3 (TestID) | `getByTestId('checkout')` | `byKey(Key('checkout'))` | `by.id('checkout')` | `tapOn: {id: "checkout"}` |
| 4 (CSS/Type) | `locator('.btn')` | `byType(ElevatedButton)` | `by.type('RCTTextInput')` | N/A |

### When to Add `data-testid` to Source Code

Add test IDs only when semantic selectors are insufficient:
- Dynamic content with no stable accessible name
- Multiple identical elements (e.g., list of "Delete" buttons)
- Third-party components that don't expose accessibility attributes
- Elements with text that changes by locale (i18n)

MUST NOT add `data-testid` to every element — it clutters markup and creates
a parallel naming system that drifts from the real UI.

### Selector Maintenance

When a test breaks due to a selector change:
1. First, try a more resilient selector (role > label > testid)
2. If the UI genuinely changed, update the selector — don't add a second
   selector "just in case"
3. Never fall back to XPath in production tests — XPath selectors break on
   any structural change

---

