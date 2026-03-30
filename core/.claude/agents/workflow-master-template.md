# Workflow Master Template — Shared Orchestration Protocol

This is a reference document, not an agent. Every workflow-master agent reads
this at runtime for shared orchestration protocols. Domain-specific overrides
are defined in each concrete agent.

## Protocol 1: Dual-Mode Operation

Every workflow master operates in one of two modes, detected at startup:

### Standalone Mode
- Trigger: prompt does NOT contain `## Pipeline ID:` and `## Mode: dispatched`
- You ARE the top-level orchestrator
- You CAN dispatch sub-orchestrators via Agent()
- You own state file creation, cleanup, and final reporting
- You execute ALL steps including commit/PR steps
- Gate failures = WARN + ask user for guidance
- After completion, display `handoff_suggestions` from config

### Dispatched Mode
- Trigger: prompt contains `## Pipeline ID:` and `## Mode: dispatched`
- You are a WORKER of the project-manager-agent
- You CAN still dispatch sub-orchestrators via Agent()
- Execute ONLY the steps listed in `## Execute Steps:` (not the full workflow)
- Skip steps marked `skip_when: "mode == 'dispatched'"`
- Gate failures = BLOCK + return failure contract to parent
- Return standard contract: {gate, artifacts, decisions, blockers, summary, duration_seconds}

## Protocol 2: Config-Driven Step Execution

1. Read `config/workflow-contracts.yaml`
2. Find your workflow by matching `master_agent` field to your agent name
3. Load steps, build dependency graph from `depends_on` fields
4. If dispatched with `## Execute Steps:` subset, filter to those steps only
5. Compute execution order (topological sort of dependency graph)
6. Identify parallel opportunities (steps with all dependencies satisfied simultaneously)

For each step (in dependency order):

  a. **Skip check** — Evaluate `skip_when` condition. If true, mark SKIPPED, continue
  b. **Dependency check** — Verify all `depends_on` steps are PASSED or SKIPPED
  c. **Artifact input check** — For each entry in `artifacts_in`, verify the
     referenced artifact exists on disk. If missing:
     - Standalone: WARN + ask user
     - Dispatched: BLOCK + return failure
  d. **Dispatch** —
     - If step has `skill:` field → `Skill("{skill}", args="{context_json}")`
     - If step has `dispatch:` field → `Agent(subagent_type="{agent}", prompt="{context_json}")`
  e. **Output validation** — Verify all `artifacts_out` exist on disk
  f. **Gate evaluation** — If step has `gate:` field, read the artifact JSON
     and evaluate the expression. Examples:
     - `"verification.result == PASSED"` → read the JSON file, check result field
     - `"fix_result.result IN (PASSED, FIXED)"` → check result is one of the listed values
  g. **State update** — Write step status to state file
  h. **Event log** — Append event to `.workflows/{workflow-id}/events.jsonl`

On failure:
  1. Retry up to `max_retries_per_step` (from config defaults)
  2. Each retry decrements `global_retries_remaining` in state
  3. If step retries exhausted → mark FAILED, check if downstream steps can proceed
  4. If global budget exhausted → STOP all execution
     - Standalone: report failures, ask user for guidance
     - Dispatched: return FAILED contract with failure details

## Protocol 3: State Management

State file location: `state_file` field from `config/workflow-contracts.yaml`

### Initialization
At workflow start:
```bash
mkdir -p .workflows/{workflow-id}/
```

Create state file with:
```json
{
  "workflow_id": "{workflow-id}",
  "mode": "standalone|dispatched",
  "pipeline_id": null,
  "run_id": "{ISO-8601-timestamp}_{7-char-git-sha}",
  "started_at": "{ISO-8601}",
  "status": "running",
  "global_retries_used": 0,
  "global_retries_remaining": 15,
  "user_input": "{original request}",
  "steps": {
    "{step_id}": {
      "status": "pending",
      "retries": 0,
      "started_at": null,
      "completed_at": null,
      "artifacts_produced": {},
      "gate_result": null,
      "summary": null,
      "error": null
    }
  }
}
```

### Rules
- MUST update state file after EVERY step status change
- MUST create `.workflows/{workflow-id}/events.jsonl` as append-only event log
- Event format: `{"timestamp": "ISO-8601", "step": "id", "event": "started|completed|failed|skipped|retried", "details": "..."}`
- On resume: read state, find first non-passed/non-skipped step, validate upstream artifacts, continue

### State Ownership
- Your state file: read/write (you own it)
- Parent's state file (`.pipeline/state.json`): read-only
- Sibling workflow state files: read-only (for cross-workflow artifact discovery)

## Protocol 4: Context Passing Between Steps

When dispatching a step, build structured context from ALL upstream results:

```json
{
  "workflow": "{workflow_id}",
  "step": "{step_id}",
  "mode": "standalone|dispatched",
  "upstream_artifacts": {
    "{artifact_name}": "{path_on_disk}"
  },
  "upstream_summaries": {
    "{step_id}": "{one-line summary from state}"
  },
  "user_input": "{original user request}",
  "decisions_so_far": ["{decisions from completed steps}"]
}
```

For `Skill()` calls: pass as the `args` parameter (serialize to structured text):
```
Skill("{skill}", args="
  Workflow: {workflow_id} | Step: {step_id} | Mode: {mode}

  Upstream Artifacts:
    spec: docs/specs/feature-spec.md
    plan: docs/plans/feature-plan.md

  Previous Steps:
    ideate: Spec written with 3 approaches, chose option B (event sourcing)
    plan: 12 tasks planned, estimated 45 min

  User Request: {original request}

  Decisions So Far:
    - Chose event sourcing over CRUD (ADR-001)
    - Using PostgreSQL for persistence
")
```

For `Agent()` calls: embed in the prompt as structured sections:
```
Agent(subagent_type="{agent}", prompt="
  ## Workflow: {workflow_id}
  ## Step: {step_id}
  ## Mode: {mode}

  ## Upstream Artifacts
  spec: docs/specs/feature-spec.md
  plan: docs/plans/feature-plan.md

  ## Previous Steps
  ideate: Spec written with 3 approaches, chose option B
  plan: 12 tasks planned

  ## User Request
  {original request}

  ## Decisions So Far
  - Chose event sourcing over CRUD (ADR-001)
")
```

This ensures no skill or agent starts from scratch — every step receives
the full chain of what happened before it.

## Protocol 5: Cross-Workflow Interface

### Input Contract (Dispatched Mode)
The parent orchestrator sends:
```
## Pipeline ID: {pipeline_id}
## Mode: dispatched
## Workflow: {workflow_id}
## Execute Steps: [{step_ids}]
## Upstream Artifacts:
  {artifact_name}: {path}
## Expected Outputs:
  {artifact_name}: {expected_path}
```

### Output Contract (Return to Parent)
Return JSON matching project-manager-agent's stage return contract:
```json
{
  "gate": "PASSED|FAILED",
  "artifacts": {"name": "path_on_disk"},
  "decisions": ["list of key decisions made"],
  "blockers": ["list of unresolved issues"],
  "summary": "one-paragraph summary of what was accomplished",
  "duration_seconds": 180
}
```

### Cross-Workflow Artifact Discovery (Standalone Mode)
When starting a workflow and a previous workflow's state file exists:
1. Read `.workflows/{previous-workflow}/state.json` (read-only)
2. Extract `artifacts_produced` from completed steps
3. Make these available as optional upstream context
4. Do NOT require them — the user may be starting fresh

## Protocol 6: Progress Reporting

After each step completes, print a progress dashboard:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{WORKFLOW_NAME} — Step {completed}/{total}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✅ step_id_1     summary text (artifact path)
  ✅ step_id_2     summary text (artifact path)
  🔄 step_id_3     RUNNING...
  ⏳ step_id_4     PENDING
  ⏭️  step_id_5     SKIPPED (reason)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Retries: {used}/{budget} | Mode: {standalone|dispatched}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Workflow Completion Report (Standalone Mode Only)
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{WORKFLOW_NAME} — COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Steps: {passed}/{total} passed, {skipped} skipped
Retries used: {used}/{budget}
Duration: {total_time}

Artifacts produced:
  - {path} (from {step_id})
  - {path} (from {step_id})

Decisions made:
  - {decision_1}
  - {decision_2}

SUGGESTED NEXT WORKFLOWS:
  1. /{workflow_id} — {reason}
  2. /{workflow_id} — {reason}

Continue with a workflow? (1/2/skip)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

In dispatched mode, skip the completion report and handoff suggestions — just
return the output contract to the parent orchestrator.
