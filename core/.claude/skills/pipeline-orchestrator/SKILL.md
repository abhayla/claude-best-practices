---
name: pipeline-orchestrator
description: >
  DAG-based multi-stage pipeline orchestrator for PRD-to-Production delivery.
  Thin wrapper that dispatches the pipeline-orchestrator agent. Use when
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
version: "2.0.0"
type: workflow
---

# Pipeline Orchestrator — Dispatch Wrapper

Dispatch the `pipeline-orchestrator-agent` agent to coordinate a multi-stage pipeline from PRD to Production.

**Input:** $ARGUMENTS

---

## STEP 1: Dispatch Pipeline Orchestrator Agent

Launch the pipeline-orchestrator agent with the user's input. The agent handles DAG loading from `config/pipeline-stages.yaml`, wave computation, stage agent dispatch, gate validation, state management, retry logic, and pipeline completion.

```
Agent(subagent_type="pipeline-orchestrator-agent", prompt="$ARGUMENTS")
```

The agent will:
1. Parse input (free text / PRD file / GitHub Issue URL)
2. Detect project stacks and load the pipeline DAG
3. Compute execution waves and evaluate skip conditions
4. Dispatch stage agents in parallel waves with artifact contracts
5. Validate gates and manage retries (max 3/stage, 15 global)
6. Persist state to `.pipeline/state.json` after every mutation
7. Generate pipeline summary on completion

## STEP 2: Report Results

After the agent completes, relay the pipeline summary to the user:

- Overall status (completed / failed / paused)
- Per-stage results with timing
- Deployment URL (if Stage 10 completed)
- Decisions requiring user review
- Any stages that need manual intervention

---

## MUST DO

- Always dispatch via the `pipeline-orchestrator-agent` agent — do not inline orchestration logic
- Always relay the full pipeline summary to the user after completion

## MUST NOT DO

- MUST NOT implement pipeline logic in this skill — delegate to the agent
- MUST NOT modify `.pipeline/state.json` directly — the agent owns state management
