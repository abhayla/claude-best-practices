# QA Report: Selective Workflow Provisioning (`--workflows`)

**Date:** 2026-06-15  **Role:** QA / Test Automation Engineer  **Feature PR:** #68

## How each scenario was tested (two layers)

1. **Persistent / reproducible (the authoritative results):**
   `scripts/tests/test_recommend.py::TestSelectiveWorkflowProvisioning` — 3 pytest
   tests, run in CI on every PR. Reproduce: `PYTHONPATH=. python -m pytest
   scripts/tests/test_recommend.py::TestSelectiveWorkflowProvisioning -v`.
2. **End-to-end CLI in a throwaway downstream sandbox:** a temp git project
   provisioned via the real `recommend.py --local <dir> --provision --workflows
   <names>`, then the resulting `.claude/` tree inspected. (Sandboxes are
   ephemeral and deleted after inspection; this report records the captured
   output so the evidence is durable.)

## Scenarios + results

| # | Scenario | Expected | Actual |
|---|----------|----------|--------|
| 1 | Select ONLY `development-loop` | dev-loop orchestrator present | PRESENT ✅ |
| 1 | — unselected orchestrators (debugging-loop, code-review, documentation, …) | absent | absent ✅ |
| 1 | — selected closure (plan-executor-agent, post-fix-pipeline, **workflow-contracts** config) | present | PRESENT ✅ |
| 1 | — **shared** `auto-verify` (also used by the unselected debugging-loop) | present (selected wf needs it) | PRESENT ✅ |
| 1 | — unselected-exclusive nice-to-have (e.g. debugging-loop-only workers) | absent | absent ✅ |
| 2 | Select `development-loop` + `debugging-loop` | both + union closure; shared once | both PRESENT, auto-verify PRESENT ✅ |
| 2 | — third unselected (`code-review-workflow` + `code-reviewer-agent` exclusive) | absent | absent ✅ |
| 3 | No `--workflows` (back-compat) | all workflows | all PRESENT ✅ |

**Latest run (2026-06-15):** 3/3 unit tests PASS; CLI `--workflows development-loop`
→ only `development-loop` among the 8 orchestrators, `auto-verify` +
`plan-executor-agent` + `workflow-contracts.yaml` present, `debugging-loop` absent.

## Design note (delegated decision)
Standalone `must-have` patterns that an unselected workflow also uses (e.g.
`systematic-debugging`, `debugger-agent`) still provision on their own merit —
"orchestrator-only" selection. They are not "workflows"; withholding them would
deprive the project of useful standalone patterns. A strict mode that withholds
them too is a documented future option (`--workflows-strict`), not implemented.

## Reproduce
```bash
# persistent guard
PYTHONPATH=. python -m pytest scripts/tests/test_recommend.py::TestSelectiveWorkflowProvisioning -v
# end-to-end in a sandbox
mkdir /tmp/sbx && cd /tmp/sbx && git init -q && echo '{"name":"x"}' > package.json && git add -A && git commit -qm b
cd <hub> && PYTHONPATH=. python scripts/recommend.py --local /tmp/sbx --provision --workflows development-loop
ls /tmp/sbx/.claude/skills    # development-loop present; debugging-loop absent; auto-verify present
```
