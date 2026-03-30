---
description: Constraints for multi-agent orchestration patterns in agents and skills.
globs: [".claude/agents/*.md", ".claude/skills/*/SKILL.md"]
---

# Agent Orchestration Constraints

## 1. Orchestrators MUST Be Agents

Multi-stage coordination that dispatches subagents or sequences skills MUST be implemented as an agent (in `.claude/agents/`), not as a skill. Skills are single-purpose workflows; orchestration is a coordination concern. If a skill grows to dispatch 3+ subagents or manage cross-stage state, convert it to an agent with a thin skill wrapper that preserves the slash command.

## 2. Tiered Nesting with Visibility

Orchestration hierarchies follow a 4-tier model. Each tier has clear ownership and dispatch rights:

| Tier | Role | Can Dispatch | Example |
|------|------|-------------|---------|
| **T0** | Pipeline orchestrator | T1 workflow-masters via `Agent()` | `project-manager-agent` |
| **T1** | Workflow master | T2 sub-orchestrators via `Agent()` + skills via `Skill()` | `testing-pipeline-master-agent` |
| **T2** | Sub-orchestrator | T3 worker agents via `Agent()` + skills via `Skill()` | `e2e-conductor-agent`, `test-pipeline-agent` |
| **T3** | Worker agent | `Skill()` calls ONLY — no further `Agent()` dispatch | `test-scout-agent`, `tester-agent` |

**Maximum depth: 4 tiers (T0 → T1 → T2 → T3).** T3 agents MUST NOT call `Agent()`. Any deeper nesting indicates a design problem — flatten by moving coordination up a tier.

**Visibility rule:** Every tier MUST report completion status to its parent via a structured return contract (JSON with `gate`, `artifacts`, `summary` fields). A parent MUST NOT proceed until it has read the child's return. No fire-and-forget dispatches within orchestration chains.

## 3. Controlled Nesting — Tier Enforcement

Each agent MUST declare its tier (T0–T3) in its description or operational context. An agent at tier N may dispatch agents at tier N+1, but MUST NOT dispatch agents at its own tier or above. T3 agents MUST NOT call `Agent()` — they are leaf workers that execute via `Skill()` only.

**Why tiers instead of a flat ban:** Workflow-master agents (T1) need to dispatch specialized sub-orchestrators (T2) like `e2e-conductor-agent` which in turn dispatch worker agents (T3). A flat "no subagent-spawning subagents" rule would force all coordination into a single overloaded orchestrator, violating Rule 8 (max 3-4 responsibilities).

**Failure attribution:** Every tier MUST propagate failure details upward — not just "FAILED" but the specific step, error, and retry count. The parent at each tier is responsible for deciding whether to retry, skip, or escalate.

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
| Full pipeline | `.pipeline/state.json` | `project-manager-agent` (T0) |
| Per workflow | `.workflows/{workflow-id}/state.json` | Workflow master-agent (T1) |
| Per sub-orchestrator | Embedded in parent workflow state OR own sub-file | Sub-orchestrator (T2) |

**Ownership rules:**
- A state file is owned by exactly ONE agent — the agent named in `master_agent` field of the workflow contract
- Parent agents MAY read child state files (for progress monitoring) but MUST NOT write to them
- Child agents MUST NOT read or write sibling workflow state files — cross-workflow coordination flows through the parent (T0)

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

## 10. Dual-Mode Operation for Workflow Masters

Every workflow-master agent (T1) MUST support two operational modes:

| Mode | Trigger | Behavior |
|------|---------|----------|
| **Standalone** | User invokes directly (no Pipeline ID in prompt) | Full lifecycle: init → execute → commit → report |
| **Dispatched** | Parent orchestrator invokes (Pipeline ID present) | Worker lifecycle: execute step subset → return contract to parent |

In dispatched mode, skip steps marked `skip_when: "mode == 'dispatched'"` (typically commit/PR steps). Return results using the standard stage return contract (`gate`, `artifacts`, `decisions`, `blockers`, `summary`).

In standalone mode, the workflow-master IS the top-level orchestrator and handles all lifecycle concerns including state creation, cleanup, and final reporting.

## 11. Mandatory Context Passing

When a workflow-master dispatches a step, it MUST pass upstream context — not just the step's direct `artifacts_in`. The dispatch context includes:

1. **Artifact paths** from all completed upstream steps (not just direct dependencies)
2. **One-line summaries** of each completed step's outcome
3. **Key decisions** made during the workflow so far
4. **Original user input** that initiated the workflow

This ensures no skill starts from scratch. The context is the connective tissue that makes skills work as a team instead of isolated tools.

Context MUST be structured (JSON or structured prompt sections), not freeform prose. Freeform context degrades across multiple handoffs.
