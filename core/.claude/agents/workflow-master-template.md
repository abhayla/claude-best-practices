---
name: workflow-master-template
description: >
  Shared orchestration protocol reference for workflow orchestrators in
  core/.claude/skills/. Not an invokable agent — a reference document
  consulted when creating or refactoring a workflow orchestrator skill.
  Rewritten 2026-04-24 (v2.0.0) to reflect the skill-at-T0 pattern after
  the platform finding that subagents cannot dispatch further subagents
  (Anthropic docs: "subagents cannot spawn other subagents"). See
  agent-orchestration.md §1-3.
model: inherit
version: "2.0.0"
---

# Workflow Orchestrator Template — Shared Protocol (skill-at-T0 pattern)

This is a reference document, not an invokable pattern. Use it as the
authoritative structure when creating or refactoring a workflow
orchestrator at `core/.claude/skills/<workflow-id>/SKILL.md`.

> **Platform note (2026-04-24).** Claude Code does not forward the `Agent`
> tool to dispatched subagents ([official docs](https://code.claude.com/docs/en/sub-agents):
> *"subagents cannot spawn other subagents"*, confirmed by [GH #19077](https://github.com/anthropics/claude-code/issues/19077)
> and [GH #4182](https://github.com/anthropics/claude-code/issues/4182)). A
> workflow orchestrator therefore cannot itself be a dispatched agent. It
> MUST run at T0 (the user's session). The slash-command skill IS the
> orchestrator: its body is injected into T0, and the T0 session executes
> the orchestration logic with `Agent()` actually available for worker
> dispatch. See `agent-orchestration.md` §1-3 for the normative constraint.

## Protocol 1: Skill-at-T0 Pattern

A workflow orchestrator is a slash-command skill whose body IS the
orchestration logic. When the user invokes `/<workflow-id>`, the skill's
body is injected into the user's T0 session; the session then runs the
orchestration, dispatching worker subagents via `Agent()` where useful
(which is allowed because T0 has `Agent` in its tool set).

### Skill structure

```yaml
---
name: <workflow-id>
description: >
  <action-verb> ... — one-sentence purpose. Use when <trigger>.
triggers:
  - <natural-language trigger phrases>
type: workflow
allowed-tools: "Agent Bash Read Write Edit Grep Glob Skill"
argument-hint: "<arg description>"
version: "1.0.0"
---

# <Workflow Title>

## STEP 1: Initialize state
...

## STEP N: Final step
...

## MUST DO
...

## MUST NOT DO
...
```

There is no separate `<workflow-id>-master-agent` in the new pattern; the
legacy workflow-master agent pattern is retired (see
`agent-orchestration.md` §10). Workers referenced by the orchestrator are
flat subagents in `core/.claude/agents/` whose `dispatched_from:` field
is `worker` (Phase 2 validator enforces this).

## Protocol 2: Config-Driven Step Execution

The orchestrator reads `config/workflow-contracts.yaml` → `workflows.<workflow-id>`
at the start of every run. It MUST NOT hardcode the step DAG, artifact
paths, or skill chain.

1. Read the workflow contract for the current `<workflow-id>`
2. Load steps; build dependency graph from each step's `depends_on`
3. Topologically sort; identify parallel opportunities (steps whose
   dependencies are all satisfied simultaneously)

For each step, in dependency order:

1. **Skip check** — Evaluate `skip_when`. If true, mark SKIPPED, continue.
2. **Dependency check** — Verify all `depends_on` steps are PASSED or SKIPPED.
3. **Artifact input check** — For each entry in `artifacts_in`, verify the
   referenced artifact exists on disk. If missing, BLOCK.
4. **Dispatch**:
   - If step has `skill:` → `Skill("{skill}", args="{context}")` — runs inline
     in the T0 session
   - If step has `dispatch:` → `Agent(subagent_type="{agent}", prompt="{context}")`
     — spawns a worker subagent (works because we are at T0)
5. **Output validation** — Verify all `artifacts_out` exist on disk.
6. **Gate evaluation** — If step has `gate:` expression, evaluate it against
   the artifact JSON. Examples:
   - `"verification.result == PASSED"` — read the JSON file, check the field
   - `"fix_result.result IN (PASSED, FIXED)"` — membership test
7. **State update** — Write step status to the state file.
8. **Event log** — Append to `.workflows/{workflow-id}/events.jsonl`.

### Parallel dispatch at T0

When two or more steps have satisfied dependencies AND no mutual
dependency, dispatch them together in a SINGLE T0 message with multiple
`Agent()` calls:

```
# Single T0 message, two Agent() calls run concurrently
Agent(subagent_type=<worker-A>, prompt="...")
Agent(subagent_type=<worker-B>, prompt="...")
```

This is the ONLY reliable parallelism in Claude Code (empirically verified
2026-04-24 — see `.claude/tasks/lessons.md`). Multiple `Skill()` calls
in one message serialize as a prompt-injection queue; multiple `Bash()`
calls in one message serialize at the runtime level. Parallelism requires
T0 + `Agent()`.

### Workers MUST NOT nest-dispatch

Each worker agent dispatched above runs as a subagent — the platform
strips `Agent` from its tool set regardless of frontmatter. Worker bodies
that attempt `Agent(subagent_type=...)` will silently inline their work,
producing serial execution instead of the intended parallelism. If a
worker needs its own fan-out, it MUST return a structured contract
listing the sub-tasks; the T0 orchestrator reads the contract and
dispatches the next wave at T0.

## Protocol 3: Retry and Failure Handling

Enforce a **global retry budget** per workflow run (default 15):

1. Retry each step up to `max_retries_per_step` (from config defaults).
2. Each retry decrements `global_retries_remaining` in state.
3. If step retries exhausted → mark FAILED, check if downstream steps can
   still run (they can if their remaining dependencies are all PASSED).
4. If global budget exhausted → STOP. Report failures to the user.

Workers propagate structured failure details (step, error, retry count).
The T0 orchestrator decides whether to retry the same worker, dispatch an
alternative, or escalate — workers do NOT retry themselves.

## Protocol 4: State Management

State file location: `state_file` field from `config/workflow-contracts.yaml`
(e.g., `.workflows/{workflow-id}/state.json`).

### Initialization
At workflow start:

```bash
mkdir -p .workflows/{workflow-id}/
```

Create the state file with:

```json
{
  "workflow_id": "{workflow-id}",
  "schema_version": "1.0.0",
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

- MUST update the state file after every step status change
- MUST append every significant event to `.workflows/{workflow-id}/events.jsonl`
  (append-only, one JSON per line)
- On resume: read state, find first non-PASSED/non-SKIPPED step, validate
  upstream artifacts exist, continue from there

## Protocol 5: Worker Dispatch Context

Every worker dispatch MUST include upstream context — never just the
step's immediate `artifacts_in`. Workers cannot see any state from
previous steps unless the orchestrator passes it explicitly.

```
Agent(subagent_type=<worker>, prompt="
  ## Workflow: {workflow_id}
  ## Step: {step_id}
  ## Run ID: {run_id}

  ## Upstream Artifacts
  {artifact_name}: {path_on_disk}

  ## Previous Steps (one-line summaries)
  {step_id}: {summary}

  ## User Request
  {original request}

  ## Decisions So Far
  - {decision_1}

  ## Instructions
  {worker-specific task}

  ## Return Contract
  Return structured JSON:
  {
    \"gate\": \"PASSED | FAILED\",
    \"artifacts\": { \"name\": \"path_on_disk\" },
    \"decisions\": [\"...\"],
    \"blockers\": [\"...\"],
    \"summary\": \"one-paragraph summary\",
    \"duration_seconds\": <number>
  }
")
```

The worker executes, writes artifacts to disk, and returns the contract.
The T0 orchestrator reads the contract to decide next steps.

## Protocol 6: Progress Reporting

After each step completes, print a progress dashboard:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{WORKFLOW_NAME} — Step {completed}/{total}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✅ step_1     summary (artifact path)
  ✅ step_2     summary (artifact path)
  🔄 step_3     RUNNING...
  ⏳ step_4     PENDING
  ⏭️  step_5     SKIPPED (reason)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Retries: {used}/{budget}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### Workflow completion report

At workflow end:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{WORKFLOW_NAME} — COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Steps: {passed}/{total} passed, {skipped} skipped
Retries used: {used}/{budget}
Duration: {total_time}

Artifacts produced:
  - {path} (from {step_id})

Decisions made:
  - {decision}

SUGGESTED NEXT WORKFLOWS (from handoff_suggestions):
  1. /{workflow_id} — {reason}
  2. /{workflow_id} — {reason}

Continue with a workflow? (1/2/skip)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## Protocol 7: Cross-Workflow Handoffs

Each workflow runs independently at T0. The orchestrator reads
`handoff_suggestions` from its workflow contract and surfaces the next
slash command to the user; the user decides whether to invoke it.

There is no automatic chained dispatch. Automatic chaining would require
Agent()-invoking-an-orchestrator-skill, but a skill cannot be dispatched
via `Agent()` and running an orchestrator agent means the orchestrator
becomes a subagent — losing the `Agent` tool and therefore losing the
ability to dispatch workers. Always return control to the user between
workflows.

If cross-workflow state is needed:

1. Read `.workflows/{previous-workflow}/state.json` (read-only)
2. Extract `artifacts_produced` from completed steps
3. Use as optional upstream context — do NOT require them (the user may
   be starting from a different state)

## Appendix A: Migrating a legacy workflow-master-agent to this pattern

If you have a `<workflow-id>-master-agent.md` file in `core/.claude/agents/`
that was written against the old tier model:

1. Copy the orchestration logic from the agent body into a new or existing
   `core/.claude/skills/<workflow-id>/SKILL.md` as the skill body
2. Replace all `Agent(subagent_type=<sub-orchestrator>, …)` calls with
   direct flat worker dispatches — remove the intermediate "sub-
   orchestrator" layer
3. Mark the agent file `deprecated: true` with `deprecated_by:
   <workflow-id-skill>` (per `pattern-structure.md` Deprecation Lifecycle)
4. Remove the workflow's `sub_orchestrators:` list from
   `config/workflow-contracts.yaml` (the field is no longer meaningful)
5. Update `registry/patterns.json`: bump hashes, update descriptions, add
   deprecation fields on the old agent entry
6. Run the 4 CI gates:
   - `PYTHONPATH=. python scripts/dedup_check.py --validate-all`
   - `PYTHONPATH=. python scripts/dedup_check.py --secret-scan`
   - `PYTHONPATH=. python scripts/workflow_quality_gate_validate_patterns.py`
   - `PYTHONPATH=. python -m pytest scripts/tests/`

## Appendix B: Common worker patterns

Workers are focused single-responsibility agents. Declare their frontmatter
with `dispatched_from: worker` so the Phase 2 validator recognizes them as
flat workers that must NOT declare `Agent` in `tools:`.

Typical worker responsibilities (one per agent):
- Test execution (e.g., `tester-agent`, `fastapi-api-tester-agent`)
- Code analysis (e.g., `test-failure-analyzer-agent`, `code-reviewer-agent`)
- Fix proposal (e.g., `android-build-fixer-agent`)
- External system interaction (e.g., `github-issue-manager-agent`)
- Information capture (e.g., `session-summarizer-agent`)

Workers return structured contracts and write artifacts to disk; they do
not drive the overall flow. The orchestrator owns the flow.
