---
name: code-review-workflow
description: >
  Run pre-merge quality gates, create PR, and handle review feedback.
  Use when preparing code for review end-to-end or running the complete
  pre-merge quality pipeline.
type: workflow
allowed-tools: "Agent Read Grep Glob"
argument-hint: "<branch name, 'current', or review scope description>"
version: "1.0.0"
---

# Code Review Workflow — Full Review Orchestration

Dispatch the code-review-master-agent to coordinate the complete
pre-merge quality pipeline from gates through PR to feedback resolution.
Routes to the agent which handles verdict aggregation, deferred item TTL,
and auto-fix for blocking findings.

**Critical:** All review orchestration is owned by the agent. Do not
implement steps inline. Quality gates MUST NOT be bypassed.

**Input:** $ARGUMENTS

---

## STEP 1: Dispatch Workflow Master

Launch the code-review-master-agent in standalone mode:

```
Agent(subagent_type="code-review-master-agent", prompt="
  ## Workflow: code-review
  ## Mode: standalone
  ## User Request: $ARGUMENTS
")
```

The agent will:
1. Read `config/workflow-contracts.yaml` for step definitions
2. Execute review-gate → request-code-review → receive-code-review
3. Aggregate quality gate verdicts (APPROVED / APPROVED WITH CAVEATS / REJECTED)
4. Track deferred items with TTL enforcement (14-day auto-promotion)
5. Offer auto-fix for blocking findings in standalone mode
6. Manage state in `.workflows/code-review/state.json`

### Expected Workflow Steps
The agent executes these steps from the workflow contract config:
- **quality_gates** → `review-gate` → produces review report JSON with verdict
- **create_pr** → `request-code-review` → produces PR URL (standalone only)
- **handle_feedback** → `receive-code-review` → produces feedback resolution status

### If Agent Is Not Available
If `code-review-master-agent` is not provisioned in the project, run the
constituent skills manually: `/review-gate`, then `/request-code-review` with
the review report, then `/receive-code-review` with the PR URL.

## STEP 2: Report Results

After the agent completes, relay the review summary to the user:

- Quality gate verdict and breakdown
- Risk score with contributing factors
- PR URL (if created)
- Review feedback status (resolved/outstanding)
- Deferred items summary
- Handoff suggestions (`/documentation-workflow`)

---

## MUST DO

- Always dispatch via code-review-master-agent — do not inline orchestration
- Always relay the full verdict breakdown, not just pass/fail
- Always report deferred item count and any auto-promotion warnings

## MUST NOT DO

- MUST NOT implement review logic in this skill — delegate to the agent
- MUST NOT bypass quality gates — the agent enforces strict gate checking
- MUST NOT auto-fix blocking findings without user confirmation in standalone mode
