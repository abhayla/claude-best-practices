---
name: pipeline-orchestrator
description: >
  DAG-based multi-stage pipeline orchestrator for PRD-to-Production delivery.
  Manages typed artifact contracts between stages, state persistence, conditional
  branching, idempotent execution, observability, and compensating rollback.
  Use when coordinating 2+ sequential/parallel stages that produce artifacts
  consumed by downstream stages.
triggers:
  - pipeline
  - orchestrate stages
  - PRD to production
  - multi-stage
  - coordinate stages
  - run pipeline
allowed-tools: "Bash Read Write Edit Grep Glob Agent Skill"
argument-hint: "<feature description, PRD file path, or GitHub Issue URL>"
version: "1.0.0"
type: workflow
---

# Pipeline Orchestrator — DAG-Based Multi-Stage Coordination

Coordinate a multi-stage pipeline from PRD to Production, managing artifact contracts, state, branching, and rollback.

**Input:** $ARGUMENTS

---

## STEP 1: Initialize Pipeline

### 1.1 Parse Input

Accept ONE of:
- **Free text description** → Stage 1 generates PRD
- **PRD file path** → Stage 1 parses and validates
- **GitHub Issue URL** → Stage 1 fetches and expands

### 1.2 Detect Project Stacks

Scan the project to determine which stages and stage variants apply:

```bash
# Detect language/framework
ls package.json pyproject.toml build.gradle.kts Cargo.toml go.mod 2>/dev/null
```

### 1.3 Build Pipeline DAG

Define stages with dependencies and conditional skip rules:

```json
{
  "pipeline_id": "<uuid>",
  "started_at": "<ISO-8601>",
  "input_type": "description|prd_file|github_issue",
  "input": "<the input>",
  "project_root": "<absolute path>",
  "stages": [
    {
      "id": "stage_1_prd",
      "name": "Requirements → PRD",
      "depends_on": [],
      "skip_when": "input_type == 'prd_file' AND prd_valid == true",
      "artifacts_out": {
        "prd": { "path": "docs/plans/<feature>-prd.md", "schema": "prd_v1" }
      },
      "timeout_minutes": 30
    },
    {
      "id": "stage_2_plan",
      "name": "PRD → Plan",
      "depends_on": ["stage_1_prd"],
      "artifacts_in": { "prd": "stage_1_prd.artifacts_out.prd" },
      "artifacts_out": {
        "plan": { "path": "docs/plans/<feature>-plan.md", "schema": "plan_v1" },
        "adrs": { "path": "docs/adr/ADR-*.md", "schema": "adr_v1" }
      },
      "timeout_minutes": 30
    },
    {
      "id": "stage_3_scaffold",
      "name": "Scaffolding",
      "depends_on": ["stage_1_prd"],
      "skip_when": "project_already_scaffolded == true",
      "artifacts_out": {
        "skeleton": { "path": "<project_root>", "schema": "scaffold_v1" }
      },
      "timeout_minutes": 20
    },
    {
      "id": "stage_4_demo",
      "name": "HTML Demo",
      "depends_on": ["stage_1_prd", "stage_3_scaffold"],
      "skip_when": "project_type IN ('cli', 'library', 'api_only', 'backend', 'data_pipeline', 'infrastructure')",
      "artifacts_in": {
        "prd": "stage_1_prd.artifacts_out.prd",
        "skeleton": "stage_3_scaffold.artifacts_out.skeleton"
      },
      "artifacts_out": {
        "screens": { "path": "demos/<feature>/index.html", "schema": "html_screens_v1", "note": "index.html + N screen HTML files (auth-*.html, main-*.html, etc.)" },
        "design_system_css": { "path": "demos/<feature>/shared.css", "schema": "css_v1" },
        "design_system_js": { "path": "demos/<feature>/shared.js", "schema": "js_v1" },
        "impl_mapping": { "path": "demos/<feature>/IMPL-MAPPING.md", "schema": "impl_mapping_v1" },
        "screenshots": { "path": "docs/stages/screenshots/stage-4/*.png", "schema": "image_v1" }
      },
      "timeout_minutes": 30
    },
    {
      "id": "stage_5_schema",
      "name": "Schema & Migrations",
      "depends_on": ["stage_2_plan", "stage_3_scaffold"],
      "skip_when": "no_database == true",
      "artifacts_out": {
        "erd": { "path": "docs/schema/erd.md", "schema": "erd_v1" },
        "migrations": { "path": "migrations/", "schema": "migration_v1" },
        "seeds": { "path": "scripts/seed.*", "schema": "seed_v1" }
      },
      "timeout_minutes": 25
    },
    {
      "id": "stage_6_pre_tests",
      "name": "Pre-Impl Tests (TDD Red)",
      "depends_on": ["stage_2_plan", "stage_5_schema"],
      "artifacts_out": {
        "test_matrix": { "path": "docs/stages/STAGE-6-PRE-IMPL-TESTS.md#test-matrix", "schema": "test_matrix_v1" },
        "unit_tests": { "path": "tests/unit/", "schema": "test_files_v1" },
        "api_tests": { "path": "tests/api/", "schema": "test_files_v1" },
        "e2e_stubs": { "path": "tests/e2e/", "schema": "test_files_v1" }
      },
      "timeout_minutes": 30
    },
    {
      "id": "stage_7_impl",
      "name": "Implementation (TDD Green)",
      "depends_on": ["stage_6_pre_tests"],
      "artifacts_in": {
        "plan": "stage_2_plan.artifacts_out.plan",
        "unit_tests": "stage_6_pre_tests.artifacts_out.unit_tests",
        "api_tests": "stage_6_pre_tests.artifacts_out.api_tests",
        "erd": "stage_5_schema.artifacts_out.erd",
        "migrations": "stage_5_schema.artifacts_out.migrations"
      },
      "artifacts_out": {
        "source_code": { "path": "src/", "schema": "source_v1" },
        "progress": { "path": "docs/plans/<feature>-progress.md", "schema": "progress_v1" },
        "quality_report": { "path": "test-results/code-quality-gate.json", "schema": "quality_gate_v1" }
      },
      "timeout_minutes": 60
    },
    {
      "id": "stage_8_post_tests",
      "name": "Post-Impl Tests",
      "depends_on": ["stage_7_impl"],
      "artifacts_out": {
        "e2e_report": { "path": "playwright-report/", "schema": "report_v1" },
        "perf_results": { "path": "results/perf.json", "schema": "perf_v1" },
        "security_report": { "path": "tests/security/threat-model.md", "schema": "threat_model_v1" }
      },
      "timeout_minutes": 45
    },
    {
      "id": "stage_9_review",
      "name": "Code Review",
      "depends_on": ["stage_8_post_tests"],
      "artifacts_out": {
        "review_report": { "path": "docs/stages/STAGE-9-REVIEW.md", "schema": "review_v1" },
        "pr_url": { "type": "string", "schema": "url" }
      },
      "timeout_minutes": 30
    },
    {
      "id": "stage_10_deploy",
      "name": "Deploy & Monitor",
      "depends_on": ["stage_9_review"],
      "artifacts_in": {
        "pr_url": "stage_9_review.artifacts_out.pr_url",
        "source": "stage_3_scaffold.artifacts_out.skeleton",
        "migrations": "stage_5_schema.artifacts_out.migrations",
        "test_results": "stage_8_post_tests.artifacts_out.test_results"
      },
      "artifacts_out": {
        "deploy_url": { "type": "string", "schema": "url" },
        "ci_pipeline": { "path": ".github/workflows/ci.yml", "schema": "ci_v1" },
        "monitoring_dashboards": { "path": "monitoring/dashboards/", "schema": "grafana_json_v1" },
        "runbooks": { "path": "docs/runbooks/", "schema": "runbook_v1" },
        "slo_definitions": { "path": "monitoring/slo-rules.yml", "schema": "prometheus_rules_v1" },
        "dr_runbook": { "path": "docs/DR-RUNBOOK.md", "schema": "dr_runbook_v1" }
      },
      "timeout_minutes": 45
    },
    {
      "id": "stage_11_docs",
      "name": "Docs & Handover",
      "depends_on": ["stage_10_deploy"],
      "artifacts_out": {
        "readme": { "path": "README.md", "schema": "readme_v1" },
        "architecture": { "path": "docs/ARCHITECTURE.md", "schema": "arch_doc_v1" },
        "handover": { "path": "docs/HANDOVER.md", "schema": "handover_v1" },
        "summary": { "path": "docs/stages/PIPELINE-SUMMARY.md", "schema": "summary_v1" }
      },
      "timeout_minutes": 30
    }
  ]
}
```

### 1.4 Evaluate Skip Conditions

For each stage with `skip_when`, evaluate the condition:
- `project_type IN ('cli', 'library', 'api_only', 'backend', 'data_pipeline', 'infrastructure')` → skip Stage 4 (HTML Demo)
- `no_database == true` → skip Stage 5 (Schema)
- `input_type == 'prd_file'` → skip PRD generation, parse instead
- `project_already_scaffolded == true` → skip Stage 3

Mark skipped stages as `"status": "skipped"` in state.

### 1.5 Create State File

Write `.pipeline/state.json`:

```json
{
  "pipeline_id": "<uuid>",
  "started_at": "<ISO-8601>",
  "stages": {
    "stage_1_prd": { "status": "pending", "started_at": null, "completed_at": null, "retries": 0, "gate_result": null },
    "stage_2_plan": { "status": "pending" },
    "...": "..."
  },
  "current_wave": 0,
  "blockers": [],
  "config": {
    "max_retries": 3,
    "timeout_default_minutes": 30
  }
}
```

### 1.6 Create Event Log

Initialize `.pipeline/event-log.jsonl` (append-only):

```jsonl
{"ts": "<ISO-8601>", "event": "pipeline_started", "pipeline_id": "<uuid>", "input_type": "<type>", "stages_total": 11, "stages_skipped": ["stage_4_demo"]}
```

---

## STEP 2: Compute Execution Waves

From the DAG, compute parallel execution waves:

```
Wave 1:  Stage 1 (PRD)
Wave 2:  Stage 2 (Plan) + Stage 3 (Scaffold)         — after Stage 1
Wave 3:  Stage 4 (Demo)                               — after Stages 1 + 3
Wave 4:  Stage 5 (Schema)                             — after Stages 2 + 3
Wave 5:  Stage 6 (Pre-Tests)                          — after Stages 2 + 5
Wave 6:  Stage 7 (Implementation)                     — after Stage 6
Wave 7:  Stage 8 (Post-Tests)                         — after Stage 7
Wave 8:  Stage 9 (Review)                             — after Stage 8
Wave 9:  Stage 10 (Deploy)                            — after Stage 9
Wave 10: Stage 11 (Docs)                              — after Stage 10
```

**Critical path:** Stage 1 → 2 → 5 → 6 → 7 → 8 → 9 → 10 → 11

Adjust waves by removing skipped stages. If Stage 5 is skipped, Stage 6 depends only on Stage 2.

---

## STEP 3: Dispatch Waves

For each wave, dispatch all eligible stages in parallel using the Agent tool.

### 3.1 Pre-Dispatch Contract Validation

Before dispatching a stage, validate that all `artifacts_in` exist:

```
For stage_6_pre_tests:
  ✓ stage_2_plan.artifacts_out.plan exists at docs/plans/<feature>-plan.md
  ✓ stage_5_schema.artifacts_out.erd exists at docs/schema/erd.md
  → All inputs satisfied, dispatch allowed
```

If any artifact is missing, the stage MUST NOT be dispatched. Log a blocker.

### 3.2 Agent Prompt Template

Each stage agent receives:

```
Agent("
## You are: {stage_name}
## Pipeline ID: {pipeline_id}
## Project Root: {project_root}

## Your Instructions
Read docs/stages/STAGE-{N}-{NAME}.md for your full audit/execution instructions.

## Upstream Artifacts (read these)
{list of artifact paths from upstream stages}

## Your Artifacts (produce these)
{list of artifacts_out with expected paths}

## Gate Protocol
When done:
1. Verify all artifacts_out exist on disk
2. Update docs/stages/STAGE-{N}-{NAME}.md Gate Status to PASSED or FAILED
3. Return JSON: {gate, artifacts, decisions, blockers, summary}

## Idempotency
If you detect your artifacts already exist and are valid, verify them and return PASSED without re-creating.
")
```

### 3.3 Agent Return Contract

Every stage agent MUST return structured JSON:

```json
{
  "gate": "PASSED|FAILED",
  "artifacts": {
    "prd": "docs/plans/user-auth-prd.md"
  },
  "decisions": [
    "Chose UUID over auto-increment for primary keys (see ADR-001)"
  ],
  "blockers": [],
  "summary": "Generated PRD with 12 user stories, 24 acceptance criteria, 8 NFRs",
  "duration_seconds": 180,
  "token_usage": { "input": 15000, "output": 8000 }
}
```

### 3.4 Post-Dispatch Processing

After each agent returns:

1. **Parse the return JSON** — extract gate, artifacts, decisions, blockers
2. **Validate artifacts exist** — check each path on disk
3. **Update state.json** — set stage status, timestamps, gate result
4. **Append to event log** — structured event with timing and token usage
5. **Store decisions** — accumulate for pipeline summary
6. **Check for next wave** — if all stages in current wave passed, advance

---

## STEP 4: Gate Protocol

### 4.1 Gate Evaluation

After a stage agent returns:

```
IF gate == "PASSED" AND all artifacts exist on disk:
  → Update state: "status": "passed"
  → Log event: stage_passed
  → Check if next wave is unblocked

IF gate == "FAILED":
  → Update state: "status": "failed"
  → Log event: stage_failed with reason
  → Enter retry protocol (Step 5)

IF gate == "PASSED" BUT artifacts missing:
  → Override to FAILED
  → Log event: artifact_validation_failed
  → Enter retry protocol
```

### 4.2 Artifact Validation

For each artifact in `artifacts_out`:

| Check | How |
|-------|-----|
| File exists | `test -f <path>` or glob match |
| File non-empty | `test -s <path>` |
| Valid format (if schema) | Parse JSON/YAML/markdown structure |

---

## STEP 5: Failure Handling & Retry

### 5.1 Retry Protocol

```
Attempt 1: Re-dispatch with failure context
  "Previous attempt failed: {reason}. Try a different approach."

Attempt 2: Simplify scope
  "Focus only on {critical_subset}. Skip {optional_parts}."

Attempt 3: Escalate to user
  "Stage {N} failed after 3 attempts. Error: {details}.
   Options: (1) Fix manually, (2) Skip stage, (3) Abort pipeline"
```

### 5.2 Compensating Rollback

When a stage fails and has produced partial artifacts:

```bash
# Identify files created by the failed stage
git diff --name-only --diff-filter=A HEAD

# Revert partial artifacts
git checkout HEAD -- <partial_artifact_paths>

# Or if committed:
git revert --no-commit <stage_commit_hash>
```

Update state.json: `"status": "rolled_back"`

### 5.3 Upstream Failure Cascade

If Stage N fails, all stages that depend on it (directly or transitively) are marked `"status": "blocked"`:

```
stage_5_schema FAILED
  → stage_6_pre_tests: BLOCKED (depends on stage_5)
  → stage_7_impl: BLOCKED (depends on stage_6)
  → stage_8_post_tests: BLOCKED (depends on stage_7)
  → ... cascade through all downstream
```

Stages NOT in the dependency chain continue unaffected.

---

## STEP 6: Idempotency

Every stage MUST be safely re-runnable:

1. **Check before creating** — if artifact exists and is valid, skip creation
2. **Use git tags as checkpoints** — `git tag pipeline/<pipeline_id>/stage-<N>-start` before each stage
3. **Clean rollback** — reverting to a tag restores exact pre-stage state
4. **State file is source of truth** — if state says "passed" and artifacts exist, skip the stage

```bash
# Tag before stage execution
git tag "pipeline/${PIPELINE_ID}/stage-${N}-start"

# If stage fails and needs rollback:
git reset --hard "pipeline/${PIPELINE_ID}/stage-${N}-start"
```

---

## STEP 7: Observability

### 7.1 Event Log Format

Every significant event appends to `.pipeline/event-log.jsonl`:

```jsonl
{"ts": "2026-03-13T10:00:00Z", "event": "stage_started", "stage": "stage_1_prd", "wave": 1}
{"ts": "2026-03-13T10:03:00Z", "event": "stage_passed", "stage": "stage_1_prd", "duration_s": 180, "tokens": {"in": 15000, "out": 8000}, "artifacts": ["docs/plans/auth-prd.md"]}
{"ts": "2026-03-13T10:03:01Z", "event": "wave_completed", "wave": 1, "stages_passed": ["stage_1_prd"]}
{"ts": "2026-03-13T10:03:02Z", "event": "wave_started", "wave": 2, "stages": ["stage_2_plan", "stage_3_scaffold"]}
```

### 7.2 Progress Dashboard

After each wave, print a progress summary:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PIPELINE PROGRESS — Wave 4/10
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✅ Stage 1:  PRD              3m    (180 tokens)
  ✅ Stage 2:  Plan             5m    (240 tokens)
  ✅ Stage 3:  Scaffold         4m    (120 tokens)
  ⏭️  Stage 4:  Demo            SKIPPED (CLI project)
  🔄 Stage 5:  Schema           RUNNING...
  ⏳ Stage 6:  Pre-Tests        PENDING
  ⏳ Stage 7:  Implementation   PENDING
  ⏳ Stage 8:  Post-Tests       PENDING
  ⏳ Stage 9:  Review           PENDING
  ⏳ Stage 10: Deploy           PENDING
  ⏳ Stage 11: Docs             PENDING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Elapsed: 12m | Est. remaining: ~45m
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## STEP 8: Pipeline Completion

### 8.1 All Stages Passed

When all non-skipped stages have `"status": "passed"`:

1. Update state.json: `"pipeline_status": "completed"`
2. Generate `docs/stages/PIPELINE-SUMMARY.md`:
   - Pipeline ID, total duration, total tokens
   - Per-stage results (status, duration, retries, artifacts)
   - All decisions consolidated from all stages
   - All research findings consolidated
   - Test results summary
   - Deployment URL + health status
3. Invoke `/learn-n-improve` with mode "session"
4. Log final event: `pipeline_completed`
5. Report to user: deployment URL, health check, decisions for review

### 8.2 Pipeline Failed

If any stage exhausted retries and user chose to abort:

1. Update state.json: `"pipeline_status": "failed"`
2. Generate partial summary with completed stages and failure details
3. Log event: `pipeline_failed`
4. Report: what succeeded, what failed, what was blocked, suggested next steps

### 8.3 Pipeline Resumed

The pipeline supports resume from any point:

1. Read `.pipeline/state.json`
2. Find first non-passed, non-skipped stage
3. Validate all upstream artifacts still exist
4. Resume from that stage

```
# To resume:
/pipeline-orchestrator --resume
```

---

## MUST DO

- Always create `.pipeline/state.json` before dispatching any stage
- Always validate artifact contracts before dispatching downstream stages
- Always append to event log (never overwrite) — it is the audit trail
- Always tag git before each stage for clean rollback
- Always check idempotency — skip stages whose artifacts already exist and are valid
- Always print progress dashboard after each wave completes
- Always include failure context when retrying a stage
- Always cascade blockers to all transitive dependents of a failed stage
- Always generate pipeline summary on completion (success or failure)

## MUST NOT DO

- MUST NOT dispatch a stage before all its `depends_on` stages have passed — violates DAG ordering
- MUST NOT dispatch a stage if any `artifacts_in` are missing — contract violation
- MUST NOT retry more than 3 times per stage — escalate to user
- MUST NOT delete or overwrite the event log — append only
- MUST NOT skip artifact validation even if gate returns PASSED — trust but verify
- MUST NOT proceed past a failed stage to its dependents — mark them blocked
- MUST NOT hard-reset git without user confirmation — compensating rollback only
- MUST NOT hold pipeline state only in memory — persist to `.pipeline/state.json` after every state change
