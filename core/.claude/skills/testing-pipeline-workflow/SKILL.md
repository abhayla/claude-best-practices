---
name: testing-pipeline-workflow
description: >
  Run the complete test verification chain from TDD through quality gates.
  Use when running the full testing workflow end-to-end rather than
  individual test skills.
type: workflow
allowed-tools: "Agent Read Grep Glob"
argument-hint: "<test target, failure output, or 'full-suite'>"
version: "1.0.0"
---

# Testing Pipeline Workflow — Full Verification Orchestration

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

- Always dispatch via testing-pipeline-master-agent — do not inline orchestration
- Always relay the unified verdict and any screenshot override details
- Always report flaky tests detected during the run

## MUST NOT DO

- MUST NOT implement test orchestration logic in this skill — delegate to the agent
- MUST NOT modify test artifact directories directly — the agent handles cleanup and writes
- MUST NOT proceed past a FAILED gate — the agent enforces fail-closed semantics
