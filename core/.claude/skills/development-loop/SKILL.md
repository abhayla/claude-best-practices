---
name: development-loop
description: >
  Orchestrate the full development cycle end-to-end as a skill-at-T0 orchestrator
  (Phase 3.2 of subagent-dispatch-platform-limit remediation). The skill body IS
  the orchestrator — it runs in the user's T0 session and drives: ideate →
  plan → execute → verify → commit. Dispatches flat worker subagents
  (plan-executor-agent, optionally planner-researcher-agent) via Agent() at T0
  where subagent dispatch actually works. Invokes inline sub-skills
  (/brainstorm, /writing-plans, /auto-verify, /post-fix-pipeline) via Skill().
  Use when building a feature end-to-end. For bug fixes use /fix-issue or
  /debugging-loop; for just implementation use /implement.
type: workflow
triggers:
  - full development cycle
  - develop feature from scratch
  - ideate plan build verify
  - development workflow
  - feature end to end
  - new feature end to end
allowed-tools: "Agent Bash Read Write Edit Grep Glob Skill"
argument-hint: "<feature description, issue URL, or spec file path>"
version: "2.0.0"
---

# /development-loop — Skill-at-T0 Orchestrator

This skill's body is injected into the user's T0 session and executed there.
T0 dispatches workers via `Agent()` (the only reliably-parallel dispatch point
in Claude Code) and invokes sub-skills via `Skill()`. The retired
`development-loop-master-agent` is NOT dispatched (deprecated Phase 3.2,
2026-04-24); its orchestration lives here.

**Why skill-at-T0:** Anthropic's Claude Code doesn't forward the `Agent` tool
to dispatched subagents ([docs](https://code.claude.com/docs/en/sub-agents),
[GH #19077](https://github.com/anthropics/claude-code/issues/19077)). The
legacy `development-loop-master-agent` → `plan-executor-agent` (T2) dispatch
chain would silently inline the T2 work at runtime. This body runs at T0
where `Agent()` actually works. Canonical pattern:
`core/.claude/agents/workflow-master-template.md` v2.0.0 (Phase 3.0);
test-pipeline Phase 3.1 reference in spec v2.2.

**Input:** `$ARGUMENTS`

If `$ARGUMENTS` is empty, ask the user to describe the feature before proceeding.

If the task is trivial (single file, config change, fewer than ~3 files affected),
suggest `/implement` directly. Proceed with the full cycle only on confirmation.

---

## CLI Signature

```
/development-loop <feature description | issue URL | spec file path>
                  [--skip-ideate] [--skip-plan]
                  [--research] [--no-commit]
```

| Flag | Default | Meaning |
|------|---------|---------|
| `--skip-ideate` | auto (Simple/Medium) | Skip STEP 2 IDEATE even if complexity suggests it |
| `--skip-plan` | auto (Simple only) | Skip STEP 3 PLAN; go straight from ideate to execute |
| `--research` | off | Dispatch `planner-researcher-agent` during IDEATE for deep research before brainstorming |
| `--no-commit` | off | Stop after STEP 5 VERIFY; do not run STEP 6 COMMIT |

---

## STEP 1: INIT

1. **Parse args + assess complexity.** Score the request:
   - **Simple**: single file, typo, config change, "quick", "just" — EXECUTE → VERIFY → COMMIT (skip IDEATE + PLAN)
   - **Medium**: 2–5 files, single feature, clear scope — PLAN → EXECUTE → VERIFY → COMMIT (skip IDEATE)
   - **Complex**: 6+ files, cross-layer, architecture decisions — all 5 steps
   - Uncertain → **Medium**
   - `--skip-*` flags override the heuristic
2. **Read config.** `Read config/workflow-contracts.yaml` → `workflows.development-loop`. Pull step DAG + artifact contracts. master_agent should be null (Phase 3.2); sub_orchestrators should be empty list.
3. **Generate `run_id`.** `{ISO-8601}_{7-char git sha}` with `:` → `-`.
4. **Initialize state.** `Write .workflows/development-loop/state.json`:
   ```json
   {
     "schema_version": "2.0.0",
     "run_id": "<run_id>",
     "started_at": "<iso>",
     "complexity": "Simple | Medium | Complex",
     "steps_to_execute": ["ideate", "plan", "execute", "verify", "commit"],
     "step_status": { "INIT": "done", "IDEATE": "pending", ... },
     "artifacts": {},
     "dispatches_used": 0
   }
   ```
5. **Append INIT event** to `events.jsonl`.

---

## STEP 2: IDEATE (skip if complexity=Simple or Medium)

If `--research` flag set OR the request mentions unfamiliar tech/architecture:

```
Agent(subagent_type="planner-researcher-agent", prompt="""
## Mode: deep_research
## User request: <original input>
## Output: research findings for the ideate step

Investigate unfamiliar tech, architectural precedent, library choices.
Return structured findings JSON for feeding into /brainstorm.
""")
```

Then invoke the brainstorm sub-skill with research context (if any):

```
Skill("/brainstorm", args="<user request> [research context]")
```

`/brainstorm` writes `docs/specs/<feature>-spec.md`. Capture path into
`state.artifacts.spec`. Increment `dispatches_used` by 1 if researcher was
dispatched.

---

## STEP 3: PLAN (skip if complexity=Simple)

```
Skill("/writing-plans", args="<spec path from ideate>")
```

`/writing-plans` writes `docs/plans/<feature>-plan.md`. Capture into
`state.artifacts.plan`.

If STEP 2 was skipped, use the user's raw request instead of a spec path.

---

## STEP 4: EXECUTE

Dispatch the plan executor as a flat worker from T0:

```
Agent(subagent_type="plan-executor-agent", prompt="""
## Workflow: development-loop
## Run ID: <run_id>
## Plan file: <path from state.artifacts.plan>
## Original user request: <input>
## Upstream artifacts:
##   spec: <if exists>
##   plan: <path>
## Upstream decisions:
##   complexity: <assessment>
##   steps_skipped: <list>
## Flag: --checkpoint-per-task

Execute every task in the plan file sequentially. Commit after each task for
recovery checkpointing. Return contract: {
  "gate": "PASSED|FAILED|BLOCKED",
  "tasks_completed": <int>,
  "tasks_total": <int>,
  "changed_files": [<paths>],
  "blockers": [...],
  "summary": "<line>"
}
""")
```

Worker runs in its own session; it MUST NOT `Agent()` further (platform rule).
Capture return contract; increment `dispatches_used` by 1.

If `gate: BLOCKED` or `FAILED` → abort with structured BLOCKED verdict; go to
STEP 7 REPORT without STEP 5 or STEP 6.

---

## STEP 5: VERIFY

```
Skill("/auto-verify", args="--strict-gates")
```

Read `test-results/auto-verify.json` after the skill returns. Gate:

```
if verification.result != "PASSED":
    emit FAILED state; STEP 6 COMMIT is BLOCKED
```

For richer verification (full fix→verify→commit with triage), the caller MAY
invoke `/test-pipeline` at STEP 6 instead. `/auto-verify` is the narrower
check — just "do the tests pass" — which is what the development-loop needs.

---

## STEP 6: COMMIT

Skip if `--no-commit` flag set OR STEP 5 gate failed.

```
Skill("/post-fix-pipeline", args="<run_id>, <verification.json path>")
```

`/post-fix-pipeline` handles: documentation updates, commit message
synthesis, actual git commit (respects user's in-progress work per
git-collaboration.md rule 6).

Update `state.artifacts.commit_sha`.

---

## STEP 7: REPORT

1. **Finalize state.** Mark all terminal steps done. Write
   `test-results/development-loop-verdict.json`:
   ```json
   {
     "schema_version": "2.0.0",
     "run_id": "<run_id>",
     "result": "PASSED | FAILED | BLOCKED",
     "complexity": "<assessed>",
     "steps_executed": [...],
     "steps_skipped": [...],
     "artifacts": { "spec": <path|null>, "plan": <path|null>,
                    "source_changes": [<files>], "verification": <path|null>,
                    "commit_sha": <sha|null> },
     "budget_used": { "dispatches_used": <n> },
     "finalized_at": "<iso>"
   }
   ```
2. **User-facing dashboard:**
   ```
   ============================================================
   Development Loop: <PASSED | FAILED | BLOCKED>
     Run ID: <run_id>
     Complexity: <Simple | Medium | Complex>
     Steps: <executed>/<total> (skipped: <list>)
     Changed files: <count>
     Evidence: test-results/auto-verify.json
     Commit: <sha or SKIPPED>
   ============================================================
   ```
3. **Handoff suggestions** (only if PASSED and STEP 6 committed):
   - `Next: /test-pipeline` for three-lane verification
   - `Next: /code-review-workflow` to prepare PR

---

## CRITICAL RULES

- MUST run at T0 — this skill's body is injected into the user's session.
  If dispatched as a worker (i.e., from another agent), `Agent` is stripped
  at runtime and the EXECUTE step dispatch silently becomes inline serial
  work — the exact 2026-04-24 platform failure mode that Phase 3.1 + 3.2
  are retiring.
- MUST NOT dispatch `development-loop-master-agent` (deprecated 2026-04-24,
  2-version-cycle window). Its orchestration is inlined here.
- MUST honor complexity assessment — Simple/Medium/Complex drives step skip.
  Dispatching the full 5-step chain for a typo fix wastes the user's time
  and burns retry budget unnecessarily.
- MUST pass upstream artifacts + decisions + original request into every
  worker dispatch (plan-executor-agent, planner-researcher-agent). No
  worker starts from scratch — spec v2.2 §3.5 context-passing rule.
- MUST write `.workflows/development-loop/state.json` and `events.jsonl`
  after every step transition. This is the ONLY canonical state file;
  workers read paths from dispatch context, never write state directly.
- MUST NOT commit if STEP 5 VERIFY failed — the gate is non-negotiable.
  Unverified code reaching commit undermines the entire pipeline's trust
  model (testing.md + claude-behavior.md rule 4).
- MUST emit both `Agent()` calls (researcher + executor) in separate T0
  messages — not parallel — because they have a strict data dependency
  (researcher → ideate → plan → executor). Parallelism doesn't apply here.
