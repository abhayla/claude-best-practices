# Stage 7: Implementation (TDD Green Phase)

> **Purpose:** Write production code that makes all Stage 6 failing tests pass — fully autonomously.
> **Runs In:** Dedicated Claude Code context window
> **Depends On:** Stage 6 (Pre-Impl Tests — all tests must be collected and failing)
> **Last Updated:** 2026-03-14
> **Status:** AUTONOMOUS PROMPT

---

## Diagrams

### Diagram A — Internal Workflow Flow

```
┌─────────────────────────────────────────────────────────┐
│              STAGE 7: IMPLEMENTATION (TDD GREEN)        │
│                                                         │
│  ┌───────────────────┐                                  │
│  │ Read Impl Plan &  │                                  │
│  │ Failing Tests     │                                  │
│  └────────┬──────────┘                                  │
│           ▼                                             │
│  ┌───────────────────┐                                  │
│  │ Select Next Task  │◄─────────────────────────┐       │
│  │ (wave execution)  │                          │       │
│  └────────┬──────────┘                          │       │
│           ▼                                     │       │
│  ┌───────────────────┐    ┌──────────────────┐  │       │
│  │ implement skill   │───▶│ Spawn subagents  │  │       │
│  │ (7-step workflow) │    │ (file ownership) │  │       │
│  └────────┬──────────┘    └────────┬─────────┘  │       │
│           ▼                        ▼            │       │
│  ┌───────────────────────────────────────────┐  │       │
│  │          Run Tests (auto-verify)          │  │       │
│  └────────┬──────────────────────┬───────────┘  │       │
│           ▼                      ▼              │       │
│     ┌──────────┐          ┌──────────┐          │       │
│     │  PASS ✓  │          │  FAIL ✗  │          │       │
│     └────┬─────┘          └────┬─────┘          │       │
│          │                     ▼                │       │
│          │            ┌──────────────────┐       │       │
│          │            │ fix-loop skill   │       │       │
│          │            │ (max 5 retries)  │       │       │
│          │            └────────┬─────────┘       │       │
│          │                     ▼                │       │
│          │              ┌───────────┐           │       │
│          │              │ Fixed?    │           │       │
│          │              │ YES → ─┐  │           │       │
│          │              │ NO  → HALT│           │       │
│          │              └──────┬────┘           │       │
│          ▼                     ▼                │       │
│  ┌───────────────────────────────────────────┐  │       │
│  │  code-quality-gate                        │  │       │
│  │  ├─ Complexity check (McCabe < 10)        │  │       │
│  │  ├─ Duplication (jscpd < 3%)              │  │       │
│  │  ├─ SOLID checklist                       │  │       │
│  │  ├─ Layer validation (Clean Arch)         │  │       │
│  │  ├─ Structured logging audit              │  │       │
│  │  ├─ Error handling audit                  │  │       │
│  │  └─ TDD Refactor phase                   │  │       │
│  └────────┬──────────────────────────────────┘  │       │
│           ▼                                     │       │
│  ┌───────────────────┐                          │       │
│  │ Git commit + tag  │                          │       │
│  └────────┬──────────┘                          │       │
│           ▼                                     │       │
│  ┌───────────────────┐     ┌─────┐              │       │
│  │ More tasks?       │────▶│ YES │──────────────┘       │
│  └────────┬──────────┘     └─────┘                      │
│           ▼                                             │
│     ┌──────────┐                                        │
│     │   NO     │                                        │
│     └────┬─────┘                                        │
│          ▼                                              │
│  ┌───────────────────┐                                  │
│  │ Lint + Type Check │                                  │
│  │ (final gate)      │                                  │
│  └────────┬──────────┘                                  │
│           ▼                                             │
│  ┌───────────────────┐                                  │
│  │ STAGE 7 COMPLETE  │                                  │
│  └───────────────────┘                                  │
└─────────────────────────────────────────────────────────┘
```

### Diagram B — I/O Artifact Contract

```
  ┌─────────────────────────┐    ┌─────────────────────────┐
  │  FROM STAGE 5 (Schema)  │    │ FROM STAGE 6 (Pre-Tests)│
  │                         │    │                         │
  │  • Implementation plan  │    │  • Failing test suite   │
  │  • Task dependency graph│    │  • Coverage targets     │
  └───────────┬─────────────┘    └───────────┬─────────────┘
              │                              │
              ▼                              ▼
  ┌───────────────────────────────────────────────────────┐
  │                                                       │
  │              ┌─────────────────────┐                  │
  │              │    STAGE 7          │                  │
  │              │  IMPLEMENTATION     │                  │
  │              │  (TDD Green Phase)  │                  │
  │              └─────────────────────┘                  │
  │                                                       │
  │  Skills: implement, executing-plans,                  │
  │          subagent-driven-dev, fix-loop,               │
  │          auto-verify, code-quality-gate,              │
  │          feature-flag, api-docs-generator             │
  │                                                       │
  └──────┬──────────────┬───────────────┬─────────────────┘
         │              │               │
         ▼              ▼               ▼
  ┌──────────────┐ ┌──────────────┐ ┌──────────────────┐
  │  TO STAGE 8  │ │  TO STAGE 9  │ │   TO STAGE 10    │
  │ (Post-Tests) │ │  (Review)    │ │   (Deploy)       │
  │              │ │              │ │                   │
  │ • Production │ │ • Source code│ │ • Git commits    │
  │   source code│ │ • Progress   │ │   (1 per task)   │
  │ • Passing    │ │   tracker    │ │ • Production     │
  │   tests      │ │ • Commit log │ │   source code    │
  └──────────────┘ └──────────────┘ └──────────────────┘
```

## Orchestration Prompt

This is the step-by-step workflow the Stage 7 agent executes autonomously.

### STEP 0: Read Upstream Artifacts

Read all inputs from upstream stages:

```
artifacts_in:
  plan:       docs/plans/<feature>-plan.md          (from Stage 2)
  unit_tests: tests/unit/                           (from Stage 6)
  api_tests:  tests/api/                            (from Stage 6)
  erd:        docs/schema/erd.md                    (from Stage 5, if exists)
  migrations: migrations/                           (from Stage 5, if exists)
  factories:  tests/factories/                      (from Stage 5, if exists)
```

Validate all required artifacts exist on disk. If any are missing, HALT and report which artifacts are absent.

### STEP 1: Red Phase Verification

Before writing any production code, verify all tests are indeed failing:

```bash
# Run unit tests — expect ALL to fail or be skipped
pytest tests/unit/ --tb=no -q 2>&1 || true
# Run API tests — expect ALL to fail or be skipped
pytest tests/api/ --tb=no -q 2>&1 || true
```

**Gate:** If any tests are already passing, investigate:
- If tests pass because stub/placeholder code exists from scaffolding, note and proceed
- If tests pass because production code already exists, HALT — Stage 7 may have already run

### STEP 2: Skill Router — Choose Execution Strategy

Read the implementation plan at `docs/plans/<feature>-plan.md` and choose the right skill:

```
┌─────────────────────────────────────┐
│ How many tasks in the plan?         │
└────────┬────────────────────────────┘
         │
    ┌────▼────┐
    │ 1 task, │──── Use /implement directly
    │ 1 file  │
    └─────────┘
    ┌─────────────────┐
    │ 2+ tasks with   │──── Use /executing-plans <plan-file>
    │ dependencies    │
    └─────────────────┘
    ┌─────────────────┐
    │ 3+ independent  │──── Use /subagent-driven-dev
    │ tasks, separate │     (delegates to /executing-plans per wave)
    │ files           │
    └─────────────────┘
    ┌─────────────────┐
    │ No plan exists  │──── Use /writing-plans first,
    │                 │     then /executing-plans
    └─────────────────┘
```

**Decision criteria:**
- Count tasks in the plan
- Check dependency graph — are tasks independent or chained?
- Check file overlap — do tasks modify the same files?
- If unsure, default to `/executing-plans` (sequential is always safe)

### STEP 3: Execute Implementation

Invoke the selected skill with the plan. The skill handles:
- Task-by-task implementation
- Running verification commands per task
- Fix loops on failures (max 3 attempts per task via `/fix-loop` with max 3 iterations each — total max 9 attempts per task before escalation)
- **Preferred:** Use `/test-pipeline` instead of invoking `/fix-loop` and `/auto-verify` separately — it handles cleanup, strict gates, screenshot proof capture, and result aggregation automatically
- Git commits per completed task
- Progress tracking

**Monitor the execution.** After each task completes:
1. Check that the task's tests now pass
2. Check that previously passing tests still pass (regression)
3. Update progress: `{completed}/{total} tasks done`

### STEP 4: Post-Implementation Quality Gate

After ALL tests pass, run `/code-quality-gate all changed files`:

The quality gate checks (with blocking thresholds):

| Check | PASS | WARN (non-blocking) | BLOCK (must fix) |
|-------|------|---------------------|-------------------|
| Cyclomatic complexity | 1-10 per function | — | >10 per function |
| Code duplication | ≤3% of changed lines | 3-5% | >5% |
| SOLID violations | 0 critical | 1-2 minor issues | Any critical (God class, layer violation) |
| Clean Architecture layers | 0 forbidden imports | — | Any forbidden import |
| Structured logging | All structured, no PII | Missing correlation ID | PII in logs |
| Error handling | Typed errors, timeouts set | Missing circuit breaker | Empty catch, swallowed exceptions |
| Diff coverage | ≥80% on new code | 60-79% | <60% or new file with 0% |

**If BLOCK:** Fix the issues, re-run tests, re-run quality gate. Use `/fix-loop` if needed.
**If WARN:** Note in the quality report, proceed. Stage 9 (Review) will address.
**If PASS:** Proceed to Step 5.

### STEP 5: Final Verification

Run the complete verification suite:

```bash
# 1. Full test suite
pytest tests/ -v --tb=short

# 2. Linting
ruff check src/ --fix     # Python
# OR: npx eslint src/     # TypeScript
# OR: golangci-lint run    # Go

# 3. Type checking
mypy src/                  # Python
# OR: npx tsc --noEmit    # TypeScript

# 4. Build verification
# (project-specific build command)
```

All four checks MUST pass. If any fail, use `/fix-loop` to resolve.

### STEP 6: Generate API Documentation (if applicable)

If the project has API endpoints, run `/api-docs-generator`:
- Detect the framework automatically by scanning for imports:
  - `from fastapi` → FastAPI
  - `express()` or `@nestjs` → Express/NestJS
  - `http.HandleFunc` or `gin.Default()` → Go
  - `@RestController` → Spring Boot
- Generate OpenAPI spec, validate against tests, produce human-readable docs

Skip this step for projects without API endpoints (CLI tools, libraries, data pipelines).

### STEP 7: Feature Flags (if applicable)

If any implemented features are marked as "gradual rollout" or "incomplete" in the plan:
1. Run `/feature-flag <feature-name>` for each
2. Verify both flag-on and flag-off paths are tested
3. Register flags in `flags.yml`

Skip this step if no features require flags.

### STEP 8: Git Finalization

```bash
# Tag the implementation as complete
git tag "stage-7-complete-$(date +%Y%m%d-%H%M%S)"

# Verify clean working tree
git status
```

### STEP 9: Produce Exit Artifacts

Write the progress report to `docs/plans/<feature>-progress.md`:

```markdown
# Implementation Progress: <feature>

| Task | Status | Tests | Fix Iterations | Commit |
|------|--------|-------|----------------|--------|
| Task 1: ... | PASSED | 5/5 | 0 | abc1234 |
| Task 2: ... | PASSED | 8/8 | 1 | def5678 |
| ... | ... | ... | ... | ... |

## Quality Gate
- Complexity: PASS (max 8)
- Duplication: PASS (1.2%)
- SOLID: PASS
- Coverage diff: PASS (87%)

## Summary
- Total tasks: N
- Total tests passing: M
- Fix iterations used: K
- Duration: ~X min
```

Write structured JSON to `test-results/stage-7.json`:

```json
{
  "stage": "stage_7_impl",
  "timestamp": "<ISO-8601>",
  "result": "PASSED|FAILED",
  "tasks_total": "<N>",
  "tasks_passed": "<N>",
  "tasks_failed": "<N>",
  "tests_passing": "<N>",
  "quality_gate": "PASS|BLOCK",
  "api_docs_generated": true,
  "feature_flags_added": 0,
  "duration_ms": "<elapsed>"
}
```

### STAGE 7 COMPLETION GATE

**PASSED** when ALL of:
- [ ] All Stage 6 failing tests now pass
- [ ] No regressions in existing tests
- [ ] Code quality gate: PASS (no BLOCK items)
- [ ] Linting: clean
- [ ] Type checking: clean
- [ ] Build: succeeds
- [ ] Progress report written to `docs/plans/<feature>-progress.md`
- [ ] Structured JSON written to `test-results/stage-7.json`
- [ ] Git tag applied

**FAILED** when ANY of:
- Tests still failing after all fix attempts exhausted
- Quality gate has unresolved BLOCK items
- Build broken

On failure, report: what passed, what failed, suggested manual interventions, and the git hash to roll back to.

---

## Capability Checklist

| # | Capability | Existing Skill/Agent | Status | SE Standard |
|---|-----------|---------------------|--------|-------------|
| 1 | TDD green phase (make tests pass) | `implement` skill (7-step workflow) | ✅ Covered | **Kent Beck TDD** |
| 2 | Plan-driven execution | `executing-plans` skill (wave execution) | ✅ Covered | — |
| 3 | Parallel subagent execution | `subagent-driven-dev` skill (file ownership) | ✅ Covered | — |
| 4 | Fix loop on failures | `fix-loop` skill (max 5 iterations) | ✅ Covered | — |
| 5 | Regression detection | `auto-verify` skill (changed files → tests) | ✅ Covered | — |
| 6 | Progress tracking | Stage 7 prompt (Step 5) | ✅ Covered | — |
| 7 | Git checkpoints | Stage 7 prompt (Step 2.4: git tag) | ✅ Covered | — |
| 8 | Linting + type checking | Stage 7 prompt (Step 6) | ✅ Covered | — |
| 9 | SOLID principles enforcement | `code-quality-gate` (Step 4: SOLID checklist) | ✅ Covered | **SOLID (Robert C. Martin)** |
| 10 | Clean Architecture layers | `code-quality-gate` (Step 5: layer dependency validation) | ✅ Covered | **Clean Architecture (Uncle Bob)** |
| 11 | Feature flags for incomplete features | `feature-flag` skill (release/experiment/ops/permission toggles) | ✅ Covered | **Feature Toggles (Martin Fowler)** |
| 12 | Code complexity metrics | `code-quality-gate` (Step 2: radon/eslint/gocyclo) | ✅ Covered | **McCabe Complexity** |
| 13 | DRY / duplication detection | `code-quality-gate` (Step 3: jscpd/pylint) | ✅ Covered | **DRY Principle** |
| 14 | Error handling strategy (consistent patterns) | `code-quality-gate` (Step 7: error handling audit — Kotlin sealed types + Result, Python domain exceptions, TypeScript discriminated unions, React error boundaries, timeout strategy, circuit breaker) | ✅ Covered | **Error Handling Best Practices** |
| 15 | Logging strategy (structured logs) | `code-quality-gate` (Step 6: structured logging audit) | ✅ Covered | **Structured Logging** |
| 16 | API documentation generation | `api-docs-generator` skill (multi-framework OpenAPI gen) | ✅ Covered | **OpenAPI Specification** |
| 17 | Refactoring phase (TDD refactor) | `code-quality-gate` (Step 7: refactor checklist + catalog) | ✅ Covered | **Kent Beck TDD (refactor phase)** |

## SE Best Practices Validation

| Standard | Relevant Aspect | Coverage |
|----------|----------------|----------|
| **SOLID Principles** | SRP, OCP, LSP, ISP, DIP in production code | ✅ Per-principle checklist with red flags in `code-quality-gate` Step 4 |
| **Clean Architecture** | Domain/Application/Infrastructure layer separation | ✅ Automated forbidden-import check in `code-quality-gate` Step 5 |
| **Feature Toggles (Fowler)** | Ship incomplete features behind flags | ✅ `feature-flag` skill with 4 toggle types, multi-SDK support, cleanup checklist |
| **McCabe Complexity** | Cyclomatic complexity < 10 per function | ✅ Stack-specific tools with threshold enforcement in `code-quality-gate` Step 2 |
| **DRY Principle** | No duplicate code blocks | ✅ jscpd / pylint detection with 3% threshold in `code-quality-gate` Step 3 |
| **Structured Logging** | JSON logs with correlation IDs, log levels | ✅ PII audit + structured format enforcement in `code-quality-gate` Step 6 |
| **OpenAPI** | Auto-generated API docs from code annotations | ✅ `api-docs-generator` with multi-framework support and spec validation |
| **Error Handling Best Practices** | Typed errors, no swallowed exceptions, timeout strategy, circuit breaker | ✅ `code-quality-gate` Step 7: stack-specific audits (Kotlin Result/sealed, Python domain exceptions, TS discriminated unions, React error boundaries), cross-stack timeout/circuit breaker patterns |
| **Kent Beck TDD** | Red → Green → **Refactor** | ✅ Explicit refactor phase with checklist + catalog in `code-quality-gate` Step 8 |

## Gap Proposals

### Gap 7.1: Code quality enforcement in implementation gate (Priority: P1)

**Problem it solves:** Stage produces working code that passes tests but may accumulate technical debt. No automated checks for complexity, duplication, SOLID compliance, or structured logging.

**What to add (enhance Stage 7 gate check):**
- Cyclomatic complexity check (max 10 per function)
- Duplication detection (jscpd or framework-specific)
- SOLID principles review checklist (can be done by `code-reviewer-agent`)
- Explicit TDD refactor phase after all tests pass
- Structured logging pattern enforcement

**Existing coverage:** Linting and type checking exist. `code-reviewer-agent` exists but not invoked during implementation.

### Gap 7.2: `api-docs-generator` skill (Priority: P2)

**Problem it solves:** Code is written but no API documentation is produced for consumers. Stage 11 (Docs) could consume this, but generation should happen during implementation when annotations are fresh.

**What it needs:**
- Auto-generate OpenAPI/Swagger docs from FastAPI annotations or Express JSDoc
- Validate generated spec against Stage 6 API test expectations

**Existing coverage:** None.

### Gap 7.3: Feature flag integration (Priority: P2)

**Problem it solves:** All code ships directly — no gradual rollout capability. Incomplete features can't be merged behind flags.

**What it needs:**
- Guidance for wrapping incomplete features behind flags (LaunchDarkly, Unleash, or simple env-var flags)
- Flag cleanup checklist for post-launch

**Existing coverage:** None.

## Input/Output Contract

### Inputs (from upstream stages)

| Artifact | Source Stage | Path | Required |
|----------|------------|------|----------|
| Implementation plan | Stage 2 (Plan) | `docs/plans/<feature>-plan.md` | Yes |
| Failing unit tests | Stage 6 (Pre-Tests) | `tests/unit/` | Yes |
| Failing API tests | Stage 6 (Pre-Tests) | `tests/api/` | Yes |
| ERD / schema docs | Stage 5 (Schema) | `docs/schema/erd.md` | If DB exists |
| Migrations | Stage 5 (Schema) | `migrations/` | If DB exists |
| Test factories | Stage 5 (Schema) | `tests/factories/` | If DB exists |

### Outputs (to downstream stages)

| Produces | Consumed By | Format |
|----------|------------|--------|
| Production source code | Stage 8 (Post-Tests), Stage 9 (Review), Stage 10 (Deploy) | Source files |
| `docs/plans/<feature>-progress.md` | Stage 9 (Review — implementation audit trail) | Markdown progress table |
| `test-results/stage-7.json` | Pipeline orchestrator (gate evaluation) | JSON |
| `test-results/code-quality-gate.json` | Stage 9 (Review — quality evidence) | JSON |
| Git commits (one per task) | Stage 9 (Review — commit history), Stage 10 (Deploy) | Git log |
| Passing unit + API tests | Stage 8 (Post-Tests — baseline), Stage 9 (Review — evidence) | Test results |

## Research Targets

- **GitHub**: `<framework> clean architecture example` >1000 stars, `SOLID principles <language>`, `structured logging pattern`
- **Reddit**: r/ExperiencedDevs — "code quality metrics CI", r/programming — "SOLID in practice"
- **Twitter/X**: `clean architecture <framework>`, `code quality AI agent`

## Stack Coverage

| Stack | Implementation Skill | Notes |
|-------|---------------------|-------|
| Python (FastAPI) | ✅ `implement` + `fastapi-*` skills | Service/repository pattern |
| Node/TypeScript | ✅ `implement` skill | Generic workflow |
| Android (Compose) | ✅ `android-arch` + `android-mvi-scaffold` | Clean Architecture + MVI |
| React (Next.js) | ⚠️ `react-nextjs` rule exists but no implementation skill | Rule only, not workflow |
| General | ✅ `subagent-driven-dev` + `executing-plans` | Orchestration layer |

## Autonomy Verdict

**✅ Can run autonomously.** Stage 7 now has a full orchestration prompt (Steps 0-9) with: skill router for choosing between `/implement`, `/executing-plans`, and `/subagent-driven-dev`; red phase verification gate; explicit quality gate thresholds (PASS/WARN/BLOCK); structured JSON output for stage gates; and clear entry/exit contracts with upstream/downstream stages. All 17 capabilities covered. Supporting skills produce `test-results/*.json` for programmatic gate evaluation.

---

## Update Log

| Date | Change |
|------|--------|
| 2026-03-13 | Initial prompt design |
| 2026-03-13 | Rewritten as AUDIT with capability checklist, SE best practices, gap proposals |
| 2026-03-13 | P1 gap resolved: `code-quality-gate` skill created with complexity, duplication, SOLID, logging, refactor, layer validation — 7 ❌ items flipped to ✅ |
| 2026-03-13 | P2 gaps resolved: `feature-flag` and `api-docs-generator` skills — all remaining ❌ items flipped to ✅ |
| 2026-03-14 | Gap #14 resolved: error handling strategy audit added to `code-quality-gate` Step 7 |
| 2026-03-14 | P0 gaps resolved: added orchestration prompt (Steps 0-9), skill router, artifacts_in contract in pipeline-orchestrator, red phase gate, quality gate thresholds. P1 gaps resolved: structured JSON output added to auto-verify/fix-loop/code-quality-gate/implement skills, TDD rule file created, retry semantics clarified, test file mapping added to auto-verify. Status changed from AUDIT to AUTONOMOUS PROMPT. |
