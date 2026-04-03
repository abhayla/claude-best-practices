---
name: development-loop
description: >
  Orchestrate the full development cycle from ideation through verified commit
  by chaining brainstorm → writing-plans → executing-plans → auto-verify →
  post-fix-pipeline via development-loop-master-agent. Use when building a
  feature end-to-end with coordinated planning and verification gates. For
  bug fixes, use /fix-issue or /debugging-loop instead. For just implementation
  without ideation, use /implement.
type: workflow
triggers:
  - full development cycle
  - develop feature from scratch
  - ideate plan build verify
  - development workflow
  - feature end to end
  - new feature end to end
allowed-tools: "Agent Read Grep Glob"
argument-hint: "<feature description, issue URL, or spec file path>"
version: "1.3.0"
---

# Development Loop — Full Cycle Orchestration

Dispatch the development-loop-master-agent to coordinate the complete
build cycle from ideation through verified commit. Routes to the agent which
handles step sequencing, artifact passing, and verification gates.

**Critical:** All orchestration logic is owned by the agent. Do not implement
steps inline — this skill is a dispatch wrapper only.

**Input:** $ARGUMENTS

If `$ARGUMENTS` is empty, ask the user to describe the feature they want to build.
Do NOT dispatch the agent without a feature description.

If the task is trivial (single file, config change, fewer than ~3 files affected),
suggest using `/implement` directly. Proceed with the full cycle only if the user
confirms.

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
1. Read `config/workflow-contracts.yaml` for step definitions (if absent, falls back to hardcoded step order below)
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

### If Agent Fails Mid-Workflow
If the agent returns an error or partial completion, relay the last completed
step and its artifacts to the user. Suggest resuming with the next skill in
the fallback sequence from the failed step onward.

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

- Always dispatch via development-loop-master-agent — do not inline orchestration — Why: orchestration logic is owned by the agent; duplicating it here causes version drift
- Always relay the full workflow summary and handoff suggestions to the user — Why: the user needs to know what was done, what artifacts were produced, and what to do next
- Always report which steps were skipped (for simple/medium tasks) and why — Why: transparency about skipped steps prevents users from assuming work that wasn't done
- Always validate input before dispatching — empty arguments waste an agent context window — Why: the agent cannot meaningfully brainstorm without a feature description

## MUST NOT DO

- MUST NOT implement workflow logic in this skill — delegate to the agent — Why: inline orchestration defeats the agent's state management and resume capabilities
- MUST NOT modify `.workflows/` state directly — the agent owns state management — Why: external state writes corrupt the agent's resumption logic
- MUST NOT skip the verify step — all code changes require verification evidence before commit — Why: unverified code reaching commit undermines the entire pipeline's trust model
- MUST NOT dispatch the agent for trivial tasks without user confirmation — Why: the 5-step pipeline is expensive; trivial tasks should use /implement directly
