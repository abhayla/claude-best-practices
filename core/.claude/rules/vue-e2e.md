---
description: Vuetify + Playwright E2E conventions — component animation timing, single-worker data-dependent suites, networkidle navigation, and the vee-validate fill() gotcha.
globs: ["**/e2e/**/*.ts", "**/*.spec.ts", "**/tests/e2e/**/*"]
---

# Vue E2E (Vuetify + Playwright)

## Navigation

Always use `networkidle` on `goto()` — Vuetify pages fire multiple API calls on mount and `load` fires too early.

```ts
await page.goto('/dashboard', { waitUntil: 'networkidle' })
```

## Component Timing

Vuetify components animate via CSS transitions and settle their internal state asynchronously. Wait after opening/closing overlay components before interacting.

| Component / Interaction | Wait | Reason |
|---|---|---|
| `.v-select` / `.v-menu` open | ~300ms | dropdown/menu animation |
| `.v-dialog` open | ~300ms then assert `.v-dialog` visible | enter transition |
| toggle / switch | 300–500ms | ripple + state update |
| `.v-snackbar` | assert visible + `toContainText(...)` | async mount |
| form submit | `waitForResponse(...)` | API round-trip |

```ts
// Select pattern
await page.locator('.v-select').filter({ hasText: /status/i }).click()
await page.waitForTimeout(300)
await page.getByRole('option', { name: /active/i }).click()

// Dialog pattern
await page.getByRole('button', { name: /add item/i }).click()
await page.waitForTimeout(300)
await expect(page.locator('.v-dialog')).toBeVisible()
```

Use `.catch(() => {})` only on waits for genuinely optional UI (charts, badges, tooltips) that may not render in every state — never to paper over a flaky required element.

## Config for Data-Dependent Suites

When a setup spec seeds data that later specs read, run serially — parallel workers cause data races.

```ts
// playwright.config.ts
export default defineConfig({
  workers: 1,
  fullyParallel: false,
  retries: process.env.CI ? 2 : 0,
  use: {
    navigationTimeout: 30000,
    storageState: 'e2e/.auth/user.json',  // reuse auth — no per-test login
  },
})
```

## The vee-validate `fill()` Gotcha

Forms wired through `useForm({ validationSchema })` + `defineField()` CANNOT be driven reliably by `page.locator(...).fill()`. Playwright's synthetic `input` events do not propagate through `defineField`'s reactive layer — especially numeric inputs with `v-model.number`, which silently fail to coerce. The symptom is quiet: `if (!isValid.value) return` short-circuits the submit, no request fires, and the test times out waiting for a response that never comes.

Use `pressSequentially` + `blur` instead:

```ts
const fillVVNumber = async (label: string, value: string) => {
  const field = page.getByLabel(label)
  await field.click()
  await field.fill('')                                  // clear
  await field.pressSequentially(value, { delay: 10 })   // per-char events
  await field.blur()                                    // flush change handlers
  await page.waitForTimeout(100)                         // let reactivity settle
}
```

If an auto-calc watcher derives a field from these inputs, wait on the observable rendered output (e.g. a computed summary leaving its `-` placeholder) before clicking submit. Do NOT reach into form state via `page.evaluate` — the vee-validate internal state will desync from the template refs and submit still fails validation.

Plain `ref()` + `v-model` forms drive cleanly via `fill()` — prefer them, and reserve vee-validate for genuine cross-field validation complexity.

## Anti-Patterns

- NEVER use `fill()` on a `defineField`-bound numeric input — use the `pressSequentially` + `blur` helper
- NEVER set `defineField` values via `page.evaluate` — it desyncs vee-validate's internal state from the template
- NEVER run a data-dependent suite with `workers > 1` or `fullyParallel: true` — seed/read ordering races
- NEVER use `waitUntil: 'load'` for Vuetify pages — they fetch on mount; use `networkidle`
- NEVER use a blanket `.catch(() => {})` to silence a required element's wait — reserve it for optional UI only
