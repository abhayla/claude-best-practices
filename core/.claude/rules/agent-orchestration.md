---
description: Constraints for multi-agent orchestration patterns in agents and skills.
globs: [".claude/agents/*.md", ".claude/skills/*/SKILL.md"]
---

# Agent Orchestration Constraints

> **Platform constraint (verified 2026-04-24):** Claude Code does not forward the `Agent` tool to dispatched subagents, regardless of what their frontmatter `tools:` field declares. [Anthropic's official documentation](https://code.claude.com/docs/en/sub-agents) states this directly: *"subagents cannot spawn other subagents."* Corroborated by open GitHub issues [#19077](https://github.com/anthropics/claude-code/issues/19077) and [#4182](https://github.com/anthropics/claude-code/issues/4182) and by three independent runtime probes. All rules below reflect this constraint — orchestration is single-level by platform design, not by preference. See §2 for the normative model.

## 1. Orchestrators MUST Run at T0

Multi-stage coordination that dispatches worker subagents MUST execute in the user's T0 session. Two patterns are valid:

| Pattern | Shape | When to use |
|---------|-------|-------------|
| **Agent-at-T0** | Agent invoked directly by the user (not dispatched from another agent) | Orchestrator needs a persistent persona, reusable state, or rich context management |
| **Skill-at-T0** | Slash command whose body is injected into the user's T0 session; the session executes the orchestration logic with `Agent` available | Orchestrator is stateless prompt logic; simpler to maintain as a skill |

Both patterns are valid because both run at T0 where `Agent()` is actually available. A skill that merely dispatches an agent (a "thin wrapper skill") is also valid, but the resulting agent MUST be one whose own design assumes it runs at T0 — not one whose design assumes it is an intermediate-tier orchestrator.

MUST NOT write an agent that dispatches worker subagents AND is itself intended to be dispatched as a subagent. Such an agent would declare `Agent` in `tools:` but never receive it at runtime, silently producing inline work instead of dispatched parallelism — the exact failure mode observed in the 2026-04-24 testbed run.

## 2. Single-Level Dispatch Model

All orchestration obeys the platform's single-dispatch-level constraint:

| Role | Where it runs | What it can dispatch |
|------|---------------|----------------------|
| **Orchestrator** | T0 (user session or skill injected into T0) | Worker subagents via `Agent()`, utility skills via `Skill()` |
| **Worker** | Subagent session dispatched by the T0 orchestrator | Skills via `Skill()`. MUST NOT attempt `Agent()` — it is absent at runtime regardless of frontmatter. |

**One dispatch level is the hard limit.** A T0 orchestrator → worker dispatch chain is 1 level deep. No worker can spawn another subagent. If a task decomposition needs work that looks multi-level, flatten it:

- The T0 orchestrator dispatches a first wave of workers
- Workers return structured contracts to T0
- T0 reads the contracts and dispatches a second wave based on the results

Parallelism is preserved at the T0 dispatch point: multiple `Agent()` calls in a single T0 message run concurrently. Parallelism inside a worker session is NOT reliably available — empirical probes confirm `Bash`, `Skill`, and other tool calls in one message execute serially in subagent sessions.

**Tier labels (T0/T1/T2/T3) are retained for responsibility-ownership documentation only.** They describe *who owns what* in a design, not a runtime dispatch chain. Existing references to "T1 dispatches T2 via `Agent()`" are legacy — treat them as describing design intent, not a runtime behavior. Phase-refactored patterns will collapse the tier labels into "orchestrator" and "worker".

**Visibility rule:** Every worker MUST return a structured contract (JSON with `gate`, `artifacts`, `summary` fields) to the T0 orchestrator. The orchestrator MUST NOT proceed to the next wave until it has read the return. No fire-and-forget dispatches.

## 3. Worker Agent Constraints

Workers (agents dispatched from a T0 orchestrator) MUST conform to:

1. **No `Agent` in `tools:` declarations.** Declaring `Agent` is misleading — the runtime will not expose it. Validator `scripts/tests/test_orchestrator_tool_grants.py` flags this.
2. **No nested dispatch in the body.** Worker prompts MUST NOT instruct the worker to "dispatch agent X" — that instruction will be silently ignored, producing inline work. If multi-step coordination is needed, return to the T0 orchestrator with a structured contract so T0 can dispatch the next wave.
3. **Skills-only for in-session workflows.** Workers MAY invoke skills via `Skill()` for inline workflow steps, but skill invocations do not create a new session — they run inline in the worker's own context. Parallel `Skill()` calls in one worker message are serialized by the runtime (empirically verified 2026-04-24); design for serial execution inside workers.
4. **One focused responsibility per worker.** Because workers cannot subdivide work further, each worker MUST be scoped to a single-responsibility task. Multi-responsibility work belongs at the T0 orchestrator, which can dispatch multiple focused workers.

**Failure attribution:** The T0 orchestrator is responsible for aggregating worker return contracts, retrying failed workers (within the global retry budget — see Rule 5), and escalating unresolvable failures to the user. Workers propagate structured failure details (specific step, error, retry count) but do NOT decide whether to retry.

## 4. Externalize DAGs to Config

Pipeline stage definitions, dependency graphs, and execution order MUST be defined in a config file (YAML/JSON in `config/`), not inline in agent or skill bodies. Inline DAGs cannot be modified without editing the pattern, violating separation of concerns. The orchestrator reads the config at runtime.

Two config files define orchestration topology:
- `config/pipeline-stages.yaml` — 11-stage pipeline DAG (read by `project-manager-agent`)
- `config/workflow-contracts.yaml` — Per-workflow step DAGs (read by workflow-master agents)

## 5. Global Retry Budget

An orchestrator MUST enforce a global retry budget across all stages — default maximum **15 total retries** per pipeline run. Individual stage retry limits (default: 3 per stage) still apply, but the global budget prevents a pipeline with many stages from accumulating unbounded retries. When the global budget is exhausted, the orchestrator MUST escalate to the user.

## 6. Single State Location Per Orchestration Scope

Each orchestration scope MUST have exactly one canonical state file:

| Scope | State File | Owner |
|-------|-----------|-------|
| Full pipeline | `.pipeline/state.json` | T0 pipeline orchestrator |
| Per workflow | `.workflows/{workflow-id}/state.json` | T0 workflow orchestrator |
| Per worker | Embedded in parent state OR per-worker sub-file written by the worker and read by the T0 orchestrator | Worker (writes) + T0 orchestrator (reads, aggregates) |

**Ownership rules:**
- A state file is owned by exactly ONE agent — the agent named in `master_agent` field of the workflow contract
- The T0 orchestrator reads worker return contracts + worker-owned sub-files to aggregate state
- Workers MUST NOT read or write the T0 orchestrator's state file directly; they communicate results via their return contract
- Cross-workflow coordination flows through the T0 orchestrator (legacy "parent-child" language assumed nested orchestration that the platform does not support — see §2)

Every state mutation MUST be written to the state file before the next action. This ensures resume, rollback, and observability all read from one source of truth per scope.

## 7. Executable Skill() Invocations in Stage Docs

Every `docs/stages/STAGE-*.md` document that references skills MUST include concrete `Skill()` or `Agent()` invocation examples showing how the orchestrator dispatches that stage. Audit-only prose without executable invocations is insufficient — the orchestrator agent reads these docs and needs actionable dispatch instructions.

## 8. Max 3–4 Responsibilities Per Orchestrator

An orchestrator agent MUST NOT own more than 4 top-level responsibilities. If an orchestrator handles DAG computation, agent dispatch, gate validation, state management, retry logic, observability, AND reporting, it is overloaded. Extract separable concerns (e.g., observability, reporting) into dedicated skills the orchestrator invokes.

## 9. Workflow Contracts as Source of Truth

Every workflow-master agent MUST read its step definitions, artifact contracts, and orchestration rules from `config/workflow-contracts.yaml` at runtime. MUST NOT hardcode skill chains, artifact paths, or step ordering in agent bodies.

The contract config defines:
- **Step DAGs** with `depends_on` for dependency-ordered execution
- **Artifact contracts** (`artifacts_in`/`artifacts_out`) for typed handoffs between steps
- **Gate expressions** for machine-readable pass/fail evaluation
- **Skip conditions** for conditional step execution
- **Sub-orchestrator declarations** for auditable nesting

Changes to workflow behavior MUST be made in the config file, not in agent bodies. Agent bodies contain orchestration *protocol* (how to execute); config contains orchestration *topology* (what to execute in what order).

## 10. Dual-Mode Operation

An agent's file MAY describe two operational modes. Because of the single-dispatch-level constraint (§2), mode semantics differ from the legacy "standalone vs dispatched master" model:

| Mode | When | Available tools | Constraints |
|------|------|-----------------|-------------|
| **T0 orchestrator** | User invokes directly OR a skill injects the agent's logic into T0 | Full tool set including `Agent` | MAY dispatch workers via `Agent()`; owns full lifecycle (init → dispatch → aggregate → commit → report) |
| **Worker** | Dispatched as a subagent via `Agent()` from the T0 orchestrator | Full tool set EXCEPT `Agent` | MUST NOT attempt further subagent dispatch — `Agent` is absent at runtime per §2. MUST return a structured contract (`gate`, `artifacts`, `decisions`, `blockers`, `summary`) to the T0 orchestrator. Skip steps marked `skip_when: "mode == 'worker'"` — typically commit/PR steps and anything requiring further dispatch. |

**Dual-mode viability:** An agent whose design requires dispatching workers can only run in T0 mode. If such an agent is dispatched as a worker, the `Agent` tool is absent and every dispatch instruction in its body is silently ignored — producing inline serial work instead of the intended parallelism (the exact failure mode observed in the 2026-04-24 testbed). Agents that support both modes MUST be designed so the worker-mode code path does not assume `Agent` is available.

In T0 mode, the agent IS the orchestrator and handles all lifecycle concerns including state creation, cleanup, worker dispatch, and final reporting.

## 11. Mandatory Context Passing

When a workflow-master dispatches a step, it MUST pass upstream context — not just the step's direct `artifacts_in`. The dispatch context includes:

1. **Artifact paths** from all completed upstream steps (not just direct dependencies)
2. **One-line summaries** of each completed step's outcome
3. **Key decisions** made during the workflow so far
4. **Original user input** that initiated the workflow

This ensures no skill starts from scratch. The context is the connective tissue that makes skills work as a team instead of isolated tools.

Context MUST be structured (JSON or structured prompt sections), not freeform prose. Freeform context degrades across multiple handoffs.
