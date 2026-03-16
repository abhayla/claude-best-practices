---
description: Constraints for multi-agent orchestration patterns in agents and skills.
globs: [".claude/agents/*.md", ".claude/skills/*/SKILL.md"]
---

# Agent Orchestration Constraints

## 1. Orchestrators MUST Be Agents

Multi-stage coordination that dispatches subagents or sequences skills MUST be implemented as an agent (in `.claude/agents/`), not as a skill. Skills are single-purpose workflows; orchestration is a coordination concern. If a skill grows to dispatch 3+ subagents or manage cross-stage state, convert it to an agent with a thin skill wrapper that preserves the slash command.

## 2. Maximum 2 Nesting Levels

Orchestration hierarchies MUST NOT exceed 2 levels: **orchestrator → worker agent**. A worker agent dispatched by an orchestrator MUST NOT spawn its own subagents. If deeper coordination is needed, flatten the hierarchy — the orchestrator dispatches all agents directly and manages sequencing.

## 3. No Subagent-Spawning Subagents

An agent dispatched via `Agent()` from an orchestrator MUST NOT call `Agent()` itself. Subagents that spawn further subagents create unobservable execution trees, exhaust token budgets unpredictably, and make failure attribution impossible. Worker agents may invoke `Skill()` calls (single-purpose, bounded) but not `Agent()`.

## 4. Externalize DAGs to Config

Pipeline stage definitions, dependency graphs, and execution order MUST be defined in a config file (YAML/JSON in `config/`), not inline in agent or skill bodies. Inline DAGs cannot be modified without editing the pattern, violating separation of concerns. The orchestrator reads the config at runtime.

## 5. Global Retry Budget

An orchestrator MUST enforce a global retry budget across all stages — default maximum **15 total retries** per pipeline run. Individual stage retry limits (default: 3 per stage) still apply, but the global budget prevents a pipeline with many stages from accumulating unbounded retries. When the global budget is exhausted, the orchestrator MUST escalate to the user.

## 6. Single State Location

All pipeline state MUST be persisted in a single canonical location (e.g., `.pipeline/state.json`). MUST NOT split state across multiple files, environment variables, or in-memory structures. Every state mutation MUST be written to this file before the next action. This ensures resume, rollback, and observability all read from one source of truth.

## 7. Executable Skill() Invocations in Stage Docs

Every `docs/stages/STAGE-*.md` document that references skills MUST include concrete `Skill()` or `Agent()` invocation examples showing how the orchestrator dispatches that stage. Audit-only prose without executable invocations is insufficient — the orchestrator agent reads these docs and needs actionable dispatch instructions.

## 8. Max 3–4 Responsibilities Per Orchestrator

An orchestrator agent MUST NOT own more than 4 top-level responsibilities. If an orchestrator handles DAG computation, agent dispatch, gate validation, state management, retry logic, observability, AND reporting, it is overloaded. Extract separable concerns (e.g., observability, reporting) into dedicated skills the orchestrator invokes.
