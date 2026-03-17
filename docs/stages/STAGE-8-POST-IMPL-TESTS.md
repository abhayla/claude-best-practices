# Stage 8: Post-Implementation Tests (E2E, Visual, Perf, Security) — AUDIT

> **Purpose:** Audit whether `core/.claude/` has everything needed to run all tests requiring working code — E2E, visual regression, performance, security scans, web quality — fully autonomously.
> **Runs In:** Dedicated Claude Code context window
> **Depends On:** Stage 7 (Implementation — all unit/API tests passing)
> **Last Updated:** 2026-03-14
> **Status:** AUDIT COMPLETE — ORCHESTRATION PROMPT ADDED

---

## Diagrams

### Diagram A — Internal Workflow Flow

```
                    ┌─────────────────────────┐
                    │  Gather Working Code     │
                    │  + Test Suite             │
                    │  (from ST7 + ST6)        │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  Run Full Test Suite     │
                    │  (unit + API + E2E)      │
                    └────────────┬────────────┘
                                 │
                       ┌─────────┴─────────┐
                       │                   │
                   ✅ ALL PASS         ❌ FAILURES
                       │                   │
                       │                   ▼
                       │         ┌──────────────────┐
                       │         │  Analyze Failures │
                       │         │  (categorize:     │
                       │         │   code vs test)   │
                       │         └────────┬─────────┘
                       │                  │
                       │                  ▼
                       │         ┌──────────────────┐
                       │         │  Fix & Retry      │
                       │         │  (fix-loop, up to │
                       │         │   3 attempts)     │
                       │         └────────┬─────────┘
                       │                  │
                       │                  └──→ (re-run suite)
                       │
                       ▼
          ┌────────────────────────────┐
          │  Run Extended Test Types   │
          │  ▓ E2E (Playwright)        │
          │  ▓ Visual (screenshots)    │
          │  ▓ Performance (k6)        │
          │  ▓ Security (SAST + DAST)  │
          │  ▓ Accessibility (axe)     │
          │  ▓ Chaos (resilience)      │
          └────────────┬───────────────┘
                       │
                       ▼
          ┌────────────────────────────┐
          │  Coverage Check            │
          │  (≥80% line, ≥70% branch)  │
          └────────────┬───────────────┘
                       │
                       ▼
          ┌────────────────────────────┐
          │  Generate Test Results     │
          │  Report + Coverage Report  │
          └────────────────────────────┘
```

### Diagram B — I/O Artifact Contract

```
 ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
 ░  UPSTREAM INPUTS                                                      ░
 ░                                                                       ░
 ░  ┌───────────────────┐        ┌───────────────────┐                   ░
 ░  │  ST 7: IMPL       │        │  ST 6: PRE-TESTS  │                   ░
 ░  │                   │        │                   │                   ░
 ░  │  source code      │        │  tests/unit/      │                   ░
 ░  │  (all unit tests  │        │  tests/api/       │                   ░
 ░  │   passing)        │        │  tests/e2e/       │                   ░
 ░  │                   │        │  tests/perf/      │                   ░
 ░  │                   │        │  tests/snapshots/ │                   ░
 ░  └────────┬──────────┘        └────────┬──────────┘                   ░
 ░           │                            │                              ░
 ░░░░░░░░░░░░┼░░░░░░░░░░░░░░░░░░░░░░░░░░░┼░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
              │                            │
              ▼                            ▼
 ┌────────────────────────────────────────────────────────────────┐
 │                                                                │
 │               STAGE 8: POST-IMPLEMENTATION TESTS               │
 │               (E2E, Visual, Perf, Security)                    │
 │                                                                │
 │  █ playwright  █ verify-screenshots  █ web-quality             │
 │  █ security-audit  █ dast-scan  █ chaos-resilience             │
 │  █ a11y-audit  █ perf-test  █ supply-chain-audit               │
 │  █ cross-platform-visual  █ code-quality-gate                  │
 │                                                                │
 └──────┬──────────┬──────────┬──────────┬────────────────────────┘
        │          │          │          │
        ▼          ▼          ▼          ▼
 ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
 ░  DOWNSTREAM OUTPUTS                                                   ░
 ░                                                                       ░
 ░  playwright-     tests/visual/    results/      tests/security/       ░
 ░  report/         baselines/       perf.json     threat-model.md       ░
 ░  (HTML)          (PNG)            (metrics)     (STRIDE)              ░
 ░     │               │                │              │                 ░
 ░     ▼               ▼                ▼              ▼                 ░
 ░  ┌──────────────────────────────────────────────────────────┐         ░
 ░  │  ST 9: REVIEW                                            │         ░
 ░  │  (E2E evidence, perf evidence, security sign-off,        │         ░
 ░  │   overall quality verdict)                               │         ░
 ░  └──────────────────────────────────────────────────────────┘         ░
 ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
```

### Diagram C — Orchestration Step Sequencing

```
 STEP 1: Read Upstream
       │
       ▼
 STEP 2: Detect Project Type ──→ sets SKIP flags
       │
       ▼
 STEP 3: Run Full Test Suite (unit + API)
       │
       ├─ FAIL → STEP 3A: fix-loop (max 3) ──→ re-run
       │
       ▼
 ┌─────────────────── PARALLEL WAVE A ───────────────────┐
 │                                                       │
 │  STEP 4         STEP 5          STEP 6                │
 │  E2E Tests      Visual Tests    Security (SAST)       │
 │  (playwright    (verify-        (security-audit       │
 │   or mobile)    screenshots)     + supply-chain)      │
 │                                                       │
 └───────────────────────┬───────────────────────────────┘
                         │
 ┌─────────────── PARALLEL WAVE B ───────────────────────┐
 │  (requires running app for DAST + chaos)              │
 │                                                       │
 │  STEP 7         STEP 8          STEP 9                │
 │  Performance    DAST Scan       Chaos /               │
 │  (perf-test     (dast-scan)     Resilience            │
 │   + k6)                         (chaos-resilience)    │
 │                                                       │
 └───────────────────────┬───────────────────────────────┘
                         │
 ┌─────────────── PARALLEL WAVE C ───────────────────────┐
 │                                                       │
 │  STEP 10        STEP 11         STEP 12               │
 │  Accessibility  Web Quality     Cross-Platform        │
 │  (a11y-audit)   (web-quality)   Visual (if multi-     │
 │                                  platform)            │
 └───────────────────────┬───────────────────────────────┘
                         │
                         ▼
 STEP 13: Coverage & Quality Gate
       │
       ▼
 STEP 14: Gate — Aggregate Results → JSON
       │
       ▼
 STEP 15: Artifact Verification
```

---

## Orchestration Prompt

This section is the **runnable prompt** that the pipeline orchestrator dispatches to a Stage 8 agent. The agent follows these steps, invoking skills as specified. Steps within the same wave run in parallel via subagents.

### STEP 1: Read Upstream Artifacts

1. **Read Stage 1 PRD** — Find and read `docs/plans/<feature>-prd.md`. Extract:
   - Non-functional requirements (NFRs): response time targets, throughput, availability
   - Compliance requirements (GDPR, SOC2, HIPAA) — determines whether Step 6.3 compliance testing runs
   - User stories and acceptance criteria (drive E2E test scenarios)

2. **Read Stage 6 test inventory** — Identify test directories and what exists:
   - `tests/unit/` — Unit tests (from Stage 6, made green in Stage 7)
   - `tests/api/` — API/integration tests
   - `tests/e2e/` — E2E test skeletons (Playwright or Maestro)
   - `tests/perf/` — k6 performance test stubs
   - `tests/security/` — Security test artifacts

3. **Read Stage 7 verification** — Check `test-results/auto-verify.json` if it exists. Confirm all unit/API tests passed in Stage 7.

### STEP 2: Detect Project Type & Set Skip Flags

Scan the project root to determine which test types apply. Set skip flags for inapplicable steps:

| Indicator | Project Type | Skip |
|-----------|-------------|------|
| `package.json` + Playwright config | Web app | — (run all web tests) |
| `build.gradle` / `settings.gradle` | Android app | Skip Playwright, web-quality, Lighthouse |
| `pubspec.yaml` | Flutter app | Skip Playwright, web-quality |
| No UI directory (pure API/CLI) | API / CLI | Skip Playwright, visual regression, web-quality, a11y-audit |
| `docker-compose.yml` with services | Dockerized services | Enable chaos-resilience |
| No `docker-compose.yml` | No infra for chaos | Skip chaos-resilience |
| Multiple platform dirs (e.g., `android/` + `web/`) | Multi-platform | Enable cross-platform-visual |
| PRD has GDPR/SOC2/HIPAA references | Regulated | Enable compliance testing in security-audit |

Document detected type and skip decisions in the structured report (Step 14).

### STEP 3: Run Full Test Suite (Regression Baseline)

Run all existing unit + API tests to confirm Stage 7's work is intact:

```bash
# Detect and run test suite (adapt to detected stack)
# Python:  pytest tests/unit/ tests/api/ -v --tb=short
# JS/TS:  npx jest --passWithNoTests
# Android: ./gradlew test
# Flutter: flutter test
```

- **If ALL PASS** → Proceed to Step 4 (Wave A)
- **If FAILURES** → Invoke `/test-pipeline` to run the full fix→verify→commit chain with strict gates and screenshot proof:

```
/test-pipeline <failure_output>
```

Or invoke `/fix-loop` directly for a lighter-weight fix cycle:

```
/fix-loop <failure_output> retest_command: "<test command>" max_iterations: 3
```

If `fix-loop` reports UNRESOLVED after 3 iterations, set `regression_baseline` to `FAILED` and **halt** — do not proceed to extended tests with a broken baseline. Report the failure in Step 14.

### STEP 4: E2E Tests (Wave A — parallel with Steps 5, 6)

**Skip if:** project type is API/CLI (no UI).

#### 4.1 Web E2E (if web project)

Invoke `/playwright` to run E2E tests:

```
/playwright tests/e2e/ --browsers chromium,firefox,webkit
```

This runs Page Object Model E2E tests across all browsers. On failure, invoke `/fix-loop` with Playwright retest command (max 3 iterations).

#### 4.2 Mobile E2E (if Android/Flutter/React Native project)

Invoke `/android-run-e2e` for mobile E2E:

```
/android-run-e2e
```

For Flutter projects with Maestro flows:

```bash
maestro test e2e/maestro/ --format junit --output test-results/maestro-report.xml
```

### STEP 5: Visual Regression Tests (Wave A — parallel)

**Skip if:** project type is API/CLI (no UI), or no visual baselines exist.

Invoke `/verify-screenshots`:

```
/verify-screenshots tests/visual/baselines/
```

- If baselines don't exist yet (first run), capture them as the new baseline
- If baselines exist, compare current screenshots against them
- Flag MAJOR visual regressions as blocking failures

For multi-platform projects, also run `/cross-platform-visual` after per-platform screenshots are captured (deferred to Step 12).

### STEP 6: Security Testing — Static (Wave A — parallel)

#### 6.1 SAST

Invoke `/security-audit`:

```
/security-audit --scope full
```

This runs Semgrep + CodeQL, OWASP Top 10 mapping, variant analysis, and false-positive gating.

#### 6.2 Supply Chain Audit

Invoke `/supply-chain-audit`:

```
/supply-chain-audit
```

This checks dependencies for CVEs, typosquatting, abandoned packages, and license compliance.

#### 6.3 Compliance Testing (conditional)

If the PRD references GDPR, SOC2, or HIPAA requirements (detected in Step 2):

Run `security-audit` Step 9 specifically for compliance:
- GDPR checklist (8 requirements)
- SOC2 trust principles (5)
- HIPAA safeguards (7)
- Automated PII data flow mapping

Document compliance findings in `tests/security/compliance-report.md`.

### STEP 7: Performance Testing (Wave B — parallel with Steps 8, 9)

**Skip if:** no `tests/perf/` directory and no NFR performance targets in PRD.

Invoke `/perf-test` with NFR thresholds from Step 1:

```
/perf-test --thresholds-from docs/plans/<feature>-prd.md
```

This runs:
- k6 load tests (smoke, load, stress, spike profiles)
- Baseline comparison and regression detection
- Lighthouse performance scoring (if web project)
- Bundle size analysis (if web project)

Output: `results/perf.json` with metrics and pass/fail per threshold.

### STEP 8: DAST — Dynamic Security Scanning (Wave B — parallel)

**Skip if:** no running application available (pure library/CLI with no server).

Start the application if not already running:

```bash
# Use docker-compose or dev server
docker compose up -d  # or: npm run dev, uvicorn main:app, etc.
```

Invoke `/dast-scan` against the running application:

```
/dast-scan --target http://localhost:<port> --openapi-spec docs/api/openapi.yaml
```

This runs:
- Header security audit (HSTS, CSP, X-Frame-Options, X-Content-Type-Options)
- OWASP ZAP API scan + baseline spider scan
- Nuclei vulnerability templates
- Session management testing
- API fuzzing + property-based testing + mutation testing

### STEP 9: Chaos / Resilience Testing (Wave B — parallel)

**Skip if:** no `docker-compose.yml` or no infrastructure to inject failures into.

Invoke `/chaos-resilience`:

```
/chaos-resilience
```

This runs:
- Steady-state baseline capture
- Failure injection (service crash, network partition, latency, disk full, dependency timeout)
- Behavior observation during failure
- Resilience checklist verification (circuit breaker, backoff, graceful degradation, no data loss, recovery time)

### STEP 10: Accessibility Testing (Wave C — parallel with Steps 11, 12)

**Skip if:** project type is API/CLI (no UI).

Invoke `/a11y-audit`:

```
/a11y-audit --scope site --threshold 90
```

This runs:
- axe-core scanning via Playwright
- Lighthouse accessibility scoring
- WCAG 2.1 AA checklist (automated + manual checks)
- Color contrast verification (4.5:1 normal text, 3:1 large text)
- Keyboard & focus navigation testing

### STEP 11: Web Quality Audit (Wave C — parallel)

**Skip if:** project type is not a web application.

Invoke `/web-quality`:

```
/web-quality
```

This runs:
- Core Web Vitals (LCP < 2.5s, INP < 200ms, CLS < 0.1)
- SEO audit (meta tags, Open Graph, structured data, robots.txt)
- Progressive enhancement checks
- Responsive design verification
- Performance budget enforcement

### STEP 12: Cross-Platform Visual Consistency (Wave C — parallel)

**Skip if:** project targets a single platform only.

Invoke `/cross-platform-visual` for each shared feature:

```
/cross-platform-visual <feature-name> --platforms android,web,flutter
```

This compares the same UI across platforms, flagging MAJOR divergences (missing components, wrong layout) as blocking and MINOR divergences (font rendering) as informational.

### STEP 13: Coverage & Quality Gate

Invoke `/code-quality-gate`:

```
/code-quality-gate --full
```

This runs:
- **Coverage check** — Overall: ≥80% line coverage, ≥70% branch coverage
- **Coverage diff** — New/changed code: ≥80% line coverage via diff-cover
- **Complexity check** — No function exceeds cyclomatic complexity 10
- **Duplication scan** — ≤3% code duplication
- **SOLID principles checklist**
- **Structured logging audit** — PII check, JSON format, correlation IDs
- **Layer validation** — Clean Architecture boundary enforcement

### STEP 14: Gate — Aggregate Results & Write Structured Report

Collect all `test-results/*.json` files produced by the skills above and aggregate into a single gate report.

Write to `test-results/stage-8-post-tests.json`:

```json
{
  "stage": "stage-8-post-tests",
  "timestamp": "<ISO-8601>",
  "result": "PASSED",
  "project_type": "web",
  "skipped_steps": [],
  "steps": {
    "regression_baseline": "PASSED",
    "e2e_tests": "PASSED",
    "visual_regression": "PASSED",
    "sast": "PASSED",
    "supply_chain": "PASSED",
    "compliance": "SKIPPED",
    "performance": "PASSED",
    "dast": "PASSED",
    "chaos_resilience": "SKIPPED",
    "accessibility": "PASSED",
    "web_quality": "PASSED",
    "cross_platform_visual": "SKIPPED",
    "coverage_quality_gate": "PASSED"
  },
  "summary": {
    "total_tests_run": 342,
    "passed": 338,
    "failed": 0,
    "skipped": 4,
    "flaky": 2,
    "line_coverage_pct": 85.2,
    "branch_coverage_pct": 74.1,
    "security_findings_critical": 0,
    "security_findings_high": 0,
    "security_findings_medium": 1,
    "perf_p95_ms": 180,
    "lighthouse_score": 94,
    "a11y_score": 96
  },
  "failures": [],
  "warnings": [],
  "duration_ms": 0
}
```

**Gate logic:**

| Condition | Result |
|-----------|--------|
| `regression_baseline` is FAILED | **HALT** — do not proceed |
| Any step is FAILED (except SKIPPED) | `result` = `FAILED` |
| Any security finding is CRITICAL or HIGH | `result` = `FAILED` |
| Coverage below thresholds | `result` = `FAILED` |
| All active steps PASSED | `result` = `PASSED` |
| Some steps have warnings but none failed | `result` = `PASSED` with populated `warnings[]` |

Return structured JSON to orchestrator:

```json
{
  "gate": "PASSED",
  "artifacts": {
    "e2e_report": "playwright-report/",
    "visual_baselines": "tests/visual/baselines/",
    "perf_results": "results/perf.json",
    "threat_model": "tests/security/threat-model.md",
    "gate_report": "test-results/stage-8-post-tests.json"
  },
  "decisions": [],
  "blockers": [],
  "summary": "342 tests run (338 passed, 2 flaky, 4 skipped). 85.2% line coverage. 0 critical/high security findings. Lighthouse 94. a11y 96."
}
```

### STEP 15: Verify Output Artifacts

Before reporting completion, confirm all required artifacts exist on disk:

| Artifact | Path | Required When |
|----------|------|---------------|
| E2E report | `playwright-report/` or `test-results/maestro-report.xml` | Web or mobile project |
| Visual baselines | `tests/visual/baselines/` | UI project with visual tests |
| Performance results | `results/perf.json` | Performance tests ran |
| Threat model | `tests/security/threat-model.md` | Security audit ran |
| Compliance report | `tests/security/compliance-report.md` | Compliance testing ran |
| Gate report | `test-results/stage-8-post-tests.json` | Always |
| Individual skill results | `test-results/*.json` (per skill) | Always |

If any required artifact is missing, generate it before reporting completion. If generation fails, add to `blockers[]` in the orchestrator return.

---

## Capability Checklist

| # | Capability | Existing Skill/Agent | Status | SE Standard |
|---|-----------|---------------------|--------|-------------|
| 1 | E2E user journey testing | `playwright` skill (POM, cross-browser) | ✅ Covered | — |
| 2 | Cross-browser testing | `playwright` skill (Chromium, Firefox, WebKit) | ✅ Covered | — |
| 3 | Visual regression testing | `verify-screenshots` skill | ✅ Covered | — |
| 4 | Performance/load testing (k6) | `perf-test` skill (Step 7) | ✅ Covered | — |
| 5 | Web quality audit (Lighthouse, CWV) | `web-quality` skill (Step 11) | ✅ Covered | — |
| 6 | SAST (CodeQL, Semgrep) | `security-audit` skill (Step 6.1) | ✅ Covered | **OWASP Top 10** |
| 7 | Supply chain audit | `supply-chain-audit` skill (Step 6.2) | ✅ Covered | — |
| 8 | STRIDE threat modeling | `security-auditor-agent` (Step 6.1) | ✅ Covered | **STRIDE (Microsoft)** |
| 9 | Security checklist execution | `security-audit` skill (Step 6.1) | ✅ Covered | — |
| 10 | Test results report generation | Orchestration prompt (Step 14) | ✅ Covered | — |
| 11 | DAST (Dynamic Application Security Testing) | `dast-scan` skill (Step 8) | ✅ Covered | **OWASP DAST** |
| 12 | Chaos / resilience testing | `chaos-resilience` skill (Step 9) | ✅ Covered | **Chaos Engineering (Netflix)** |
| 13 | Compliance testing (GDPR, SOC2, HIPAA) | `security-audit` Step 9 (Step 6.3) | ✅ Covered | **Regulatory Compliance** |
| 14 | Fuzz testing (API + property-based + mutation) | `dast-scan` Step 6 (Step 8) | ✅ Covered | **Fuzz Testing** |
| 15 | Accessibility E2E testing (automated) | `a11y-audit` skill (Step 10) | ✅ Covered | **WCAG 2.1 AA** |
| 16 | Test flakiness detection & quarantine | `testing.md` rule + `fix-loop` (Step 3) | ✅ Covered | **Test Reliability** |
| 17 | Coverage diff (new code coverage) | `code-quality-gate` Step 8 (Step 13) | ✅ Covered | **Incremental Coverage** |
| 18 | Mobile E2E testing (cross-platform) | `android-run-e2e` (Step 4.2) | ✅ Covered | — |
| 19 | Cross-platform visual consistency | `cross-platform-visual` skill (Step 12) | ✅ Covered | — |

## SE Best Practices Validation

| Standard | Relevant Aspect | Coverage |
|----------|----------------|----------|
| **OWASP Testing Guide** | SAST + DAST + manual testing | ✅ SAST via `security-audit` (Step 6.1), DAST via `dast-scan` (Step 8), manual via `security-audit` checklist |
| **Chaos Engineering (Netflix)** | Resilience under failure conditions | ✅ `chaos-resilience` skill (Step 9) with failure injection, graceful degradation, gameday planning |
| **GDPR / SOC2 / HIPAA** | Compliance-specific test suites | ✅ `security-audit` Step 9 (Step 6.3): GDPR checklist (8 requirements), SOC2 trust principles (5), HIPAA safeguards (7), automated PII data flow mapping |
| **Fuzz Testing** | Automated random input generation to find crashes/security bugs | ✅ `dast-scan` Step 6 (Step 8): API input fuzzing + property-based testing (Hypothesis, fast-check, Kotest) + mutation testing (mutmut, Stryker, PIT) |
| **WCAG 2.1 AA** | Automated accessibility testing in E2E flows | ✅ `a11y-audit` skill (Step 10) with axe-core + Playwright + WCAG 2.1 AA checklist |
| **Test Reliability** | Flake detection, retry policies, quarantine for flaky tests | ✅ `testing.md` rule: prevention rules + detection commands + classification table + quarantine workflow (tagging, CI separation, weekly review) + health metrics |
| **Incremental Coverage** | Coverage only on changed/new lines | ✅ `code-quality-gate` Step 8 (Step 13): diff-cover tooling for Python/JS/Kotlin/Go, 80% threshold on new lines, per-file reporting, CI integration |

## Gap Proposals

### Gap 8.1: DAST integration (Priority: P1) — RESOLVED

**Problem it solves:** SAST scans source code and manual tests cover common attacks, but no automated runtime scanning exists. DAST finds issues SAST can't: misconfigured headers, session management flaws, runtime injection vulnerabilities.

**Resolution:** `dast-scan` skill created with ZAP, Nuclei, header security, session testing, API fuzzing, CI integration. Wired into orchestration Step 8.

### Gap 8.2: Chaos / resilience testing (Priority: P2) — RESOLVED

**Problem it solves:** No resilience testing — only happy-path and error-input testing. Production failures (DB down, network timeout, OOM) are not simulated.

**Resolution:** `chaos-resilience` skill created with failure injection, graceful degradation verification. Wired into orchestration Step 9 with skip-if-no-docker conditional.

### Gap 8.3: `perf-test` skill (Priority: P2) — RESOLVED

**Problem it solves:** k6 scripts were inline in the stage prompt — not reusable outside the pipeline. No baseline comparison or automated regression detection.

**Resolution:** `perf-test` skill created with k6, Lighthouse, baseline comparison, NFR threshold extraction. Wired into orchestration Step 7.

### Gap 8.4: No orchestration prompt (Priority: P0) — RESOLVED

**Problem it solves:** Stage 8 was an audit-only document listing capabilities but with no runnable orchestration prompt. The pipeline orchestrator had no executable instructions to dispatch. Capability rows referenced phantom "Stage 8 prompt" steps that didn't exist.

**Resolution:** Added 15-step orchestration prompt with: upstream artifact reading, project type detection with skip flags, regression baseline check, 3 parallel execution waves (A: E2E + Visual + SAST, B: Perf + DAST + Chaos, C: a11y + web-quality + cross-platform-visual), coverage/quality gate, structured JSON gate report for orchestrator, and artifact existence verification.

### Gap 8.5: No structured JSON return to orchestrator (Priority: P1) — RESOLVED

**Problem it solves:** Stages 4/5 defined JSON return format for Stage 0 but Stage 8 had no equivalent. The orchestrator couldn't programmatically determine pass/fail.

**Resolution:** Step 14 produces `test-results/stage-8-post-tests.json` with aggregated results plus a structured JSON return to the orchestrator with gate verdict, artifact paths, and summary.

### Gap 8.6: No skip/conditional logic (Priority: P2) — RESOLVED

**Problem it solves:** CLI/API projects don't need Playwright/visual/accessibility tests. Running all test types unconditionally wastes time and produces false failures.

**Resolution:** Step 2 detects project type by scanning for framework config files and sets skip flags per step. The gate report records which steps were skipped and why.

### Gap 8.7: No artifact existence verification (Priority: P2) — RESOLVED

**Problem it solves:** The I/O contract listed output artifacts but nothing verified they actually got created before marking the stage as passed.

**Resolution:** Step 15 checks all required artifacts exist on disk before reporting completion. Missing artifacts block the gate or trigger generation.

### Gap 8.8: No parallelism guidance (Priority: P2) — RESOLVED

**Problem it solves:** Some test types can run in parallel (SAST + E2E + visual) while others depend on a running app (DAST, chaos). Without ordering guidance, the agent runs everything sequentially.

**Resolution:** Diagram C and the orchestration prompt define 3 parallel waves: Wave A (no app dependency), Wave B (requires running app), Wave C (specialized audits). Steps within each wave run as parallel subagents.

### Gap 8.9: `cross-platform-visual` skill not tracked (Priority: P3) — RESOLVED

**Problem it solves:** The `cross-platform-visual` skill existed but wasn't referenced in Stage 8's capability checklist or orchestration.

**Resolution:** Added as capability #19 and wired into orchestration Step 12 (Wave C) with skip-if-single-platform conditional.

## Input/Output Contract

| Produces | Consumed By | Format |
|----------|------------|--------|
| `playwright-report/` | Stage 9 (Review — E2E evidence) | HTML report |
| `tests/visual/baselines/` | Future runs (visual regression baseline) | PNG images |
| `results/perf.json` | Stage 9 (Review — performance evidence), Stage 10 (Deploy — go/no-go) | JSON metrics |
| `tests/security/threat-model.md` | Stage 9 (Review — security sign-off) | Markdown |
| `tests/security/compliance-report.md` | Stage 9 (Review — compliance evidence) | Markdown |
| `test-results/stage-8-post-tests.json` | Stage 0 (Orchestrator — gate validation), Stage 9 (Review — overall verdict) | JSON |
| `test-results/*.json` (per skill) | Stage 9 (Review — per-skill detail) | JSON |

## Research Targets

- **GitHub**: `OWASP ZAP automation`, `k6 load testing patterns`, `chaos engineering tools`, `playwright accessibility`
- **Reddit**: r/QualityAssurance — "E2E testing strategy 2025", r/netsec — "DAST automation"
- **Twitter/X**: `chaos engineering microservices`, `DAST automated pipeline`

## Stack Coverage

| Stack | Test Coverage | Notes |
|-------|-------------|-------|
| Web (any) | ✅ Playwright + Lighthouse + k6 | Full E2E + perf + quality |
| API (any) | ✅ k6 + security-audit + dast-scan | Load + SAST + DAST |
| Android | ✅ `android-test-patterns` + `android-run-tests` + `android-run-e2e` (Maestro) | Test patterns, runner, Maestro E2E, perf profiling in `android-performance.md` |
| Mobile E2E | ✅ `android-run-e2e` (Maestro YAML flows) | Cross-platform: Android, iOS, React Native, Flutter |
| Multi-platform | ✅ `cross-platform-visual` | Visual consistency across Android, Web, Flutter |
| Desktop | ❌ | No Electron/Tauri testing |

## Autonomy Verdict

**✅ Can run fully autonomously.** The orchestration prompt sequences all 13 skills and 3 agents into a 15-step workflow with: project type detection (skip inapplicable tests), 3 parallel execution waves, fix-loop on failures, structured JSON gate report for the pipeline orchestrator, and artifact existence verification. All 19 capabilities ✅. Only remaining stack gap: desktop testing (Electron/Tauri).

---

## Update Log

| Date | Change |
|------|--------|
| 2026-03-13 | Initial prompt design |
| 2026-03-13 | Rewritten as AUDIT with capability checklist, SE best practices, gap proposals |
| 2026-03-13 | P1 gap resolved: `dast-scan` skill created with ZAP, Nuclei, header security, session testing, API fuzzing, CI integration — DAST ❌ flipped to ✅ |
| 2026-03-13 | P2 gaps resolved: `chaos-resilience` and `perf-test` skills created |
| 2026-03-13 | Audit refresh: row 14 ❌→⚠️ (`dast-scan` has API fuzzing), row 15 ⚠️→✅ (`a11y-audit` skill exists), row 16 ❌→⚠️ (`testing.md` rule covers prevention) |
| 2026-03-14 | All remaining gaps resolved: #13 compliance testing added to `security-audit` Step 9 (GDPR/SOC2/HIPAA checklists + data flow mapping) ❌→✅; #14 fuzz testing expanded in `dast-scan` Step 6 (property-based + mutation testing) ⚠️→✅; #16 flaky test detection added to `testing.md` rule (detection commands, classification, quarantine workflow, metrics) ⚠️→✅; #17 coverage diff added to `code-quality-gate` Step 8 (diff-cover tooling, thresholds, CI) ⚠️→✅; Mobile E2E added to `android-run-e2e` (Maestro cross-platform YAML flows) ❌→✅. All 18 capabilities now ✅ |
| 2026-03-14 | P0 gap resolved: Added 15-step orchestration prompt with project type detection, 3 parallel execution waves, structured JSON gate report, artifact verification. Added Diagram C (step sequencing). Fixed capability table references from phantom "Stage 8 prompt" to actual orchestration steps. Added `cross-platform-visual` as capability #19. Added `compliance-report.md` and `stage-8-post-tests.json` to I/O contract. All 6 secondary gaps (8.4–8.9) resolved. 19 capabilities ✅ |
