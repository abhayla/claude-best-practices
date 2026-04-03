---
name: pipeline-orchestrator
description: >
  Orchestrate multi-stage pipelines for PRD-to-Production delivery using a
  DAG-based execution model. Use when coordinating 2+ sequential/parallel
  stages that produce artifacts consumed by downstream stages. NOT for
  feature development cycles (use /development-loop) or test verification
  chains (use /test-pipeline).
triggers:
  - pipeline
  - orchestrate stages
  - PRD to production
  - multi-stage
  - coordinate stages
  - run pipeline
allowed-tools: "Agent Read Glob"
argument-hint: "<feature description, PRD file path, or GitHub Issue URL>"
version: "2.1.0"
type: workflow
---

# Pipeline Orchestrator — Dispatch Wrapper

**Critical:** All orchestration logic is owned by `project-manager-agent`. Do not implement pipeline steps inline — this skill is a dispatch wrapper only. Requires `config/pipeline-stages.yaml` to exist.

**Input:** $ARGUMENTS

---

## STEP 1: Dispatch Pipeline Orchestrator Agent

Launch the pipeline-orchestrator agent with the user's input. The agent handles DAG loading from `config/pipeline-stages.yaml`, wave computation, stage agent dispatch, gate validation, state management, retry logic, and pipeline completion.

```
Agent(subagent_type="project-manager-agent", prompt="$ARGUMENTS")
```

The agent will:
1. Parse input (free text / PRD file / GitHub Issue URL)
2. Detect project stacks and load the pipeline DAG
3. Compute execution waves and evaluate skip conditions
4. Dispatch stage agents in parallel waves with artifact contracts
5. Validate gates and manage retries (max 3/stage, 15 global)
6. Persist state to `.pipeline/state.json` after every mutation
7. Generate pipeline summary on completion

### Agent Dispatch Details

The orchestrator manages the full lifecycle of a pipeline run:

- **DAG Loading**: Reads `config/pipeline-stages.yaml` to build a directed acyclic graph of stages
- **Wave Computation**: Groups stages with no unmet dependencies into parallel execution waves
- **Agent Dispatch**: Launches each stage via `Agent()` with a structured prompt containing objective, input artifact paths, expected output paths, and verification commands
- **Gate Validation**: After each worker completes, validates its gate result and output artifacts before advancing
- **Retry Management**: Retries failed stages up to 3 times per stage, with a global budget of 15 retries across the entire pipeline run
- **State Persistence**: Writes pipeline state to `.pipeline/state.json` after every mutation so runs can be resumed if interrupted

## STEP 2: Report Results

After the agent completes, relay the pipeline summary to the user:

- Overall status (completed / failed / paused)
- Per-stage results with timing
- Deployment URL (if Stage 10 completed)
- Decisions requiring user review
- Any stages that need manual intervention

---

## MUST DO

- Always validate `$ARGUMENTS` is non-empty before dispatch — Why: empty prompt causes agent to produce undefined output
- Always verify `config/pipeline-stages.yaml` exists before dispatch — Why: the agent depends on this config; missing file causes immediate failure
- Always dispatch via the `project-manager-agent` agent — Why: orchestration logic is complex and maintained in the agent, not this wrapper
- Always relay the full pipeline summary including per-stage status to the user — Why: users need visibility into which stages passed/failed and why
- Always check for existing `.pipeline/state.json` and warn about in-progress runs — Why: concurrent runs corrupt shared state
- Always relay agent failures with actionable context (which stage, what error) — Why: "pipeline failed" without details forces users to dig through logs

## MUST NOT DO

- MUST NOT implement pipeline logic in this skill — delegate to the agent. Use /development-loop for feature cycles or /test-pipeline for test chains instead
- MUST NOT modify `.pipeline/state.json` directly — the agent owns state management
- MUST NOT dispatch with empty arguments — prompt user for input instead
- MUST NOT dispatch if `config/pipeline-stages.yaml` is missing — report prerequisite failure clearly
- MUST NOT run concurrent pipelines against the same `.pipeline/state.json` — warn and abort if state file shows an active run
