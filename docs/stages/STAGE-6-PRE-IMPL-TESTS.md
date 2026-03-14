# Stage 6: Pre-Implementation Tests (TDD Red Phase) — AUDIT

> **Purpose:** Audit whether `core/.claude/` has everything needed to write comprehensive test suites before implementation (TDD red phase) — fully autonomously.
> **Runs In:** Dedicated Claude Code context window
> **Depends On:** Stage 2 (Plan — task list with test types) + Stage 5 (Schema — DB models for test fixtures)
> **Last Updated:** 2026-03-14
> **Status:** AUDIT COMPLETE

---

## Diagrams

### Diagram A — Internal Workflow Flow

```
 ┌─────────────────────────────────────────────────────────────────┐
 │           STAGE 6: PRE-IMPLEMENTATION TESTS (TDD RED)           │
 └─────────────────────────────────────────────────────────────────┘

        ┌───────────────────────┐
        │  Read Plan from ST2   │
        │  + Schema from ST5    │
        └───────────┬───────────┘
                    │
                    ▼
  ┌──────────────────────────────┐
  │  Test Matrix Generation      │
  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │
  │  test-generator skill        │
  │  • Map PRD REQ → test cases  │
  │  • Test pyramid distribution │
  │  • Coverage target: 80% line │
  └──────────────┬───────────────┘
                 │
                 ▼
  ┌──────────────────────────────┐
  │  Unit Test Stubs (Red)       │
  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │
  │  tdd skill (AAA pattern)     │
  │  • All tests MUST FAIL       │
  │  • Arrange-Act-Assert        │
  │  • Property-based (Hypothesis│
  │    / fast-check)             │
  └──────────────┬───────────────┘
                 │
                 ▼
  ┌──────────────────────────────┐
  │  API Test Stubs              │
  │  ░░░░░░░░░░░░░░░░░░░░░░░░░  │
  │  • CRUD operations           │
  │  • Auth / permissions        │
  │  • Contract tests (Pact)     │
  └──────────────┬───────────────┘
                 │
                 ▼
  ┌──────────────────────────────┐
  │  BDD / Gherkin Scenarios     │
  │  ░░░░░░░░░░░░░░░░░░░░░░░░░  │
  │  • Feature files             │
  │  • Step definitions          │
  │  • Given/When/Then format    │
  └──────────────┬───────────────┘
                 │
                 ▼
  ┌──────────────────────────────┐
  │  E2E + Perf + Security Stubs │
  │  ░░░░░░░░░░░░░░░░░░░░░░░░░  │
  │  • Playwright POM skeletons  │
  │  • k6 performance stubs      │
  │  • Security checklist        │
  │  • a11y test stubs (axe)     │
  └──────────────┬───────────────┘
                 │
                 ▼
  ┌──────────────────────────────┐
  │  Mutation Testing Setup      │
  │  ░░░░░░░░░░░░░░░░░░░░░░░░░  │
  │  • mutmut (Python)           │
  │  • Stryker (JS/TS)           │
  └──────────────┬───────────────┘
                 │
                 ▼
  ┌──────────────────────────────┐
  │  Red Phase Gate              │
  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │
  │  Run ALL tests — verify     │
  │  100% FAIL or SKIP (E2E)   │
  │  Zero passing tests allowed │
  └──────────────┬───────────────┘
                 │
            PASS │ / FAIL → fix test
                 ▼
  ┌──────────────────────────────┐
  │  Structured JSON Output      │
  │  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓  │
  │  test-results/               │
  │  test-generator.json         │
  └──────────────┬───────────────┘
                 │
                 ▼
       ┌──────────────────┐
       │  Test Suite Out   │
       │  ████████████████ │
       └──────────────────┘
```

### Diagram B — I/O Artifact Contract

```
                          INPUTS
 ┌──────────────────────────────────────────────┐
 │                                              │
 │  ┌──────────────────┐ ┌──────────────────┐   │
 │  │ From ST2: plan.md│ │ From ST5:        │   │
 │  │  • Task list     │ │  • DB models     │   │
 │  │  • Test types    │ │  • Test fixtures  │   │
 │  │  • REQ→AC map    │ │  • Factory funcs  │   │
 │  └────────┬─────────┘ └────────┬─────────┘   │
 │           │                    │              │
 └───────────┼────────────────────┼──────────────┘
             │                    │
             └─────────┬──────────┘
                       │
                       ▼
      ┌──────────────────────────────────┐
      │                                  │
      │  ███ STAGE 6: PRE-TESTS ███      │
      │                                  │
      │  test-generator                  │
      │  tdd                             │
      │  contract-test                   │
      │  playwright                      │
      │                                  │
      └──────────────┬───────────────────┘
                     │
       ┌─────────────┼──────────┬──────────────┐
       │             │          │              │
       ▼             ▼          ▼              ▼
 ┌───────────┐┌───────────┐┌──────────┐ ┌───────────┐ ┌──────────┐
 │ tests/    ││ tests/    ││ tests/   │ │ tests/    │ │ test-    │
 │ unit/     ││ api/      ││ e2e/     │ │ perf/     │ │ results/ │
 │ (failing) ││ (failing) ││ (skipped │ │ (k6 stubs)│ │ test-gen │
 │           ││ + Pact    ││  stubs   │ │           │ │ .json    │
 │           ││ contracts ││  + POM)  │ │           │ │ (gate)   │
 └─────┬─────┘└─────┬─────┘└────┬─────┘ └─────┬─────┘ └────┬─────┘
       │            │           │              │             │
       ▼            ▼           ▼              ▼             ▼
 ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
 │ ST7 Impl │ │ ST7 Impl │ │ ST8 Post │ │ ST8 Post │ │ ST0 Orch │
 │ (make    │ │ (make    │ │ (remove  │ │ (run     │ │ (gate    │
 │  pass)   │ │  pass)   │ │  skip,   │ │  against │ │  valid.) │
 │          │ │          │ │  assert) │ │  deploy) │ │          │
 └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘
                   OUTPUTS
```

## Capability Checklist

| # | Capability | Existing Skill/Agent | Status | SE Standard |
|---|-----------|---------------------|--------|-------------|
| 1 | TDD red-green-refactor (red phase) | `tdd` skill (6 TDD patterns) | ✅ Covered | **Kent Beck TDD** |
| 2 | Unit test writing (AAA pattern) | `tdd` skill + `tester` agent | ✅ Covered | — |
| 3 | API test stubs (CRUD + auth) | `test-generator` (Step 5) | ✅ Covered | — |
| 4 | E2E test skeletons (Page Objects) | `test-generator` (Step 6) + `playwright` skill (POM pattern) | ✅ Covered | — |
| 5 | Performance test stubs (k6) | Stage 6 prompt | ✅ Covered | — |
| 6 | Security test stubs | `test-generator` (Step 5: API auth tests) | ✅ Covered | — |
| 7 | Test matrix (PRD req → test mapping) | `test-generator` (Step 1) | ✅ Covered | **Requirements Traceability** |
| 8 | Test fixtures from Stage 5 factories | `test-generator` (Step 4.3: factories + isolation patterns) | ✅ Covered | — |
| 9 | BDD / Gherkin scenarios | `test-generator` (Step 7: feature files + step defs) | ✅ Covered | **BDD (Dan North)** |
| 10 | Contract testing (consumer-driven) | `contract-test` skill (Pact consumer/provider, broker, CI) | ✅ Covered | **Consumer-Driven Contracts (Pact)** |
| 11 | Mutation testing setup | `test-generator` (Step 10: mutmut/Stryker config) | ✅ Covered | **Mutation Testing (Pitest/Stryker)** |
| 12 | Test coverage threshold enforcement | `test-generator` (Step 9: pytest-cov / vitest thresholds) | ✅ Covered | **Code Coverage Standards** |
| 13 | Property-based testing | `test-generator` (Step 8: Hypothesis / fast-check) | ✅ Covered | **Property-Based Testing (Hypothesis/fast-check)** |
| 14 | Snapshot testing | `test-generator` (Step 11: data snapshots) + `verify-screenshots` (visual) | ✅ Covered | — |
| 15 | Test data isolation (per-test DB transactions) | `test-generator` (Step 3 + Step 4.3: conftest.py + factories) | ✅ Covered | **Test Isolation** |
| 16 | Accessibility testing stubs | `test-generator` (Step 12: axe-core + Playwright a11y) | ✅ Covered | **WCAG 2.1 AA** |
| 17 | E2E stub format (skip + POM) | `test-generator` (Step 6: skipped stubs with Page Objects) | ✅ Covered | — |
| 18 | Shared test infrastructure | `test-generator` (Step 3: conftest.py / setupTests.ts) | ✅ Covered | — |
| 19 | Red phase gate verification | `test-generator` (Step 13: run tests, verify 100% fail/skip) | ✅ Covered | **TDD Red Phase** |
| 20 | Structured JSON output | `test-generator` (Step 14: test-results/test-generator.json) | ✅ Covered | **Stage Gate Protocol** |
| 21 | Decision criteria (BDD/property/contract) | `test-generator` (Steps 7.4, 8.3, contract criteria) | ✅ Covered | — |

## SE Best Practices Validation

| Standard | Relevant Aspect | Coverage |
|----------|----------------|----------|
| **Kent Beck TDD** | Red-green-refactor cycle, test-first development | ✅ Red phase explicitly enforced — all tests must fail |
| **BDD (Dan North)** | Behavior specs in Given/When/Then format, stakeholder-readable | ✅ Gherkin feature files + step definitions in `test-generator` Step 7 |
| **Consumer-Driven Contracts** | API consumers define expected contract, provider validates | ✅ `contract-test` skill with Pact consumer/provider, broker, CI integration |
| **Mutation Testing** | Verify test suite quality by injecting faults | ✅ mutmut/Stryker setup + interpretation guide in `test-generator` Step 10 |
| **Code Coverage** | Minimum coverage thresholds (line, branch, function) | ✅ 80% line / 70% branch thresholds enforced in `test-generator` Step 9 |
| **Property-Based Testing** | Generate random inputs to find edge cases (Hypothesis, fast-check) | ✅ Hypothesis + fast-check templates in `test-generator` Step 8 |
| **Test Pyramid** | More unit tests than integration, more integration than E2E | ✅ Test matrix in `test-generator` Step 1 structures by category count |
| **Snapshot Testing** | Lock down output shapes to detect unintended changes | ✅ Data snapshots in `test-generator` Step 11 + visual via `verify-screenshots` |
| **Stage Gate Protocol** | Machine-readable pass/fail for pipeline orchestration | ✅ Structured JSON output in `test-generator` Step 14 per `testing.md` rule |

## Gap Proposals (All Resolved)

### Gap 6.1: `test-generator` skill (Priority: P1) — ✅ RESOLVED

**Resolution:** `test-generator` skill created (2026-03-13) and expanded (2026-03-14) to 14 steps covering: shared test infrastructure, unit/API/E2E/BDD/property/snapshot stubs, coverage thresholds, mutation testing, red phase gate verification, and structured JSON output.

### Gap 6.2: `contract-test` skill (Priority: P2) — ✅ RESOLVED

**Resolution:** `contract-test` skill created (2026-03-13) with Pact consumer/provider/broker workflow. Decision criteria added to `test-generator` for when contract tests apply (multi-service) vs when to skip (monoliths).

### Gap 6.3: Security artifact mismatch (Priority: P1) — ✅ RESOLVED

**Problem:** Stage 6 listed `tests/security/checklist.md` as output, but Stage 8 produces `tests/security/threat-model.md` (STRIDE analysis). These are different documents with different purposes.

**Resolution:** Clarified that Stage 6 produces security test stubs as part of API tests (auth, permissions, injection prevention in `tests/api/`). Stage 8 produces the threat-model.md via `security-auditor` agent. No separate checklist artifact needed from Stage 6.

### Gap 6.4: Mobile E2E status stale (Priority: P2) — ✅ RESOLVED

**Problem:** Stack Coverage table listed "Mobile E2E: ❌" despite `android-run-e2e` and `flutter-e2e-test` skills existing.

**Resolution:** Updated to ✅ for Android/Flutter. Only iOS-native (XCUITest) remains uncovered; Maestro handles cross-platform flows.

## Input/Output Contract

| Produces | Consumed By | Format |
|----------|------------|--------|
| `tests/unit/` (failing tests) | Stage 7 (Impl — make them pass) | pytest/jest test files |
| `tests/api/` (failing tests) | Stage 7 (Impl — make them pass) | pytest/jest test files |
| `tests/e2e/` (skipped stubs with Page Objects) | Stage 8 (Post-Tests — remove skip, add assertions, run) | Playwright test files |
| `tests/bdd/` (feature files + step defs) | Stage 7 (Impl — make steps pass) | Gherkin + pytest-bdd/Cucumber |
| `tests/property/` (failing property tests) | Stage 7 (Impl — make them pass) | Hypothesis/fast-check test files |
| `tests/snapshots/` (snapshot test stubs) | Stage 7 (Impl — generate initial snapshots) | pytest-snapshot/Jest snapshot files |
| `tests/perf/` (k6 stubs) | Stage 8 (Post-Tests — run against deployed) | k6 scripts |
| `tests/conftest.py` / `tests/setupTests.ts` | Stage 7 + 8 (shared fixtures) | Framework config |
| `tests/factories.py` | Stage 7 + 8 (test data) | Factory functions |
| `test-results/test-generator.json` | Stage 0 (Orchestrator — gate validation) | JSON |
| Test matrix | Stage 8 (Post-Tests — verify all pass), Stage 9 (Review) | Table in stage doc |

## Research Targets

- **GitHub**: `TDD test generation AI`, `property-based testing patterns`, `consumer-driven contract testing`
- **Reddit**: r/softwaretesting — "TDD test-first AI coding", r/ExperiencedDevs — "test coverage strategy"
- **Twitter/X**: `TDD AI agent`, `test generation Claude Code`

## Stack Coverage

| Stack | Test Framework | Notes |
|-------|---------------|-------|
| Python (FastAPI) | ✅ pytest | AAA pattern, async support |
| Node/TypeScript | ✅ Jest/Vitest | Mentioned in prompt |
| E2E (any web) | ✅ Playwright | `playwright` skill |
| Performance | ✅ k6 | Stubs in prompt |
| Android | ✅ `android-test-patterns` | JUnit 5, Compose UI, Espresso, Room, coroutine test patterns |
| Mobile E2E (Android/Flutter) | ✅ `android-run-e2e` + `flutter-e2e-test` | Espresso/Compose + Maestro YAML flows + Flutter integration_test |
| Mobile E2E (iOS native) | ❌ | No XCUITest patterns (Maestro covers cross-platform flows) |

## Autonomy Verdict

**✅ Fully autonomous.** All 21 capabilities are ✅ covered. The `test-generator` skill (14 steps) now covers: shared test infrastructure generation (conftest.py/setupTests.ts), requirements-driven test matrix, E2E stub format (skipped tests with fully-defined Page Objects), BDD/Gherkin scenario generation with mandatory/optional criteria, property-based testing with decision guidance, snapshot testing (data + visual), coverage threshold configuration (reads from plan/config before defaults), mutation testing setup, accessibility test stubs, red phase gate verification (runs all tests, asserts 100% fail/skip), and structured JSON output for stage gate validation. Combined with `tdd` skill for red-green-refactor, `playwright` for E2E patterns, `contract-test` for Pact consumer-driven contracts (with decision criteria for when to use), `android-test-patterns` for Android, `android-run-e2e` + `flutter-e2e-test` for mobile E2E, and `verify-screenshots` for visual regression — no gaps remain. Only iOS-native XCUITest patterns are missing (Maestro covers cross-platform flows).

---

## Update Log

| Date | Change |
|------|--------|
| 2026-03-13 | Initial prompt design |
| 2026-03-13 | Rewritten as AUDIT with capability checklist, SE best practices, gap proposals |
| 2026-03-13 | P1 gap resolved: `test-generator` skill created with BDD/Gherkin, property-based testing, mutation testing, coverage enforcement, a11y stubs — 6 ❌ items flipped to ✅ |
| 2026-03-13 | P2 gap resolved: `contract-test` skill created with Pact consumer-driven contract testing |
| 2026-03-14 | Comprehensive autonomy review — 10 gaps fixed: (1) added structured JSON output to `test-generator` Step 14 for stage gate validation; (2) removed security checklist artifact mismatch with Stage 8 — Stage 6 produces security test stubs in tests/api/, Stage 8 produces threat-model.md; (3) defined E2E stub format (skip markers + fully-defined Page Objects) in Step 6; (4) added red phase gate verification (Step 13: run tests, assert 100% fail/skip); (5) fixed Mobile E2E status from ❌ to ✅ (android-run-e2e + flutter-e2e-test exist); (6) added decision criteria for BDD/property-based/contract tests; (7) added coverage threshold source priority (plan > config > defaults); (8) added snapshot testing (Step 11: data + visual) flipping capability #14 from ⚠️ to ✅; (9) added test file naming conventions; (10) added conftest.py/setupTests.ts generation (Step 3). All 21 capabilities now ✅ |
