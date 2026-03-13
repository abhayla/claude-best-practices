# Stage 9: Code Review & Quality Gates — AUDIT

> **Purpose:** Audit whether `core/.claude/` has everything needed to run comprehensive multi-layered code review, fix findings, and create a production-ready PR — fully autonomously.
> **Runs In:** Dedicated Claude Code context window
> **Depends On:** Stage 8 (Post-Impl Tests — all tests passing)
> **Last Updated:** 2026-03-13
> **Status:** AUDIT COMPLETE

---

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
| 11 | ADR review (decisions still valid) | None — ADRs created in Stage 2 but not re-validated during review | ⚠️ Partial | **ADR (Nygard)** |
| 12 | Change risk scoring | `change-risk-scoring` skill (composite score, hotspot analysis) | ✅ Covered | **Change Risk Analysis** |
| 13 | Merge strategy decision | `merge-strategy` skill (squash/merge/rebase by branch type) | ✅ Covered | **Git Workflow** |
| 14 | Approval workflow (multi-approver) | None — single AI reviewer, no multi-stakeholder sign-off | ❌ Missing | **Code Review Best Practices** |
| 15 | Post-merge verification plan | None — PR merged but no smoke test plan for after merge | ⚠️ Partial | **Continuous Integration** |

## SE Best Practices Validation

| Standard | Relevant Aspect | Coverage |
|----------|----------------|----------|
| **Architecture Fitness Functions** | Automated checks that architecture constraints are maintained | ✅ Dependency direction, circular deps, coupling/cohesion metrics, module boundaries in `architecture-fitness` |
| **ADR Lifecycle** | ADR status updated (Proposed → Accepted → Deprecated) during review | ⚠️ ADRs created but never re-validated |
| **Change Risk Analysis** | Quantified risk score based on files changed, complexity, test coverage delta | ✅ Composite risk score with hotspot analysis in `change-risk-scoring` |
| **Git Workflow** | Merge strategy (squash for feature branches, merge for release) | ✅ Branch-type-aware squash/merge/rebase guidance in `merge-strategy` |
| **Code Review Best Practices (Google)** | Reviewer rotation, review response time SLA, small PRs | ⚠️ Multi-reviewer exists but all are AI — no human-in-the-loop guidance |
| **Continuous Integration** | Post-merge smoke test, deploy verification | ⚠️ Tests run pre-merge but no post-merge verification step |

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

## Input/Output Contract

| Produces | Consumed By | Format |
|----------|------------|--------|
| Review report (findings + fixes) | Stage 10 (Deploy — go/no-go), Stage 11 (Docs) | Categorized findings in stage doc |
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

**✅ Can run autonomously.** Excellent skill coverage: `adversarial-review`, `security-audit`, `pr-standards`, `request-code-review`, `branching`, `fix-loop`, `auto-verify`, `architecture-fitness`, `change-risk-scoring`, `merge-strategy`. The most mature review pipeline of any stage. All P1 and P2 gaps resolved.

---

## Update Log

| Date | Change |
|------|--------|
| 2026-03-13 | Initial prompt design |
| 2026-03-13 | Rewritten as AUDIT with capability checklist, SE best practices, gap proposals |
| 2026-03-13 | P1 gap resolved: `architecture-fitness` skill created with dependency direction, circular deps, coupling metrics, ADR review — architecture conformance ❌ flipped to ✅ |
| 2026-03-13 | P2 gaps resolved: `change-risk-scoring` skill (composite score, hotspot analysis) and `merge-strategy` skill (squash/merge/rebase by branch type) — SE practices ❌ flipped to ✅ |
