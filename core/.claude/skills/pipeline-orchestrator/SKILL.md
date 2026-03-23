---
name: pipeline-orchestrator
description: >
  Orchestrate multi-stage pipelines for PRD-to-Production delivery using a
  DAG-based execution model. Use when
  coordinating 2+ sequential/parallel stages that produce artifacts consumed
  by downstream stages.
triggers:
  - pipeline
  - orchestrate stages
  - PRD to production
  - multi-stage
  - coordinate stages
  - run pipeline
allowed-tools: "Agent Read Grep Glob"
argument-hint: "<feature description, PRD file path, or GitHub Issue URL>"
version: "2.0.1"
type: workflow
---

# Pipeline Orchestrator — Dispatch Wrapper

Dispatch the `project-manager-agent` agent to coordinate a multi-stage pipeline from PRD to Production.

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
### Agent Dispatch DetailsThe orchestrator reads `config/pipeline-stages.yaml` to build a directed acyclic graph of stages. Stages with no unmet dependencies are grouped into waves and dispatched in parallel via `Agent()` calls. Each worker agent receives a structured prompt containing its objective, input artifact paths, expected output paths, and verification commands. When a worker completes, the orchestrator validates its gate result and artifacts before advancing to the next wave. If a stage fails, the orchestrator retries up to 3 times per stage while respecting the global budget of 15 retries across the entire pipeline run.

## STEP 2: Report Results

After the agent completes, relay the pipeline summary to the user:

- Overall status (completed / failed / paused)
- Per-stage results with timing
- Deployment URL (if Stage 10 completed)
- Decisions requiring user review
- Any stages that need manual intervention

---

## MUST DO

- Always dispatch via the `project-manager-agent` agent — do not inline orchestration logic
- Always relay the full pipeline summary to the user after completion

## MUST NOT DO

- MUST NOT implement pipeline logic in this skill — delegate to the agent
- MUST NOT modify `.pipeline/state.json` directly — the agent owns state management
