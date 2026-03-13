# Stage 2: PRD → Tasks & Implementation Plan — AUDIT

> **Purpose:** Audit whether `core/.claude/` has everything needed to decompose a PRD into atomic, dependency-ordered implementation tasks with verification commands, ADRs, and GitHub Issues — fully autonomously.
> **Runs In:** Dedicated Claude Code context window
> **Depends On:** Stage 1 (PRD gate PASSED)
> **Last Updated:** 2026-03-13
> **Status:** AUDIT COMPLETE

---

## Capability Checklist

| # | Capability | Existing Skill/Agent | Status | SE Standard |
|---|-----------|---------------------|--------|-------------|
| 1 | Task decomposition (5-element format) | `writing-plans` (Step 2) | ✅ Covered | — |
| 2 | Dependency graph & critical path | `writing-plans` (Step 3) | ✅ Covered | — |
| 3 | Atomic plan grouping (2-3 tasks) | `writing-plans` (Step 2, atomic plan constraint) | ✅ Covered | — |
| 4 | Architecture Decision Records | `planner-researcher` agent + Stage 2 prompt (Step 2) | ✅ Covered | **Michael Nygard ADR format** |
| 5 | PRD → GitHub Issues with epics | `plan-to-issues` skill | ✅ Covered | — |
| 6 | Verification commands per task | `writing-plans` (element 4) | ✅ Covered | — |
| 7 | File path verification | `writing-plans` (Step 4 checklist) | ✅ Covered | — |
| 8 | PRD requirement traceability (REQ→Task) | Stage 2 prompt (Step 3, "traces to PRD requirement") | ✅ Covered | **Requirements Traceability Matrix** |
| 9 | WBS hierarchy (Epic→Story→Task) | `writing-plans` (Step 2.2: WBS hierarchy) | ✅ Covered | **WBS (PMI PMBOK)** |
| 10 | Story point / effort estimation | `writing-plans` (PERT 3-point estimates) | ✅ Covered | **Agile Estimation** |
| 11 | Risk mitigation tasks | `writing-plans` (Step 2.4: risk mitigation tasks for P×I ≥ 8) | ✅ Covered | **PMI Risk Response Planning** |
| 12 | Buffer / contingency allocation | `writing-plans` (Step 3.2: 20% buffer on critical path) | ✅ Covered | **PERT / Critical Path Method** |
| 13 | Acceptance test linkage (Task→Test ID) | `writing-plans` (Requirement field traces to PRD AC-xxx) | ✅ Covered | **V-Model** |
| 14 | Parallelization efficiency analysis | `writing-plans` (Step 3: "parallelizable tasks") | ⚠️ Partial — identifies parallel tasks but no % utilization metric | **Critical Path Method** |
| 15 | Rollback plan per task | `writing-plans` (Rollback field per task) | ✅ Covered | **Change Management** |

## SE Best Practices Validation

| Standard | Relevant Aspect | Coverage |
|----------|----------------|----------|
| **WBS (PMI PMBOK)** | Hierarchical decomposition: Phase → Deliverable → Work Package → Activity | ❌ Flat task list with no hierarchy above "atomic plan group" |
| **Critical Path Method** | Float/slack calculation, resource leveling | ⚠️ Critical path identified but no float analysis |
| **PERT** | Optimistic/pessimistic/expected time estimates, buffer allocation | ❌ Single point estimates only ("~N min") |
| **V-Model** | Each requirement level maps to a test level | ⚠️ Tasks have verification but no formal test-level mapping |
| **ADR (Nygard)** | Lightweight architecture decisions with status tracking | ✅ Covered in Step 2 |
| **Agile (Scrum)** | Story points, velocity, sprint capacity | ⚠️ Time estimates exist but no story point abstraction |
| **Change Management** | Rollback/revert strategy per change | ❌ No rollback plan per task |

## Gap Proposals

### Gap 2.1: Enhance `writing-plans` with WBS hierarchy (Priority: P1)

**Problem it solves:** Flat task lists lose context at scale. Without WBS hierarchy, the orchestrator cannot reason about which milestone a failed task belongs to, making rollback and re-planning harder.

**What to add:**
- WBS levels above tasks: Epic (milestone) → Feature → Task
- PERT-style estimation: optimistic, expected, pessimistic per task
- Buffer allocation: 20% contingency on critical path
- Rollback notes per task: "revert by: `git revert <commit>`" or "delete file X"

**Existing coverage:** `writing-plans` covers task decomposition, dependency graphs, verification commands. Missing hierarchy, estimation variance, and rollback.

### Gap 2.2: Risk mitigation task generation (Priority: P1)

**Problem it solves:** PRD risk register (Stage 1) identifies risks but no corresponding mitigation tasks are generated in the plan. Autonomous execution has no fallback when risks materialize.

**What to add:**
- For each risk in the PRD risk register, generate a corresponding mitigation task or acceptance criterion
- Example: Risk "third-party API may be rate-limited" → Task "implement circuit breaker with exponential backoff"

**Existing coverage:** None — risks exist as passive documentation, not actionable tasks.

## Input/Output Contract

| Produces | Consumed By | Format |
|----------|------------|--------|
| `docs/plans/<feature>-plan.md` | Stage 6 (Pre-Tests), Stage 7 (Implementation) | Markdown with Task N format, dependency graph, execution waves |
| `docs/plans/<feature>-findings.md` | Stage 7 (Implementation) | Research discoveries log |
| `docs/adr/ADR-*.md` | Stage 9 (Review), Stage 11 (Docs) | Nygard ADR format |
| GitHub Issues with epics | Stage 7 (Implementation), Stage 9 (Review) | `gh issue` URLs |

## Research Targets

- **GitHub**: `AI coding task decomposition`, `LLM implementation plan template`, `WBS markdown template`
- **Reddit**: r/ExperiencedDevs — "task sizing for AI agents", r/agiledev — "estimation without story points"
- **Twitter/X**: `Claude Code task planning`, `AI agent task decomposition best practices`

## Stack Coverage

Universal — task decomposition is stack-agnostic. Stack-specific considerations (e.g., Android Gradle modules, FastAPI route groups) surface naturally during file path verification.

## Autonomy Verdict

**✅ Can run autonomously.** `writing-plans` now covers: WBS hierarchy (Epic→Feature→Task), PERT 3-point estimation with 20% buffer allocation, risk mitigation task generation from PRD risk register, rollback strategy per task, and PRD requirement traceability. All 15 capabilities now ✅ or ⚠️ (minor only).

---

## Update Log

| Date | Change |
|------|--------|
| 2026-03-13 | Initial prompt design |
| 2026-03-13 | Rewritten as AUDIT with capability checklist, SE best practices, gap proposals |
| 2026-03-13 | P1 gaps resolved: `writing-plans` enhanced with WBS, PERT, buffer, rollback, risk mitigation — 5 items flipped to ✅ |
