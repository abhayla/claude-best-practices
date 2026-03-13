# Stage 8: Post-Implementation Tests (E2E, Visual, Perf, Security) — AUDIT

> **Purpose:** Audit whether `core/.claude/` has everything needed to run all tests requiring working code — E2E, visual regression, performance, security scans, web quality — fully autonomously.
> **Runs In:** Dedicated Claude Code context window
> **Depends On:** Stage 7 (Implementation — all unit/API tests passing)
> **Last Updated:** 2026-03-13
> **Status:** AUDIT COMPLETE

---

## Capability Checklist

| # | Capability | Existing Skill/Agent | Status | SE Standard |
|---|-----------|---------------------|--------|-------------|
| 1 | E2E user journey testing | `playwright` skill (POM, cross-browser) | ✅ Covered | — |
| 2 | Cross-browser testing | `playwright` skill (Chromium, Firefox, WebKit) | ✅ Covered | — |
| 3 | Visual regression testing | `verify-screenshots` skill | ✅ Covered | — |
| 4 | Performance/load testing (k6) | Stage 8 prompt (Step 4) | ✅ Covered | — |
| 5 | Web quality audit (Lighthouse, CWV) | `web-quality` skill | ✅ Covered | — |
| 6 | SAST (CodeQL, Semgrep) | `security-audit` skill | ✅ Covered | **OWASP Top 10** |
| 7 | Supply chain audit | `supply-chain-audit` skill | ✅ Covered | — |
| 8 | STRIDE threat modeling | `security-auditor` agent | ✅ Covered | **STRIDE (Microsoft)** |
| 9 | Manual security checklist execution | Stage 8 prompt (Step 5.3) | ✅ Covered | — |
| 10 | Test results report generation | Stage 8 prompt (Step 6) | ✅ Covered | — |
| 11 | DAST (Dynamic Application Security Testing) | `dast-scan` skill (ZAP, Nuclei, headers, sessions, fuzzing) | ✅ Covered | **OWASP DAST** |
| 12 | Chaos / resilience testing | `chaos-resilience` skill (failure injection, degradation, gameday) | ✅ Covered | **Chaos Engineering (Netflix)** |
| 13 | Compliance testing (GDPR, SOC2, HIPAA) | None | ❌ Missing | **Regulatory Compliance** |
| 14 | API fuzz testing | None — manual SQL injection/XSS but no automated fuzzing | ❌ Missing | **Fuzz Testing** |
| 15 | Accessibility E2E testing (automated) | `web-quality` covers Lighthouse a11y score, but no dedicated a11y E2E | ⚠️ Partial | **WCAG 2.1 AA** |
| 16 | Test flakiness detection | None — no retry/flake analysis | ❌ Missing | **Test Reliability** |
| 17 | Coverage diff (new code coverage) | None — overall coverage exists but no diff-coverage for new code | ⚠️ Partial | **Incremental Coverage** |

## SE Best Practices Validation

| Standard | Relevant Aspect | Coverage |
|----------|----------------|----------|
| **OWASP Testing Guide** | SAST + DAST + manual testing | ✅ SAST via `security-audit`, DAST via `dast-scan`, manual via Stage 8 prompt |
| **Chaos Engineering (Netflix)** | Resilience under failure conditions | ✅ `chaos-resilience` skill with failure injection, graceful degradation, gameday planning |
| **GDPR / SOC2 / HIPAA** | Compliance-specific test suites | ❌ No compliance testing framework |
| **Fuzz Testing** | Automated random input generation to find crashes/security bugs | ❌ Manual injection tests only |
| **WCAG 2.1 AA** | Automated accessibility testing in E2E flows | ⚠️ Lighthouse score exists but no axe-core integration in Playwright |
| **Test Reliability** | Flake detection, retry policies, quarantine for flaky tests | ❌ No flakiness analysis |
| **Incremental Coverage** | Coverage only on changed/new lines | ⚠️ Overall coverage measured but no diff-coverage |

## Gap Proposals

### Gap 8.1: DAST integration (Priority: P1)

**Problem it solves:** SAST scans source code and manual tests cover common attacks, but no automated runtime scanning exists. DAST finds issues SAST can't: misconfigured headers, session management flaws, runtime injection vulnerabilities.

**What to add:**
- OWASP ZAP or Nuclei scanning against running application
- Automated header security check (HSTS, CSP, X-Frame-Options)
- Session management testing

**Existing coverage:** `security-audit` skill covers SAST (CodeQL + Semgrep). Manual checklist covers common attacks.

### Gap 8.2: Chaos / resilience testing (Priority: P2)

**Problem it solves:** No resilience testing — only happy-path and error-input testing. Production failures (DB down, network timeout, OOM) are not simulated.

**What to add:**
- Failure injection: kill DB mid-request, network timeout, disk full
- Verify graceful degradation: error pages, retry logic, circuit breakers

**Existing coverage:** None.

### Gap 8.3: `perf-test` skill (Priority: P2)

**Problem it solves:** k6 scripts are inline in Stage 8 prompt — not reusable outside the pipeline. No baseline comparison or automated regression detection.

**What it needs:**
- Dedicated skill for performance testing workflow (k6 + Lighthouse + bundle analysis)
- Baseline comparison and regression detection
- Automated threshold extraction from PRD NFRs

**Existing coverage:** k6 stubs in Stage 6/8 prompts. `web-quality` skill covers Lighthouse.

## Input/Output Contract

| Produces | Consumed By | Format |
|----------|------------|--------|
| `playwright-report/` | Stage 9 (Review — E2E evidence) | HTML report |
| `tests/visual/baselines/` | Future runs (visual regression baseline) | PNG images |
| `results/perf.json` | Stage 9 (Review — performance evidence), Stage 10 (Deploy — go/no-go) | JSON metrics |
| `tests/security/threat-model.md` | Stage 9 (Review — security sign-off) | Markdown |
| Test results summary | Stage 9 (Review — overall quality verdict) | Table in stage doc |

## Research Targets

- **GitHub**: `OWASP ZAP automation`, `k6 load testing patterns`, `chaos engineering tools`, `playwright accessibility`
- **Reddit**: r/QualityAssurance — "E2E testing strategy 2025", r/netsec — "DAST automation"
- **Twitter/X**: `chaos engineering microservices`, `DAST automated pipeline`

## Stack Coverage

| Stack | Test Coverage | Notes |
|-------|-------------|-------|
| Web (any) | ✅ Playwright + Lighthouse + k6 | Full E2E + perf + quality |
| API (any) | ✅ k6 + security-audit | Load + SAST |
| Android | ❌ | No Espresso/Compose test runner, no Android perf profiling |
| Mobile E2E | ❌ | No Appium/Detox |
| Desktop | ❌ | No Electron/Tauri testing |

## Autonomy Verdict

**✅ Can run autonomously.** Excellent skill coverage: `playwright`, `verify-screenshots`, `web-quality`, `security-audit`, `supply-chain-audit`, `semgrep-rules`, `dast-scan`, plus `security-auditor` and `tester` agents. DAST gap resolved with ZAP/Nuclei scanning, header security, session management, and API fuzzing. P2 gaps resolved: `chaos-resilience` for failure injection and `perf-test` for dedicated performance testing. Remaining minor gap: compliance testing (GDPR/SOC2/HIPAA).

---

## Update Log

| Date | Change |
|------|--------|
| 2026-03-13 | Initial prompt design |
| 2026-03-13 | Rewritten as AUDIT with capability checklist, SE best practices, gap proposals |
| 2026-03-13 | P1 gap resolved: `dast-scan` skill created with ZAP, Nuclei, header security, session testing, API fuzzing, CI integration — DAST ❌ flipped to ✅ |
| 2026-03-13 | P2 gaps resolved: `chaos-resilience` and `perf-test` skills created |
