# Session Handover — 2026-06-15 (Workflow Hardening & Validation)

**Read this first in a new session.** State: `main`, clean tree, **0 open issues**,
20 PRs merged (#49–#69). All work below is on `main` and CI-green.

## What this session accomplished (one line)
Made all 8 hub workflows foolproof + verified for downstream use, added selective
workflow provisioning, and locked it all behind 4 permanent CI guards.

## What was done (by theme)

### A. Workflow dependency-closure hardening (the core)
Root defect (now fixed everywhere): workflow skills' registry `dependencies` were
mis-declared (listed deprecated `*-master-agent`s, omitted the worker agents they
dispatch) AND provisioning was not closure-aware — so workflows shipped downstream
without their workers.
- `recommend.py` now has **closure-aware provisioning** (`_provision_dependency_closure`): a provisioned pattern's transitive registry `dependencies` are co-provisioned regardless of tier (#49).
- Corrected closures for all orchestrators (#54 the 6 siblings, #56 test-pipeline/e2e-visual-run/research-mode).
- **PREFLIGHT** `WORKER_REGISTRY_NOT_LOADED` gates added to all skill-at-T0 workflows (#49, #55, #59); test-pipeline already had `WORKER_REGISTRY_PROBE`.

### B. Behavioral defects found + fixed (via real sandbox QA)
- **Vacuous-green VERIFY gate** — auto-verify returned PASSED with 0 tests; now `NO_TESTS_FOR_CHANGE` under `--strict-gates` (#50/#52).
- **debugging-loop** flag step-numbers off-by-one (#58).
- **Monorepo runner mis-scoping** (#53) — auto-verify now scopes the test runner to the changed sub-package (verified real against AlgoChanakya: root `package.json` test=playwright vs backend pytest) (#63).

### C. The contracts config now provisions (#67)
Every workflow reads `config/workflow-contracts.yaml` at STEP 1, but it was hub-only
and never provisioned. Now distributed (`core/.claude/config/`), registered, in the
closure of the 7 workflows that read it, and the skills' read-path is portable+graceful.

### D. Selective workflow provisioning (#68/#69) — newest feature
`recommend.py --local <dir> --provision --workflows development-loop,debugging-loop`
provisions a SUBSET of workflow orchestrators. Verified: shared resources still
travel for a selected workflow (e.g. `auto-verify` copies for development-loop even
if debugging-loop unselected); unselected orchestrators + their exclusive nice-to-have
resources don't. Semantics = "orchestrator-only" (standalone must-have patterns still
provision on their own merit). A strict mode (`--workflows-strict`) is a documented
NOT-implemented future option.

## Permanent guards added (run in CI — the regression safety net)
- `scripts/tests/test_workflow_closure_consistency.py` — dispatched agents must be declared deps; no deprecated deps; contracts-config distributable+synced+declared.
- `scripts/tests/test_workflow_orchestration_conformance.py` — master_agent null, Agent granted at T0, no deprecated dispatch, state_file SSOT, single-level dispatch.
- `scripts/tests/test_readme_count_drift.py` — README can't hardcode a stale hub count.
- `scripts/tests/test_recommend.py::TestSelectiveWorkflowProvisioning` — the --workflows scenarios.

## Key documents to reference (in priority order)
1. `plans/workflow-validation-campaign-status.md` — the master "what's done / what's open" status.
2. `plans/selective-provisioning-qa-report.md` — the newest feature's scenario evidence.
3. `plans/development-loop-qa-report.md`, `plans/debugging-loop-qa-report.md` — behavioral QA evidence.
4. `plans/development-loop-hardening-{plan,findings,progress}.md` — the original deep-dive.
5. Memory: `project_workflow_hardening_complete.md` (auto-loaded via MEMORY.md).

## What is NOT done (resumable backlog — all genuinely blocked or low-value)
- **Full multi-agent end-to-end scenario runs** for code-review / documentation / learning workflows — their closures/gates/sub-skills are validated; a full agent run is low marginal value. Do on-demand in a fresh context.
- **synthesize-hub behavioral run** — BLOCKED: needs an enrolled downstream repo with `allow_hub_sharing: true` + `synthesized: true` patterns. Both enrolled repos (KKB, AlgoChanakya) have `allow_hub_sharing: false` (opt-in, by design), so the flywheel is correctly dormant.
- **Telemetry bootstrap** — BLOCKED: no real adoption data; owned by the weekly `aggregate-telemetry.yml` CI job.
- **`--workflows-strict`** mode — only if the user wants minimal installs that withhold standalone must-haves.

## How to verify current state in a new session
```bash
git -C <hub> log --oneline -1          # expect the #69 merge / latest docs commit
gh issue list --state open             # expect [] (none)
PYTHONPATH=. python -m pytest scripts/tests/ -q   # expect ~1444 passed
```
