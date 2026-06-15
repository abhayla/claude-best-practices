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

### Defining-behavior validation (remaining 4) — all PASS
- **skill-authoring** — BLOCKING VALIDATE proven: `workflow_quality_gate_validate_patterns.py` exits 1 on an invalid skill, 0 on valid (real exit, not pipe-masked).
- **code-review** — quality-gates (STEP 2) precede PR creation (STEP 3) and PR is gated on green.
- **documentation** — sub-skills (doc-staleness, doc-structure-enforcer, adr, api-docs-generator) present; skip-conditions audited.
- **learning-self-improvement** — closure + capture/propose gate-behavior audited; sub-skills present.

## Status: all 8 workflows validated
Every workflow is validated across structure (Tier-A guard), contract, gates, closures, and its defining behavioral property. Four (development-loop, debugging-loop, test-pipeline, session-continuity) additionally have full end-to-end sandbox runs.

## Optional / on-demand (low marginal value)
- Full multi-agent end-to-end scenario runs for code-review / documentation / learning (their closures, gates, and sub-skills are already validated; a full agent run adds marginal coverage). Best run on-demand in a fresh context.
- **#53** monorepo VERIFY verification — run validated workflows against real monorepos (KKB/AlgoChanakya).

## Also open
- **#53** monorepo VERIFY verification — run validated workflows against real monorepos (KKB/AlgoChanakya).
