# Stage 7: Implementation (TDD Green Phase) — AUDIT

> **Purpose:** Audit whether `core/.claude/` has everything needed to write production code that makes all Stage 6 failing tests pass — fully autonomously.
> **Runs In:** Dedicated Claude Code context window
> **Depends On:** Stage 6 (Pre-Impl Tests — all tests must be collected and failing)
> **Last Updated:** 2026-03-13
> **Status:** AUDIT COMPLETE

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
| 14 | Error handling strategy (consistent patterns) | Mentioned in research but no enforced pattern | ⚠️ Partial | **Error Handling Best Practices** |
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
| **Kent Beck TDD** | Red → Green → **Refactor** | ✅ Explicit refactor phase with checklist + catalog in `code-quality-gate` Step 7 |

## Gap Proposals

### Gap 7.1: Code quality enforcement in implementation gate (Priority: P1)

**Problem it solves:** Stage produces working code that passes tests but may accumulate technical debt. No automated checks for complexity, duplication, SOLID compliance, or structured logging.

**What to add (enhance Stage 7 gate check):**
- Cyclomatic complexity check (max 10 per function)
- Duplication detection (jscpd or framework-specific)
- SOLID principles review checklist (can be done by `code-reviewer` agent)
- Explicit TDD refactor phase after all tests pass
- Structured logging pattern enforcement

**Existing coverage:** Linting and type checking exist. `code-reviewer` agent exists but not invoked during implementation.

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

| Produces | Consumed By | Format |
|----------|------------|--------|
| Production source code | Stage 8 (Post-Tests), Stage 9 (Review), Stage 10 (Deploy) | Source files |
| `docs/plans/<feature>-progress.md` | Stage 9 (Review — implementation audit trail) | Markdown progress table |
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

**✅ Can run autonomously.** Strong skill coverage: `implement`, `executing-plans`, `subagent-driven-dev`, `fix-loop`, `auto-verify`, `tdd`, plus `code-reviewer` and `tester` agents. `code-quality-gate` skill now adds: cyclomatic complexity enforcement, duplication detection, SOLID principles checklist, Clean Architecture layer validation, structured logging audit, and TDD refactor phase. All P2 gaps resolved: `feature-flag` for toggles and `api-docs-generator` for OpenAPI. All 17 capabilities now ✅.

---

## Update Log

| Date | Change |
|------|--------|
| 2026-03-13 | Initial prompt design |
| 2026-03-13 | Rewritten as AUDIT with capability checklist, SE best practices, gap proposals |
| 2026-03-13 | P1 gap resolved: `code-quality-gate` skill created with complexity, duplication, SOLID, logging, refactor, layer validation — 7 ❌ items flipped to ✅ |
| 2026-03-13 | P2 gaps resolved: `feature-flag` and `api-docs-generator` skills — all remaining ❌ items flipped to ✅ |
