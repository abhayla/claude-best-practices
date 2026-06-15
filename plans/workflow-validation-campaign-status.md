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

### Tier B — behavioral (full sandbox runs)
- **development-loop** — full QA, 14/14; found+fixed vacuous-green VERIFY gate (#50/#52). Report: `development-loop-qa-report.md`.
- **debugging-loop** — full QA; diagnose→fix→verify→learn on a seeded bug; found+fixed F-DBG1 flag step-numbers (#58). Report: `debugging-loop-qa-report.md`.

## Remaining (Tier B behavioral — resumable backlog)
Each needs a domain-specific sandbox scenario; do each in a **fresh context** (context-management rule 7) to keep quality high:
1. **test-pipeline** (highest blast radius left) — three-lane run; verify gate aggregation + WORKER_REGISTRY_PROBE + escalation budgets.
2. **code-review-workflow** — quality-gates → PR → feedback loop on a reviewable diff.
3. **documentation-workflow** — ADR/api-docs/structure/staleness on a project with doc gaps.
4. **session-continuity** — save → restore → handover round-trip fidelity.
5. **learning-self-improvement** — capture → detect-patterns → knowledge-test.
6. **skill-authoring-workflow** — author → validate(BLOCKING) → register.

## Also open
- **#53** monorepo VERIFY verification — run validated workflows against real monorepos (KKB/AlgoChanakya).
