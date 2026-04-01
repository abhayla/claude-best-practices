# Agent Quality Checklist

## Frontmatter Contract

| Field | Required | Validation |
|-------|----------|------------|
| `name` | MUST | Kebab-case, matches filename (without `.md`) |
| `description` | MUST | MUST explain WHEN to use, not just WHAT it does |
| `model` | MUST | One of: `inherit`, `sonnet`, `haiku`, `opus` |
| `color` | MUST | One of: `red`, `orange`, `yellow`, `blue`, `green` |

## Color Field (Severity/Importance)

| Color | Severity | Use When |
|-------|----------|----------|
| `red` | Critical | Security gates, quality blockers, breaking-change detection |
| `orange` | High | Failure diagnosis, build repair, debugging |
| `yellow` | Medium | Code review, context management, session lifecycle |
| `blue` | Standard | Test execution, verification, learning, general workflows |
| `green` | Low | Documentation, research, planning, information gathering |

## Body Structure

- MUST have `## Core Responsibilities` section
- MUST have `## Output Format` section
- Description MUST include a "use when" clause
- Opening persona line MUST specify domain expertise, failure modes watched for, and mental model

## Proactive Spawning

Agents that should spawn automatically MUST include "Use proactively" in description:
- Quality/security checks → proactive
- Failure catching → proactive
- Context/session lifecycle → proactive
- Workflow orchestration → reactive (no proactive language)
- Explicit user intent required → reactive

## Orchestration Constraints

Multi-stage coordination MUST be an agent, not a skill. 4-tier model:

| Tier | Role | Can Dispatch |
|------|------|-------------|
| T0 | Pipeline orchestrator | T1 via `Agent()` |
| T1 | Workflow master | T2 via `Agent()` + `Skill()` |
| T2 | Sub-orchestrator | T3 via `Agent()` + `Skill()` |
| T3 | Worker agent | `Skill()` ONLY — no `Agent()` |

Max depth: 4 tiers. T3 MUST NOT call `Agent()`.
Each tier MUST report completion to parent via structured return contract.
Max 3-4 responsibilities per orchestrator.
