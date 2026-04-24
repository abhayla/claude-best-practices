---
name: testing-pipeline-workflow
description: >
  DEPRECATED 2026-04-24 — use /test-pipeline instead. This skill dispatches
  testing-pipeline-master-agent, whose design assumes nested subagent
  dispatch; Anthropic's platform does not support that (subagents cannot
  spawn subagents). See agent-orchestration.md §2 for the platform-constraint
  note. Will be removed after Phase 3 of the 2026-04-24 remediation completes
  the collapse of the tiered test pipeline into a single T0 orchestrator.
deprecated: true
deprecated_by: test-pipeline
triggers:
  - full testing pipeline
  - tdd through quality gates
  - complete test verification
  - end-to-end testing workflow
  - testing pipeline orchestration
  - run full test chain
type: workflow
allowed-tools: "Agent Read Grep Glob"
argument-hint: "<test target, failure output, or 'full-suite'>"
version: "1.3.0"
---

# Testing Pipeline Workflow — DEPRECATED

> **Deprecated 2026-04-24.** This skill dispatches `testing-pipeline-master-agent`,
> which was designed as a T1 workflow master that further dispatches T2 sub-orchestrators
> via `Agent()`. Anthropic's platform does not forward the `Agent` tool to dispatched
> subagents ([official docs](https://code.claude.com/docs/en/sub-agents):
> *"subagents cannot spawn other subagents"*), so the nested-dispatch design cannot
> execute as intended — the agent silently inlines its downstream work. Use
> `/test-pipeline` as the canonical entry point; Phase 3 of the 2026-04-24 remediation
> will restructure `/test-pipeline` to inject its orchestration logic directly into
> the user's T0 session, where `Agent()` actually works, so parallel Wave 1 lanes
> (functional + API) can be dispatched from T0.
>
> This skill file remains in place for the deprecation window defined in
> `pattern-structure.md` ("Deprecation Lifecycle" — 2 version cycles). Do not
> invoke it in new workflows.

Dispatch the testing-pipeline-master-agent to coordinate the complete
test verification chain from TDD through quality gates to commit. Routes to
the agent which handles gate enforcement, screenshot verdict authority, and
E2E queue-based orchestration.

**Critical:** All test orchestration logic is owned by the agent. Do not
implement steps inline — this skill is a dispatch wrapper only.

**Input:** $ARGUMENTS

---

## STEP 1: Dispatch Workflow Master

Launch the testing-pipeline-master-agent in standalone mode:

```
Agent(subagent_type="testing-pipeline-master-agent", prompt="
  ## Workflow: testing-pipeline
  ## Mode: standalone
  ## User Request: $ARGUMENTS
")
```

The agent will:
1. Read `config/workflow-contracts.yaml` for step definitions
2. Clean ephemeral test artifact directories before execution
3. Execute TDD → fix-loop → auto-verify → E2E → quality gates in order
4. Enforce strict gates with screenshot verdict authority for UI tests
5. Manage state in `.workflows/testing-pipeline/state.json`
6. Aggregate all test results into a unified verdict

### Expected Workflow Steps
The agent executes these steps from the workflow contract config:
- **tdd_red** → `tdd-failing-test-generator` → produces failing tests
- **fix_loop** → `fix-loop` → produces fix result JSON
- **auto_verify** → `auto-verify` → produces verification result JSON
- **e2e** → `e2e-conductor-agent` → produces E2E state (skipped if no UI tests)
- **quality_gate** → `code-quality-gate` → produces quality report JSON
- **post_fix** → `post-fix-pipeline` → produces verified commit

### If Agent Is Not Available
If `testing-pipeline-master-agent` is not provisioned in the project, run
the constituent skills manually: `/tdd`, then `/fix-loop`, then `/auto-verify`,
then `/code-quality-gate`, then `/post-fix-pipeline`.

## STEP 2: Report Results

After the agent completes, relay the testing summary to the user:

- Unified test verdict (PASSED/FAILED)
- Per-step results with timing
- UI test screenshot summary (if applicable)
- Flaky test report
- Handoff suggestions (`/code-review-workflow`)

---

## MUST DO

- Always dispatch via testing-pipeline-master-agent — do not inline orchestration — Why: the agent owns state, gates, and retry logic; inlining breaks observability
- Always relay the unified verdict and any screenshot override details — Why: overrides indicate tests that passed by exit code but failed visually, which blocks commit
- Always report flaky tests detected during the run — Why: flaky tests erode CI confidence and must be quarantined per testing.md rules
- If $ARGUMENTS is empty, default to "full-suite" — Why: the most common invocation is a full pipeline run

## MUST NOT DO

- MUST NOT implement test orchestration logic in this skill — delegate to the agent — Why: duplicating orchestration creates state divergence between skill and agent
- MUST NOT modify test artifact directories directly — the agent handles cleanup and writes — Why: concurrent writes corrupt test-results/ JSON files
- MUST NOT proceed past a FAILED gate — the agent enforces fail-closed semantics — Why: shipping past a failed gate defeats the purpose of the pipeline
- MUST NOT skip the E2E step even if no UI tests exist — let the agent detect and skip — Why: the agent's skip logic handles edge cases like unconfigured visual-tests.yml
