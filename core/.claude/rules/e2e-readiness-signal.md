---
description: >
  E2E tests MUST wait on an explicit app-emitted readiness signal after
  navigation, never a fixed wall-clock delay. Framework-agnostic: the app
  emits a ready attribute/event, the test waits on it.
globs: ["**/e2e/**/*", "**/tests/e2e/**/*", "**/*.e2e.*", "**/*.spec.ts", "**/*.cy.*"]
version: "1.0.0"
---

# E2E Readiness Signal — wait on a signal, not a timeout

The hub's `e2e-test-writing.md` and `testing.md` both forbid fixed delays in
E2E tests. This rule supplies the **positive** pattern they leave unstated:
the application emits an **explicit readiness signal**, and the test **waits on
that signal** instead of guessing a duration.

## The pattern (framework-agnostic)

1. The app sets an explicit marker once it is interactive — e.g. a
   `data-ready="true"` (or `data-hydrated="true"`) attribute on the root
   element after mount/hydration, or it dispatches a custom `app:ready` event.
2. The E2E test waits on that marker after every top-level navigation
   (`waitForSelector('[data-ready="true"]')` or equivalent), with a generous
   timeout for cold CI machines.
3. Centralize the wait in the base page object / navigation helper so every
   test inherits it; tests that navigate manually MUST replicate the wait.

This works across SSR-hydration and SPA-mount stacks (React, Vue, Svelte,
Angular) and any runner (Playwright, Cypress, WebdriverIO) — only the selector
syntax changes.

## MUST / MUST NOT

- MUST wait for the app-emitted readiness signal after every top-level
  navigation — not for a fixed timeout.
- MUST NOT use a fixed delay (`waitForTimeout(1500)` / `sleep`) as the **primary**
  ready signal. Fixed delays flake under CI load and waste wall-clock on fast
  machines — the same delay cannot serve both (a cold CI mount can exceed 2s
  while a warm reload is ~100ms).
- MUST NOT reuse the first-mount readiness signal as a proxy for downstream
  async state (API calls, dialog open, route-view swap). It fires once, on
  first mount; subsequent transitions need their own targeted waits.

## When fixed waits are still acceptable

Transient animation timings (dialog enter/leave, snackbar auto-dismiss) that
expose no clean DOM signal MAY use a short `waitForTimeout` — typically under
300ms — as a last resort. Annotate each occurrence with a comment explaining
why no selector-based wait was possible.

## CRITICAL RULES

- MUST have the app emit an explicit readiness signal and have E2E tests wait
  on it after navigation.
- MUST NOT substitute a fixed delay for the readiness signal.
- MUST NOT overload the first-mount signal as a wait for later async state.
