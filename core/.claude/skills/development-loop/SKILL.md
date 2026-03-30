---
name: development-loop
description: >
  Orchestrate the full development cycle from ideation through verified commit.
  Use when building a feature end-to-end, when the task requires coordinated
  planning and implementation with verification gates.
type: workflow
allowed-tools: "Agent Read Grep Glob"
argument-hint: "<feature description, issue URL, or spec file path>"
version: "1.0.0"
---

# Development Loop — Full Cycle Orchestration

Dispatch the development-loop-master-agent to coordinate the complete
build cycle from ideation through verified commit. Routes to the agent which
handles step sequencing, artifact passing, and verification gates.

**Critical:** All orchestration logic is owned by the agent. Do not implement
steps inline — this skill is a dispatch wrapper only.

**Input:** $ARGUMENTS

---

## STEP 1: Dispatch Workflow Master

Launch the development-loop-master-agent in standalone mode:

```
Agent(subagent_type="development-loop-master-agent", prompt="
  ## Workflow: development-loop
  ## Mode: standalone
  ## User Request: $ARGUMENTS
")
```

The agent will:
1. Read `config/workflow-contracts.yaml` for step definitions
2. Assess task complexity (simple/medium/complex)
3. Execute steps in dependency order with context passing
4. Manage state in `.workflows/development-loop/state.json`
5. Verify artifacts and gates between steps
6. Present completion report with handoff suggestions

### Expected Workflow Steps
The agent executes these steps from the workflow contract config:
- **ideate** → `brainstorm` → produces spec document
- **plan** → `writing-plans` → produces implementation plan
- **execute** → `plan-executor-agent` → produces source code changes
- **verify** → `auto-verify` → produces test verification results
- **commit** → `post-fix-pipeline` → produces verified commit

### If Agent Is Not Available
If `development-loop-master-agent` is not provisioned in the project, run the
constituent skills manually in order: `/brainstorm`, then `/writing-plans`,
then `/executing-plans`, then `/auto-verify`, then `/post-fix-pipeline`.

## STEP 2: Report Results

After the agent completes, relay the workflow summary to the user:

- Steps completed and their artifacts
- Key decisions made during the workflow
- Handoff suggestions for next workflows (`/testing-pipeline-workflow`, `/code-review-workflow`)

---

## MUST DO

- Always dispatch via development-loop-master-agent — do not inline orchestration
- Always relay the full workflow summary and handoff suggestions to the user
- Always report which steps were skipped (for simple/medium tasks) and why

## MUST NOT DO

- MUST NOT implement workflow logic in this skill — delegate to the agent
- MUST NOT modify `.workflows/` state directly — the agent owns state management
- MUST NOT skip the verify step — all code changes require verification evidence before commit
