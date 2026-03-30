# Spec: Workflow Master Agents — Federated Orchestration Architecture

## Meta
- Author: Claude Code
- Date: 2026-03-30
- Status: DRAFT
- Version: 1.0

---

## 1. Problem Statement

The project has 133 skills, 27 agents, and 20 rules organized into 8 workflow groups — but they operate as **isolated tools** with no coordination layer. The root causes:

1. **No shared context** — Each skill invocation starts from scratch. Output from `/brainstorm` isn't automatically available to `/writing-plans`. Users must manually pass context between skills.
2. **No automatic handoffs** — After one skill finishes, there's no system that knows what should run next. Users must memorize skill chains.
3. **No workflow-level state** — State is fragmented across `.pipeline/state.json`, `.skill-master-state.json`, `test-results/*.json`, and ad-hoc locations. No unified view of "where am I in this workflow?"
4. **No coordination between workflow groups** — Development-loop, testing-pipeline, and code-review have no communication protocol. When implementation finishes, testing doesn't automatically know.
5. **Entry point confusion** — Users must know which of 133 skills to invoke. `skill-master` helps but is reactive and doesn't compose multi-skill workflows automatically.

**What goes wrong without this:** Users spend more time orchestrating Claude Code than doing actual work. Skills that should chain together require 5-10 manual invocations with manual context copying. Complex tasks that should be "run the full development cycle" become "run brainstorm, copy the spec path, run writing-plans with that path, copy the plan path, run executing-plans..."

---

## 2. Chosen Approach

**Approach B (Revised): Dedicated Workflow Master Agents with Existing Orchestrators as Sub-Orchestrators**

Create 8 workflow-master agents (one per workflow group) that:
- Read their step DAG from a shared `config/workflow-contracts.yaml`
- Orchestrate all skills and sub-orchestrators within their workflow
- Manage per-workflow state under `.workflows/{workflow-id}/`
- Operate in dual mode: standalone (user invokes directly) or dispatched (project-manager-agent invokes as a pipeline stage worker)
- Pass structured context between steps so no skill starts from scratch

Existing orchestrators (`test-pipeline-agent`, `e2e-conductor-agent`) are absorbed as T2 sub-orchestrators — their code stays intact, they just get dispatched by the workflow master instead of by skills directly.

### Why This Approach Over Alternatives

| Alternative | Why Not |
|-------------|---------|
| **A: Config-only (no new agents)** | Adds contracts but no active orchestration layer. Skills still don't coordinate — it's a patch, not a fix. |
| **C: Federated/wrapping** | Creates an indirection layer where masters "wrap" existing orchestrators. Confused ownership (who handles retries — the wrapper or the wrapped?). With unlimited nesting, direct dispatch is cleaner than wrapping. |

---

## 3. Design

### 3.1 Config Schema — `config/workflow-contracts.yaml`

**Purpose:** The machine-readable playbook that every workflow-master reads at runtime. Externalizes workflow topology (what to execute and in what order) from agent bodies (how to execute).

**Structure per workflow:**

```yaml
defaults:
  max_retries_per_step: 3
  global_retry_budget: 15
  timeout_default_minutes: 20

workflows:
  {workflow-id}:
    description: "..."
    master_agent: {workflow-id}-master-agent
    state_file: ".workflows/{workflow-id}/state.json"

    sub_orchestrators:
      - agent: {existing-agent-name}
        role: "what it does"

    steps:
      - id: {step_id}
        skill: {skill-name}           # Skill() dispatch
        # OR
        dispatch: {agent-name}         # Agent() dispatch
        depends_on: [{upstream_ids}]
        artifacts_in:
          {name}: "{step_id}.artifacts_out.{name}"
        artifacts_out:
          {name}: { path: "...", schema: {schema_name} }
        gate: "{expression}"
        skip_when: "{condition}"
        timeout_minutes: N

    handoff_suggestions:
      - workflow: {next-workflow-id}
        when: "{condition}"
        reason: "..."

# Bridge: maps pipeline stages to workflow masters
stage_to_workflow:
  stage_1_prd: development-loop
  stage_7_impl: development-loop
  stage_8_post_tests: testing-pipeline
  stage_9_review: code-review
  stage_11_docs: documentation
  stage_10_deploy: null   # direct stage agent, no workflow master
```

**Key fields:**
- `skill:` vs `dispatch:` — distinguishes `Skill()` calls from `Agent()` calls
- `gate:` — machine-readable pass/fail expression evaluated against artifact JSON
- `skip_when:` — conditional step execution (same pattern as `pipeline-stages.yaml`)
- `stage_to_workflow` — bridges `pipeline-stages.yaml` stages to workflow masters for dispatched mode
- `handoff_suggestions` — standalone mode only, shown to user after workflow completes

**Full workflow definitions:** See the approved Section 1 design for complete YAML for all 8 workflows (development-loop, testing-pipeline, debugging-loop, code-review, documentation, session-continuity, learning-self-improvement, skill-authoring).

---

### 3.2 Master Agent Template — `core/.claude/agents/workflow-master-template.md`

**Purpose:** Shared orchestration DNA that all 8 master-agents reference. Prevents template drift by centralizing common protocols.

**Not an agent itself** — a reference document. Each concrete agent reads this at runtime via `Read` tool, same pattern as `pipeline-orchestrator` reading config at runtime.

**Contains 6 protocols:**

#### Protocol 1: Dual-Mode Operation
- **Standalone mode** (no Pipeline ID in prompt): Full lifecycle — init, execute, commit, report, handoff suggestions
- **Dispatched mode** (Pipeline ID present): Worker lifecycle — execute step subset, return contract to parent
- Mode detection: If prompt contains `## Pipeline ID:` and `## Mode: dispatched`, operate as worker

#### Protocol 2: Config-Driven Step Execution
1. Read `config/workflow-contracts.yaml` → find workflow by `master_agent` field
2. If dispatched with `## Execute Steps:` subset, filter to only those steps
3. Compute dependency graph from `depends_on`
4. For each step in dependency order:
   - Check `skip_when` → skip if true
   - Verify `depends_on` all PASSED
   - Verify `artifacts_in` exist on disk
   - Dispatch via `Skill()` or `Agent()` (based on `skill:` vs `dispatch:` field)
   - Verify `artifacts_out` exist on disk
   - Evaluate `gate:` expression
   - Update state file
5. On failure: retry (per-step + global budget), then escalate

#### Protocol 3: State Management
- State file: path from `state_file` field in config
- Schema:
  ```json
  {
    "workflow_id": "string",
    "mode": "standalone|dispatched",
    "pipeline_id": "string|null",
    "run_id": "{ISO-8601}_{git-sha}",
    "started_at": "ISO-8601",
    "status": "running|completed|failed|paused",
    "global_retries_used": 0,
    "global_retries_remaining": 15,
    "steps": {
      "{step_id}": {
        "status": "pending|running|passed|failed|skipped",
        "retries": 0,
        "started_at": null,
        "completed_at": null,
        "artifacts_produced": {},
        "gate_result": null,
        "error": null
      }
    }
  }
  ```
- Update after EVERY step completion/failure
- Append-only event log: `.workflows/{workflow-id}/events.jsonl`

#### Protocol 4: Context Passing Between Steps
Every step dispatch includes:
```json
{
  "workflow": "{workflow_id}",
  "step": "{step_id}",
  "mode": "standalone|dispatched",
  "upstream_artifacts": { "{name}": "{path}" },
  "upstream_summaries": { "{step_id}": "one-line summary" },
  "user_input": "original request",
  "decisions_so_far": ["list of decisions"]
}
```
This is the root cause fix — no skill starts from scratch.

#### Protocol 5: Cross-Workflow Interface
- **Input contract** (dispatched mode): Pipeline ID, upstream artifacts, step subset, expected outputs
- **Output contract** (return to parent): `{gate, artifacts, decisions, blockers, summary, duration_seconds}`
- **State isolation**: Own state = read/write. Parent state = read-only. Sibling state = read-only.

#### Protocol 6: Progress Reporting
```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{WORKFLOW_NAME} — Step {N}/{total}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✅ step_1        summary (artifact path)
  🔄 step_2        RUNNING...
  ⏳ step_3        PENDING
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Retries: 2/15 | Mode: standalone
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

### 3.3 Concrete Master Agents (8 total)

Each is a thin ~60-80 line agent that declares:
- Workflow identity (`workflow_id`, config source)
- Reference to template (`Read workflow-master-template.md`)
- Core responsibilities (4 max, per Rule #8)
- Domain-specific overrides (e.g., screenshot verdict authority for testing)
- Output format additions beyond standard template

**Agents to create:**

| Agent File | Workflow | Sub-Orchestrators Absorbed | Domain Overrides |
|-----------|----------|---------------------------|-----------------|
| `development-loop-master-agent.md` | development-loop | `plan-executor-agent`, `planner-researcher-agent` | Complexity-based step skipping (simple tasks skip brainstorm+plan) |
| `testing-pipeline-master-agent.md` | testing-pipeline | `test-pipeline-agent`, `e2e-conductor-agent`, `tester-agent`, `test-failure-analyzer-agent` | Screenshot verdict authority, flaky test handling, coverage delta |
| `debugging-loop-master-agent.md` | debugging-loop | `debugger-agent`, `test-failure-analyzer-agent` | Root cause classification, learning recording mandatory |
| `code-review-master-agent.md` | code-review | `code-reviewer-agent`, `security-auditor-agent` | Review gate verdict matrix, deferred item TTL |
| `documentation-master-agent.md` | documentation | `docs-manager-agent` | Parallel step execution (ADR + API docs), staleness scoring |
| `session-continuity-master-agent.md` | session-continuity | `session-summarizer-agent` | Mode-aware (save vs restore), context compression |
| `learning-self-improvement-master-agent.md` | learning-self-improvement | `session-summarizer-agent`, `context-reducer-agent` | Pattern detection thresholds, skill proposal validation |
| `skill-authoring-master-agent.md` | skill-authoring | `skill-author-agent` | Quality gate enforcement (pattern-structure, portability, self-containment rules) |

---

### 3.4 Updated Agent Orchestration Rules

Changes to `.claude/rules/agent-orchestration.md` (also mirrored to `core/.claude/rules/`):

| Rule | Change | New Content |
|------|--------|-------------|
| **#2** | Replace "Max 2 Nesting" | **4-tier model:** T0 (pipeline) → T1 (workflow master) → T2 (sub-orchestrator) → T3 (worker). T3 = Skill() only. Max depth 4. Visibility rule: every tier returns structured JSON to parent. |
| **#3** | Replace "No Subagent-Spawning" | **Controlled nesting:** Agent at tier N dispatches tier N+1 only. Never same tier or above. T3 = leaf. Failure attribution must propagate upward with specifics. |
| **#6** | Expand scope | **Single state per scope:** Pipeline = `.pipeline/state.json`. Per-workflow = `.workflows/{id}/state.json`. Owner = one agent. Parent reads child state (read-only). No cross-sibling writes. |
| **#9 (new)** | Add | **Workflow contracts as SSOT:** Masters MUST read `config/workflow-contracts.yaml`. No hardcoded chains in agent bodies. Config = topology, agent = protocol. |
| **#10 (new)** | Add | **Dual-mode operation:** Standalone (full lifecycle) vs dispatched (worker). Mode detected by Pipeline ID in prompt. Skip commit steps in dispatched mode. |
| **#11 (new)** | Add | **Mandatory context passing:** Every step dispatch includes upstream artifacts, summaries, decisions, user input. No skill starts from scratch. Context MUST be structured JSON. |

Rules #1, #4, #5, #7, #8 unchanged.

---

### 3.5 Integration Points

#### project-manager-agent → Workflow Masters
- Reads `stage_to_workflow` mapping from `config/workflow-contracts.yaml`
- Dispatches workflow-masters with `## Mode: dispatched` and `## Execute Steps:` subset
- Workflow master executes only the requested steps, returns standard contract
- Stages with `null` mapping use direct stage agent dispatch (legacy behavior)

#### skill-master → Workflow Masters
- Step 2 (Parse Intent) updated: check task complexity before matching individual skills
- Complex tasks (6+ files, cross-layer) → route to workflow master
- Medium tasks → present choice: individual skill or workflow
- Simple tasks → route to individual skill directly

#### Workflow Masters ↔ Each Other (Standalone Mode)
- After completing, display `handoff_suggestions` from config
- User chooses next workflow or skips
- Next workflow reads previous workflow's state file (read-only) for upstream artifacts
- No automatic cross-workflow dispatch in standalone mode — user stays in control

#### Thin Skill Wrappers (8 total)
- Each workflow gets a slash-command entry point: `/development-loop`, `/testing-pipeline`, etc.
- ~40 lines each: frontmatter + `Agent()` dispatch + result relay
- Same pattern as existing `pipeline-orchestrator/SKILL.md`

---

### 3.6 Updated `project-manager-agent.md`

Add to Stage Dispatch Protocol section:
- Check `config/workflow-contracts.yaml` → `stage_to_workflow` before dispatching
- If mapping exists → dispatch workflow-master with step subset in dispatched mode
- If mapping is null → dispatch direct stage agent (unchanged)
- Update MUST NOT rule: remove "MUST NOT let dispatched stage agents spawn their own subagents" (now allowed per tier model)

---

## 4. Requirement Tiers

### Must Have (MVP)
- `config/workflow-contracts.yaml` with all 8 workflow definitions
- `workflow-master-template.md` with all 6 protocols
- 4 primary master-agents: `development-loop`, `testing-pipeline`, `debugging-loop`, `code-review`
- Updated `agent-orchestration.md` rules (#2, #3, #6, #9, #10, #11)
- 4 thin skill wrappers for the primary workflows
- Updated `project-manager-agent.md` dispatch protocol
- `.workflows/` directory structure and `.gitignore` entry

### Nice to Have (v1.1)
- 4 secondary master-agents: `documentation`, `session-continuity`, `learning-self-improvement`, `skill-authoring`
- 4 thin skill wrappers for secondary workflows
- Updated `skill-master` routing to detect workflow-level tasks
- `handoff_suggestions` in config and display logic
- Cross-workflow state reading (next workflow reads previous workflow's state)

### Out of Scope
- Automatic cross-workflow dispatch in standalone mode (users stay in control)
- Visual UI/dashboard for workflow state (terminal progress bars are sufficient)
- Workflow version history or migration tooling
- Custom user-defined workflows (only the 8 predefined groups)
- Changes to existing individual skills (they remain independently invocable)

---

## 5. Open Questions

1. **Registry entries** — Do the 8 thin skill wrappers get entries in `registry/patterns.json`? **Recommendation:** Yes, they're distributable patterns in `core/.claude/skills/`.

2. **hub-sync workflow** — The 9th workflow group in `workflow-groups.yml` is `hub-sync`. It's hub-only (not distributable). Should it get a master-agent in `.claude/agents/` (hub-only) or skip? **Recommendation:** Skip for MVP — it has only 3 skills and is hub-specific.

3. **Backward compatibility** — Users who invoke `/fix-loop` directly should still work. Individual skills must remain independently invocable. **Decision:** No changes to existing skills. Workflow masters are additive — they coordinate skills but don't modify them.

4. **Config validation** — Should `workflow_quality_gate_validate_patterns.py` be extended to validate `workflow-contracts.yaml`? **Recommendation:** Yes, in v1.1. Validate: step references exist as skills/agents, artifact paths don't conflict, DAG has no cycles.

---

## 6. Success Criteria

1. **User can invoke `/development-loop "add payment feature"` and get ideation → planning → implementation → verification → commit without manual handoffs** — measured by: zero manual skill invocations needed between steps.

2. **project-manager-agent dispatches workflow masters instead of raw stage agents** — measured by: pipeline runs use workflow masters for mapped stages, return contracts match expected schema.

3. **Context flows between steps** — measured by: `/writing-plans` receives the spec path from `/brainstorm` automatically, `/auto-verify` receives changed file paths from implementation automatically.

4. **Workflow state is resumable** — measured by: interrupting a workflow mid-step and re-invoking continues from the last checkpoint, not from scratch.

5. **Existing skills work unchanged** — measured by: all current tests pass, individual skill invocations (`/fix-loop`, `/brainstorm`, etc.) still work standalone.

6. **No template drift across master-agents** — measured by: shared protocols live in template, concrete agents contain only domain-specific overrides (each under 100 lines).

---

## 7. Files to Create/Modify

### New Files (MVP)

| File | Type | Lines (est.) |
|------|------|-------------|
| `config/workflow-contracts.yaml` | Config | ~350 |
| `core/.claude/agents/workflow-master-template.md` | Reference | ~250 |
| `core/.claude/agents/development-loop-master-agent.md` | Agent | ~80 |
| `core/.claude/agents/testing-pipeline-master-agent.md` | Agent | ~80 |
| `core/.claude/agents/debugging-loop-master-agent.md` | Agent | ~70 |
| `core/.claude/agents/code-review-master-agent.md` | Agent | ~70 |
| `core/.claude/skills/development-loop/SKILL.md` | Skill wrapper | ~40 |
| `core/.claude/skills/testing-pipeline-workflow/SKILL.md` | Skill wrapper | ~40 |
| `core/.claude/skills/debugging-loop/SKILL.md` | Skill wrapper | ~40 |
| `core/.claude/skills/code-review-workflow/SKILL.md` | Skill wrapper | ~40 |

### Modified Files (MVP)

| File | Change |
|------|--------|
| `.claude/rules/agent-orchestration.md` | Update rules #2, #3, #6; add #9, #10, #11 |
| `core/.claude/rules/agent-orchestration.md` | Mirror same changes (distributable copy) |
| `core/.claude/agents/project-manager-agent.md` | Add workflow-master dispatch protocol |
| `registry/patterns.json` | Add entries for 4 new agents + 4 new skills |
| `config/workflow-groups.yml` | Add master-agent references to each group |
| `.gitignore` | Add `.workflows/` |

### New Files (v1.1)

| File | Type | Lines (est.) |
|------|------|-------------|
| `core/.claude/agents/documentation-master-agent.md` | Agent | ~70 |
| `core/.claude/agents/session-continuity-master-agent.md` | Agent | ~60 |
| `core/.claude/agents/learning-self-improvement-master-agent.md` | Agent | ~70 |
| `core/.claude/agents/skill-authoring-master-agent.md` | Agent | ~70 |
| 4 thin skill wrappers for secondary workflows | Skills | ~40 each |

---

## 8. Implementation Order

1. **Config first** — `config/workflow-contracts.yaml` (foundation everything reads)
2. **Rules update** — `agent-orchestration.md` (unblocks new nesting patterns)
3. **Template** — `workflow-master-template.md` (shared DNA)
4. **Primary agents** — 4 master-agents (development-loop, testing-pipeline, debugging-loop, code-review)
5. **Skill wrappers** — 4 thin slash-command entry points
6. **Integration** — Update `project-manager-agent.md` dispatch protocol
7. **Registry** — Update `registry/patterns.json` + regenerate docs
8. **Validation** — Run CI validators, verify existing tests still pass
