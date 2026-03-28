# E2E Edge Cases & Platform Gotchas

Environment and platform-specific issues that cause E2E flakiness. Each entry:
what happens, why, and how to mitigate.

---

## A/B Test Variants

**What happens:** Tests fail intermittently because the app shows different UI
variants to different sessions. A test expects "Sign Up" but sees "Get Started."

**Mitigation:**
- Force a deterministic variant in test environments via feature flag config
- Or use the reconnaissance pattern: discover the actual UI state before
  asserting, and branch test logic accordingly
- Never assert on A/B-variant text without controlling the variant assignment

## Feature Flags Changing Behavior Mid-Suite

**What happens:** A flag toggles between test runs (or mid-run if flags are
polled), causing some tests to see the new behavior while others see the old.

**Mitigation:**
- Pin all feature flags to known values in the test environment config
- Load flag state once at suite start, not per-test
- If testing flag behavior itself, create explicit tests for each variant

## Third-Party Widget Iframes (Cookie Consent, Chat, Ads)

**What happens:** Cookie consent banners, chat widgets, and ad iframes overlay
the page, intercepting clicks or blocking element visibility assertions.

**Mitigation:**
- Dismiss or suppress third-party widgets in test configuration:
  - Set cookies to bypass consent banners before test starts
  - Disable chat widget loading via environment variable or feature flag
  - Block third-party script URLs via network interception (`page.route()`)
- Never dismiss widgets via UI clicks in every test — fragile and slow

## Time-Zone Dependent Failures

**What happens:** Tests asserting on formatted dates/times pass locally
(UTC-5) but fail in CI (UTC). A test expects "March 28, 2026" but sees
"March 29, 2026" because of timezone offset.

**Mitigation:**
- Set a fixed timezone in test configuration: `TZ=UTC` env variable
- Use clock mocking (freezegun, jest.useFakeTimers) for time-sensitive tests
- Assert on relative time ("2 hours ago") or date components, not exact strings
- CI runners MUST use UTC — never assume local timezone

## CORS/CSP Blocking in E2E but Not Development

**What happens:** The app works in dev (relaxed CORS) but E2E tests fail
because CI uses stricter headers that block cross-origin API calls or
inline scripts.

**Mitigation:**
- Test environment MUST use production-equivalent CORS/CSP headers
- If E2E tests load from a different origin, configure the test server's
  CORS policy to allow the test origin
- Never disable CORS/CSP in tests — it masks real deployment issues

## Mobile Keyboard Covering Input Fields

**What happens:** On mobile emulators, the soft keyboard appears when tapping
an input field and covers the submit button or the next field. Taps on covered
elements fail silently or hit the wrong target.

**Mitigation:**
- Scroll the target element into view before interacting
- Use `scrollIntoViewIfNeeded` or equivalent framework method
- For form flows, dismiss keyboard after each field fill if it blocks the next
  field (tap outside the field or press the "Next"/"Done" key)
- In Flutter, use `tester.ensureVisible(finder)` before tapping

## Slow CI Runners Causing Timeout-Based Flakiness

**What happens:** Tests pass on fast developer machines but fail in CI where
shared runners have less CPU/memory. Operations that take 200ms locally take
2s+ in CI, exceeding default timeouts.

**Mitigation:**
- Set CI-specific timeouts higher than local defaults (2x–3x multiplier)
- Use auto-wait assertions (not fixed timeouts) so waits adapt to speed
- Reduce parallelism on resource-constrained runners (fewer workers = more
  CPU per worker)
- Monitor CI runner performance — flaky spikes often correlate with runner
  contention during peak hours

## Database Migration State Mismatch

**What happens:** E2E tests run against a database with stale migrations —
new columns are missing, constraints differ, or seed data doesn't match
the current schema. Tests fail with SQL errors that don't reproduce locally.

**Mitigation:**
- Always run migrations before E2E tests in CI (`alembic upgrade head`,
  `prisma migrate deploy`, `flyway migrate`)
- Use Testcontainers with migration-on-startup for guaranteed clean state
- Never share a persistent test database across CI runs without migration

## Font Rendering Variance Across OS/Browsers

**What happens:** Visual regression screenshots differ between macOS, Linux,
and Windows because font engines (CoreText, FreeType, DirectWrite) render
fonts differently. Anti-aliasing, hinting, and kerning all vary.

**Mitigation:**
- Pin the CI OS and browser version (e.g., `ubuntu-22.04`, Chromium 130)
- Use Docker containers for visual tests to ensure identical rendering
- Set a per-pixel tolerance threshold (0.1–0.5%) to absorb anti-aliasing
  differences without masking real visual regressions
- For mobile, pin emulator API level and screen density

## Anti-Aliasing Differences in Visual Comparisons

**What happens:** Pixel-diff tools flag anti-aliasing variations as failures.
A button with slightly different edge smoothing between renders triggers a
"visual regression" that is actually identical to the human eye.

**Mitigation:**
- Use perceptual diff (SSIM, YIQ) instead of pixel-exact comparison
- Set a tolerance threshold: 0.1% for design-system components, 0.5% for
  full-page screenshots
- Consider AI-powered visual comparison (Applitools) that ignores rendering
  artifacts and focuses on meaningful visual changes
- Mask areas with known variance (timestamps, avatars, animated elements)

## Network Interruption During E2E Flow

**What happens:** A transient network hiccup during an E2E test causes an
API call to fail, breaking a test that has nothing to do with network
resilience. Common in CI with shared infrastructure.

**Mitigation:**
- Configure test-level retries (`retries: 2` in Playwright, `--reruns 2`
  in pytest) with trace capture on first retry for diagnostics
- Mock external APIs that are not the system under test
- For internal services, ensure the test environment has stable networking
  (same Docker network, localhost loopback, no proxy)

## Race Conditions in Real-Time Features

**What happens:** Tests for WebSocket-powered features (live updates, chat,
notifications) fail because messages arrive before or after the assertion
window. The test checks for a notification that hasn't arrived yet, or one
that was already dismissed.

**Mitigation:**
- Use event-based waits: wait for the WebSocket message event, then assert
- Buffer received messages and assert against the buffer
- For live updates, poll the UI for the expected state change with a timeout
- Never assert on WebSocket message order unless the protocol guarantees it
