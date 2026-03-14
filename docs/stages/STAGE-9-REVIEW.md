# Stage 9: Code Review & Quality Gates — AUDIT

> **Purpose:** Audit whether `core/.claude/` has everything needed to run comprehensive multi-layered code review, fix findings, and create a production-ready PR — fully autonomously.
> **Runs In:** Dedicated Claude Code context window
> **Depends On:** Stage 8 (Post-Impl Tests — all tests passing)
> **Last Updated:** 2026-03-14
> **Status:** AUDIT COMPLETE

---

## Diagrams

### Diagram A — Internal Workflow Flow (review-gate Orchestrator)

```
                    ┌─────────────────────────┐
                    │  /review-gate            │
                    │  Validate preconditions  │
                    │  (branch, commits, tests)│
                    └────────────┬────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │      BATCH A (parallel)  │
                    │                          │
                    │  ▓ code-quality-gate     │
                    │    (skip Step 5 layer)   │
                    │  ▓ architecture-fitness  │
                    │    (authoritative layers)│
                    └────────────┬────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │      BATCH B (parallel)  │
                    │                          │
                    │  ▓ security-audit        │
                    │    (OWASP, STRIDE)       │
                    │  ▓ change-risk-scoring   │
                    │    (0-100 composite)     │
                    └────────────┬────────────┘
                                 │
                                 ▼
               ┌──────────────────────────────────┐
               │  adversarial-review --mode code   │
               │  (uses findings from A+B)         │
               │  Up to 3 rounds of debate         │
               └────────────────┬─────────────────┘
                                 │
                                 ▼
               ┌──────────────────────────────────┐
               │  pr-standards                     │
               │  (diff-aware standards check)     │
               └────────────────┬─────────────────┘
                                 │
                        Any BLOCK?
                       ┌────┴────┐
                      YES       NO
                       │         │
                       ▼         │
               ┌──────────────┐  │
               │  fix-loop +  │  │
               │  auto-verify │  │
               │  (if --fix)  │  │
               └──────┬───────┘  │
                      │          │
                      ▼          ▼
               ┌──────────────────────────────────┐
               │  Consolidated Report              │
               │  test-results/review-gate.json    │
               │  + markdown summary               │
               └────────────────┬─────────────────┘
                                 │
                       ┌─────────┴─────────┐
                       │                   │
                 ✅ APPROVED          ❌ REJECTED
                 (or WITH CAVEATS)         │
                       │                   │
                       ▼                   ▼
              ┌──────────────┐   ┌──────────────────┐
              │ Create PR    │   │ Return to ST7/ST8 │
              │ (if --pr)    │   │ with findings for  │
              │ + report in  │   │ remediation        │
              │ PR body      │   │                    │
              └──────────────┘   └──────────────────┘
```

### Diagram B — I/O Artifact Contract

```
 ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
 ░  UPSTREAM INPUTS                                                      ░
 ░                                                                       ░
 ░  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐                 ░
 ░  │  ST 7: IMPL  │  │ ST 6: TESTS  │  │  ST 1: PRD   │                 ░
 ░  │              │  │ ST 8: POST   │  │              │                 ░
 ░  │  source      │  │              │  │  prd.md      │                 ░
 ░  │  code        │  │  test suite  │  │  requirements│                 ░
 ░  │              │  │  test results│  │  .json       │                 ░
 ░  │              │  │  coverage    │  │              │                 ░
 ░  │              │  │  perf.json   │  │              │                 ░
 ░  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘                 ░
 ░         │                 │                 │                          ░
 ░░░░░░░░░░┼░░░░░░░░░░░░░░░░┼░░░░░░░░░░░░░░░░┼░░░░░░░░░░░░░░░░░░░░░░░░░
            │                 │                 │
            ▼                 ▼                 ▼
 ┌────────────────────────────────────────────────────────────────┐
 │                                                                │
 │                STAGE 9: CODE REVIEW & QUALITY GATES            │
 │                                                                │
 │  █ review-gate (orchestrator)                                  │
 │    ├─ code-quality-gate  ├─ architecture-fitness               │
 │    ├─ security-audit     ├─ adversarial-review                 │
 │    ├─ change-risk-scoring├─ pr-standards                       │
 │    ├─ fix-loop + auto-verify (conditional)                     │
 │    └─ request-code-review + merge-strategy                     │
 │                                                                │
 └──────┬──────────┬──────────┬──────────┬────────────────────────┘
        │          │          │          │
        ▼          ▼          ▼          ▼
 ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
 ░  DOWNSTREAM OUTPUTS                                                   ░
 ░                                                                       ░
 ░  review-gate.json PR URL         tech debt        updated             ░
 ░  (consolidated    (GitHub)       issues           ADR statuses        ░
 ░   report)                        (gh issue)       (docs/adr/)         ░
 ░     │                │               │                │               ░
 ░     ▼                ▼               ▼                ▼               ░
 ░  ┌──────────┐  ┌──────────┐  ┌──────────────┐  ┌──────────┐         ░
 ░  │ ST 10    │  │ ST 10    │  │ Future       │  │ ST 11    │         ░
 ░  │ DEPLOY   │  │ DEPLOY   │  │ Sprints      │  │ DOCS     │         ░
 ░  │(go/no-go)│  │(what to  │  │              │  │          │         ░
 ░  │          │  │ deploy)  │  │              │  │          │         ░
 ░  └──────────┘  └──────────┘  └──────────────┘  └──────────┘         ░
 ░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░
```

## Capability Checklist

| # | Capability | Existing Skill/Agent | Status | SE Standard |
|---|-----------|---------------------|--------|-------------|
| 1 | Adversarial code review (multi-reviewer) | `adversarial-review` skill | ✅ Covered | — |
| 2 | Security review | `security-auditor` agent + `security-audit` skill | ✅ Covered | **OWASP Top 10** |
| 3 | Automated quality checks (lint, type, build) | `code-reviewer` agent | ✅ Covered | — |
| 4 | PR standards enforcement | `pr-standards` skill | ✅ Covered | — |
| 5 | PR creation with comprehensive description | `request-code-review` + `branching` skills | ✅ Covered | — |
| 6 | Fix loop for review findings | `fix-loop` skill | ✅ Covered | — |
| 7 | Regression check after fixes | `auto-verify` skill | ✅ Covered | — |
| 8 | Tech debt tracking (GitHub Issues) | `plan-to-issues` skill | ✅ Covered | — |
| 9 | Architecture conformance check | `architecture-fitness` skill (dependency direction, circular deps, coupling, ADR review) | ✅ Covered | **Architecture Fitness Functions (Ford/Parsons)** |
| 10 | License compliance check | `supply-chain-audit` covers licenses | ✅ Covered | — |
| 11 | ADR lifecycle review | `architecture-fitness` (Step 6: ADR inventory, code conformance validation, context drift detection, missing ADR detection, status lifecycle management, conformance report) | ✅ Covered | **ADR (Nygard)** |
| 12 | Change risk scoring | `change-risk-scoring` skill (composite score, hotspot analysis) | ✅ Covered | **Change Risk Analysis** |
| 13 | Merge strategy decision | `merge-strategy` skill (squash/merge/rebase by branch type) | ✅ Covered | **Git Workflow** |
| 14 | Approval workflow (multi-approver) | Out of scope — multi-stakeholder sign-off is a human-org concern enforced by GitHub branch protection / CODEOWNERS, not an AI skill | 🚫 Out of Scope | **Code Review Best Practices** |
| 15 | Post-merge verification plan | `merge-strategy` skill Step 5 (smoke tests, deploy verification, rollback) | ✅ Covered | **Continuous Integration** |
| 16 | Orchestrated review pipeline | `review-gate` skill (sequences all sub-skills, aggregates results, produces consolidated report for Stage 10) | ✅ Covered | **Quality Gate Orchestration** |
| 17 | Consolidated review report artifact | `review-gate` Step 8 (aggregates all sub-skill results into `test-results/review-gate.json` + markdown report) | ✅ Covered | **Artifact Contracts** |
| 18 | Post-review fix verification | `receive-code-review` Step 2.1 (invokes `/auto-verify` + `/fix-loop` after addressing must-fix comments) | ✅ Covered | **Continuous Verification** |

## SE Best Practices Validation

| Standard | Relevant Aspect | Coverage |
|----------|----------------|----------|
| **Architecture Fitness Functions** | Automated checks that architecture constraints are maintained | ✅ Dependency direction, circular deps, coupling/cohesion metrics, module boundaries in `architecture-fitness` |
| **ADR Lifecycle** | ADR status updated (Proposed → Accepted → Deprecated) during review | ✅ `architecture-fitness` Step 6: code conformance validation, context drift detection, missing ADR detection for new dependencies/patterns, status lifecycle transitions (Proposed → Accepted → Deprecated → Superseded) |
| **Change Risk Analysis** | Quantified risk score based on files changed, complexity, test coverage delta | ✅ Composite risk score with hotspot analysis in `change-risk-scoring` |
| **Git Workflow** | Merge strategy (squash for feature branches, merge for release) | ✅ Branch-type-aware squash/merge/rebase guidance in `merge-strategy` |
| **Code Review Best Practices (Google)** | Reviewer rotation, review response time SLA, small PRs | 🚫 Multi-approver sign-off is out of scope for AI — enforced by GitHub branch protection / CODEOWNERS at the org level |
| **Continuous Integration** | Post-merge smoke test, deploy verification | ✅ `merge-strategy` Step 5 covers post-merge smoke tests, deploy pipeline verification, and rollback on failure |
| **Quality Gate Orchestration** | Single pipeline sequencing all review checks with pass/fail gates | ✅ `review-gate` skill chains 6 sub-skills with conditional fix-loop and produces consolidated report |
| **Artifact Contracts** | Machine-readable review output consumed by downstream stages | ✅ `review-gate` writes `test-results/review-gate.json` consumed by Stage 10 go/no-go |
| **Continuous Verification** | Automated re-verification after addressing review feedback | ✅ `receive-code-review` invokes `/auto-verify` + `/fix-loop` after must-fix changes |

## Gap Proposals

### Gap 9.1: Architecture fitness function in review gate (Priority: P1)

**Problem it solves:** No automated checks that architectural constraints are maintained. Domain layer could import from infrastructure, circular dependencies could be introduced, coupling could grow unchecked.

**What to add:**
- Dependency direction checks (no domain → infrastructure imports)
- Circular dependency detection
- Coupling metrics (afferent/efferent coupling)
- Can be implemented as custom Semgrep rules or import analysis

**Existing coverage:** `code-reviewer` agent checks conventions. `adversarial-review` has maintainability reviewer. Neither enforces architectural constraints formally.

### Gap 9.2: Change risk scoring (Priority: P2)

**Problem it solves:** No quantified risk score for the overall change. Reviewer findings are categorized qualitatively but there's no aggregate risk metric to guide deploy decisions.

**What to add:**
- Quantified risk score: files changed × complexity delta × inverse test coverage
- High-risk changes flagged for extra scrutiny or human review

**Existing coverage:** CRITICAL/HIGH/MEDIUM/LOW categories per finding, but no aggregate.

### Gap 9.3: Merge strategy and post-merge plan (Priority: P2)

**Problem it solves:** PR created and pushed but no guidance on merge method or post-merge verification.

**What to add:**
- Merge strategy guidance: squash for feature branches, merge for release branches
- Post-merge smoke test: run critical E2E tests on main after merge

**Existing coverage:** `branching` skill handles branch lifecycle but not merge strategy selection.

### Gap 9.4: No orchestrator to sequence review sub-skills (Priority: P0) — RESOLVED

**Problem it solves:** Stage 9 lists 10+ skills and 3 agents that must execute in a specific order, but no single skill chains them together. A human must decide which to invoke, in what order, and how to pass outputs between them. This is the critical gap preventing full autonomy.

**Resolution:** Created `review-gate` skill — orchestrates all 6 review sub-skills (code-quality-gate → architecture-fitness → security-audit → adversarial-review → change-risk-scoring → pr-standards), with conditional fix-loop, consolidated report generation, and optional PR creation.

### Gap 9.5: No consolidated review report artifact (Priority: P1) — RESOLVED

**Problem it solves:** Each sub-skill produces its own report, but there is no unified artifact that Stage 10 (Deploy) can consume as a go/no-go signal. The I/O contract says Stage 9 produces a "Review report" but no skill generated it.

**Resolution:** `review-gate` Step 8 aggregates all sub-skill results into `test-results/review-gate.json` (machine-readable) and a markdown summary. Verdict logic: APPROVED / APPROVED WITH CAVEATS / REJECTED.

### Gap 9.6: code-quality-gate and architecture-fitness overlap on layer validation (Priority: P2) — RESOLVED

**Problem it solves:** Both skills check Clean Architecture layer violations, producing duplicate findings when both run in the same pipeline.

**Resolution:** Added orchestrator note to `code-quality-gate` Step 5: skip layer validation when invoked via `/review-gate` since `architecture-fitness` runs a deeper version (adding coupling metrics, circular deps, ADR review). `architecture-fitness` is the authoritative layer check.

### Gap 9.7: receive-code-review lacks auto-verify integration (Priority: P2) — RESOLVED

**Problem it solves:** When `receive-code-review` addresses must-fix comments, it says "run related tests" but doesn't invoke existing verification skills (`auto-verify`, `fix-loop`), leaving a manual gap.

**Resolution:** Updated `receive-code-review` Step 2.1 to explicitly invoke `/auto-verify --files <fixed_files>` after applying fixes, with fallback to `/fix-loop` if verification fails.

## Input/Output Contract

| Produces | Consumed By | Format |
|----------|------------|--------|
| Consolidated review report | Stage 10 (Deploy — go/no-go), Stage 11 (Docs) | `test-results/review-gate.json` + markdown summary |
| PR URL | Stage 10 (Deploy — what to deploy) | GitHub PR URL |
| Tech debt GitHub Issues | Future sprints | `gh issue` URLs |
| Updated ADR statuses | Stage 11 (Docs) | Modified `docs/adr/ADR-*.md` |

## Research Targets

- **GitHub**: `code review checklist`, `architecture fitness functions`, `PR template best practices`
- **Reddit**: r/ExperiencedDevs — "code review what to look for", r/codereview — "automated review tools"
- **Twitter/X**: `code review best practices`, `architecture fitness functions`

## Stack Coverage

Universal — code review is stack-agnostic. The `adversarial-review` skill and `code-reviewer` agent work across all languages. Stack-specific review concerns (e.g., Android ProGuard rules, FastAPI dependency injection) are handled by the respective stack rules.

## Autonomy Verdict

**✅ Can run fully autonomously.** The `review-gate` orchestrator skill sequences all sub-skills into a single autonomous pipeline: `code-quality-gate` → `architecture-fitness` → `security-audit` → `adversarial-review` → `change-risk-scoring` → `pr-standards`, with conditional `fix-loop` + `auto-verify` for blocking findings, consolidated report generation (`test-results/review-gate.json`), and optional PR creation via `request-code-review`. All 18 capabilities ✅ (except #14 which is intentionally 🚫 Out of Scope). The `receive-code-review` skill now invokes `/auto-verify` + `/fix-loop` for post-review feedback, closing the last manual gap.

---

## Update Log

| Date | Change |
|------|--------|
| 2026-03-13 | Initial prompt design |
| 2026-03-13 | Rewritten as AUDIT with capability checklist, SE best practices, gap proposals |
| 2026-03-13 | P1 gap resolved: `architecture-fitness` skill created with dependency direction, circular deps, coupling metrics, ADR review — architecture conformance ❌ flipped to ✅ |
| 2026-03-13 | P2 gaps resolved: `change-risk-scoring` skill (composite score, hotspot analysis) and `merge-strategy` skill (squash/merge/rebase by branch type) — SE practices ❌ flipped to ✅ |
| 2026-03-13 | Row 15 flipped ⚠️→✅ (post-merge covered by `merge-strategy` Step 5). Row 14 marked 🚫 Out of Scope (multi-approver is a human-org concern, not an AI skill) |
| 2026-03-14 | P0 gap resolved: `review-gate` orchestrator skill created — sequences 6 sub-skills, produces consolidated `test-results/review-gate.json`, conditional fix-loop, optional PR creation. Rows 16-18 added. |
| 2026-03-14 | P2 gap resolved: `code-quality-gate` Step 5 now skipped when invoked via `/review-gate` (dedup with `architecture-fitness`) |
| 2026-03-14 | P2 gap resolved: `receive-code-review` Step 2.1 now invokes `/auto-verify` + `/fix-loop` after must-fix changes |
| 2026-03-14 | Gap #11 resolved: `architecture-fitness` Step 6 enhanced with full ADR lifecycle — code conformance validation, context drift detection, missing ADR detection for new deps/patterns, status lifecycle transitions (Proposed→Accepted→Deprecated→Superseded), conformance report — ⚠️ flipped to ✅ |
