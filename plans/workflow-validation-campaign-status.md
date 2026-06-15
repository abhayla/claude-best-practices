# Workflow Validation Campaign — Status

**Updated:** 2026-06-15

Strategy: **Tier A** (automated, all-workflows, permanent) + **Tier B** (behavioral, prioritized, per-workflow sandbox run).

## Done

### Tier A — automated guards (permanent, in CI)
- `scripts/tests/test_workflow_closure_consistency.py` (#57) — every agent-dispatching, non-deprecated, non-reference skill must declare its dispatched workers in registry deps; no pattern may declare a deprecated dep. 14 tests.

### Cross-workflow contract sweeps (all 9 orchestrators)
- Closure correctness: development-loop (#49), 6 siblings (#54), test-pipeline + e2e-visual-run + research-mode (#56) — all corrected + verified to co-provision.
- PREFLIGHT / closure gate: development-loop (#49), 6 siblings (#55), e2e-visual-run (#59); test-pipeline already had `WORKER_REGISTRY_PROBE`. **All orchestrators now gated.**
- Step-reference consistency: clean across all 9 (debugging-loop drift fixed in #58).
- Contract completeness (REPORT + gate + CRITICAL RULES + closure gate): all 9 pass.

### Gate-behavior audit (all 5 remaining workflows) — clean
code-review (quality-gate-before-PR), documentation (skip-conditions + staleness), session-continuity (save/restore/handover), learning (capture + propose gate), skill-authoring (BLOCKING validate + register) — all gate behaviors present at the contract level; no F-DBG1-class defects.

### Tier B — behavioral (full sandbox runs)
- **development-loop** — full QA, 14/14; found+fixed vacuous-green VERIFY gate (#50/#52). Report: `development-loop-qa-report.md`.
- **debugging-loop** — full QA; diagnose→fix→verify→learn on a seeded bug; found+fixed F-DBG1 flag step-numbers (#58). Report: `debugging-loop-qa-report.md`.
- **test-pipeline** — PASS; closure + WORKER_REGISTRY_PROBE provisioned; union-of-failures gate correctly blocks on any failing lane (exit 1) and passes when all green (exit 0).
- **session-continuity** — PASS; closure + PREFLIGHT provisioned; save→restore round-trip carries all required sections (working files, git state, decisions, task progress).

## Remaining (Tier B full behavioral — resumable backlog)
Structural (Tier-A guard) + contract + gate-behavior layers are validated for these already; only the full multi-agent scenario run remains. Do each in a **fresh context** (context-management rule 7):
1. **code-review-workflow** — quality-gates → PR → feedback loop on a reviewable diff.
2. **documentation-workflow** — ADR/api-docs/structure/staleness on a project with doc gaps.
3. **learning-self-improvement** — capture → detect-patterns → knowledge-test.
4. **skill-authoring-workflow** — author → validate(BLOCKING) → register (note: the BLOCKING validators are the same `workflow_quality_gate_validate_patterns.py`/`dedup_check.py` proven to block this session).

## Also open
- **#53** monorepo VERIFY verification — run validated workflows against real monorepos (KKB/AlgoChanakya).
