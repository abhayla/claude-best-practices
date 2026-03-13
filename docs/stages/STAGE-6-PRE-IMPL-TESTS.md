# Stage 6: Pre-Implementation Tests (TDD Red Phase) — AUDIT

> **Purpose:** Audit whether `core/.claude/` has everything needed to write comprehensive test suites before implementation (TDD red phase) — fully autonomously.
> **Runs In:** Dedicated Claude Code context window
> **Depends On:** Stage 2 (Plan — task list with test types) + Stage 5 (Schema — DB models for test fixtures)
> **Last Updated:** 2026-03-13
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
  │  ░░░░░░░░░░░░░░░░░░░░░░░░░  │
  │  All tests run and FAIL      │
  │  (no implementation yet)     │
  └──────────────┬───────────────┘
                 │
            PASS │ / FAIL → retry
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
 ┌───────────┐┌───────────┐┌──────────┐ ┌───────────┐
 │ tests/    ││ tests/    ││ tests/   │ │ tests/    │
 │ unit/     ││ api/      ││ e2e/     │ │ perf/     │
 │ (failing) ││ (failing) ││ (skipped │ │ (k6 stubs)│
 │           ││ + Pact    ││  stubs)  │ │ security/ │
 │           ││ contracts ││          │ │ checklist │
 └─────┬─────┘└─────┬─────┘└────┬─────┘ └─────┬─────┘
       │            │           │              │
       ▼            ▼           ▼              ▼
 ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐
 │ ST7 Impl │ │ ST7 Impl │ │ ST8 Post │ │ ST8 Post │
 │ (make    │ │ (make    │ │ (fill in │ │ (execute │
 │  pass)   │ │  pass)   │ │  & run)  │ │  checks) │
 └──────────┘ └──────────┘ └──────────┘ └──────────┘
                   OUTPUTS
```

## Capability Checklist

| # | Capability | Existing Skill/Agent | Status | SE Standard |
|---|-----------|---------------------|--------|-------------|
| 1 | TDD red-green-refactor (red phase) | `tdd` skill (6 TDD patterns) | ✅ Covered | **Kent Beck TDD** |
| 2 | Unit test writing (AAA pattern) | `tdd` skill + `tester` agent | ✅ Covered | — |
| 3 | API test stubs (CRUD + auth) | Stage 6 prompt (Step 4) | ✅ Covered | — |
| 4 | E2E test skeletons (Page Objects) | `playwright` skill (POM pattern) | ✅ Covered | — |
| 5 | Performance test stubs (k6) | Stage 6 prompt (Step 6) | ✅ Covered | — |
| 6 | Security test checklist | Stage 6 prompt (Step 7) | ✅ Covered | — |
| 7 | Test matrix (PRD req → test mapping) | Stage 6 prompt (Step 2) | ✅ Covered | **Requirements Traceability** |
| 8 | Test fixtures from Stage 5 factories | Stage 6 prompt (Step 3.3) | ✅ Covered | — |
| 9 | BDD / Gherkin scenarios | `test-generator` (Step 5: feature files + step defs) | ✅ Covered | **BDD (Dan North)** |
| 10 | Contract testing (consumer-driven) | `contract-test` skill (Pact consumer/provider, broker, CI) | ✅ Covered | **Consumer-Driven Contracts (Pact)** |
| 11 | Mutation testing setup | `test-generator` (Step 8: mutmut/Stryker config) | ✅ Covered | **Mutation Testing (Pitest/Stryker)** |
| 12 | Test coverage threshold enforcement | `test-generator` (Step 7: pytest-cov / vitest thresholds) | ✅ Covered | **Code Coverage Standards** |
| 13 | Property-based testing | `test-generator` (Step 6: Hypothesis / fast-check) | ✅ Covered | **Property-Based Testing (Hypothesis/fast-check)** |
| 14 | Snapshot testing | `verify-screenshots` for visual; data snapshots via test factories | ⚠️ Partial | — |
| 15 | Test data isolation (per-test DB transactions) | `test-generator` (Step 3.3: factories + isolation patterns) | ✅ Covered | **Test Isolation** |
| 16 | Accessibility testing stubs | `test-generator` (Step 9: axe-core + Playwright a11y) | ✅ Covered | **WCAG 2.1 AA** |

## SE Best Practices Validation

| Standard | Relevant Aspect | Coverage |
|----------|----------------|----------|
| **Kent Beck TDD** | Red-green-refactor cycle, test-first development | ✅ Red phase explicitly enforced — all tests must fail |
| **BDD (Dan North)** | Behavior specs in Given/When/Then format, stakeholder-readable | ✅ Gherkin feature files + step definitions in `test-generator` Step 5 |
| **Consumer-Driven Contracts** | API consumers define expected contract, provider validates | ✅ `contract-test` skill with Pact consumer/provider, broker, CI integration |
| **Mutation Testing** | Verify test suite quality by injecting faults | ✅ mutmut/Stryker setup + interpretation guide in `test-generator` Step 8 |
| **Code Coverage** | Minimum coverage thresholds (line, branch, function) | ✅ 80% line / 70% branch thresholds enforced in `test-generator` Step 7 |
| **Property-Based Testing** | Generate random inputs to find edge cases (Hypothesis, fast-check) | ✅ Hypothesis + fast-check templates in `test-generator` Step 6 |
| **Test Pyramid** | More unit tests than integration, more integration than E2E | ✅ Test matrix in `test-generator` Step 1 structures by category count |

## Gap Proposals

### Gap 6.1: `test-generator` skill (Priority: P1)

**Problem it solves:** Test writing is manual via `tdd` skill or inline Stage 6 prompt. No skill auto-generates test stubs from requirements traceability matrix, schema, or API specs.

**What it needs:**
- Auto-generate unit, API, E2E test stubs from PRD requirements + schema
- BDD/Gherkin scenario generation for stakeholder-readable specs
- Coverage threshold configuration (line ≥80%, branch ≥70%) in gate check
- Property-based test templates (Hypothesis for Python, fast-check for JS)
- Mutation testing setup (Stryker for JS, mutmut for Python)

**Existing coverage:** `tdd` skill covers red-green-refactor workflow. `playwright` covers E2E. `tester` agent runs tests. None auto-generates from requirements.

### Gap 6.2: `contract-test` skill (Priority: P2)

**Problem it solves:** API tests verify response shape but no formal consumer-driven contract framework exists. Breaking API changes are only caught by downstream consumers failing, not by contract validation.

**What it needs:**
- Consumer-driven contract testing with Pact or similar
- Provider verification tests generated from consumer expectations
- Contract broker integration for cross-service validation

**Existing coverage:** API tests in Stage 6 prompt verify response structure manually.

## Input/Output Contract

| Produces | Consumed By | Format |
|----------|------------|--------|
| `tests/unit/` (failing tests) | Stage 7 (Impl — make them pass) | pytest/jest test files |
| `tests/api/` (failing tests) | Stage 7 (Impl — make them pass) | pytest/jest test files |
| `tests/e2e/` (skipped stubs) | Stage 8 (Post-Tests — fill in and run) | Playwright test files |
| `tests/perf/` (k6 stubs) | Stage 8 (Post-Tests — run against deployed) | k6 scripts |
| `tests/security/checklist.md` | Stage 8 (Post-Tests — execute checks) | Markdown checklist |
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
| Mobile E2E | ❌ | No Appium/Detox patterns |

## Autonomy Verdict

**✅ Can run autonomously.** `test-generator` skill now covers: requirements-driven test matrix, BDD/Gherkin scenario generation, property-based testing (Hypothesis/fast-check), mutation testing setup (mutmut/Stryker), coverage threshold enforcement (80% line / 70% branch), test data factories, and accessibility test stubs. Combined with existing `tdd` skill for red-green-refactor and `playwright` for E2E, all major capabilities are ✅. Only consumer-driven contract testing remains as a P2 gap.

---

## Update Log

| Date | Change |
|------|--------|
| 2026-03-13 | Initial prompt design |
| 2026-03-13 | Rewritten as AUDIT with capability checklist, SE best practices, gap proposals |
| 2026-03-13 | P1 gap resolved: `test-generator` skill created with BDD/Gherkin, property-based testing, mutation testing, coverage enforcement, a11y stubs — 6 ❌ items flipped to ✅ |
| 2026-03-13 | P2 gap resolved: `contract-test` skill created with Pact consumer-driven contract testing |
