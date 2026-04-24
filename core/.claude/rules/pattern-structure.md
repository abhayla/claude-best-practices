---
description: Structural requirements for skills, agents, and rules. Enforces frontmatter, versioning, type classification, and scope.
globs: [".claude/**/*.md"]
---

# Pattern Structure Standards

## Skill Structure

Every skill in `core/.claude/skills/*/SKILL.md` MUST have:

### Required Frontmatter Fields

```yaml
---
name: kebab-case-name          # MUST match directory name
description: >                  # 1-3 sentences, start with a verb
  What it does, when to use it.
type: workflow                   # workflow | reference
allowed-tools: "Read Grep Glob" # Space-separated, minimal set
argument-hint: "<required> [optional]"
version: "1.0.0"                # SemVer format
---
```

### Type Classification

| Type | Structure Required | Use When |
|---|---|---|
| `workflow` | MUST have numbered `## STEP N:` sections | Skill is a multi-step procedure |
| `reference` | MUST have organized `##` sections (no step numbering required) | Skill is a knowledge base or lookup guide |

### Workflow Skills Additional Requirements

- Numbered `## STEP N:` sections with verb-phrase titles
- `## CRITICAL RULES` or `## MUST DO` / `## MUST NOT DO` section at the end
- Critical constraints placed at the TOP (in frontmatter description or preamble) AND at the BOTTOM (`CRITICAL RULES` section) for primacy + recency reinforcement

## Agent Structure

Every agent in `core/.claude/agents/*.md` MUST have:

```yaml
---
name: agent-name
description: When and why to use this agent.
tools: ["Agent", "Bash", "Read", "Write", "Edit", "Grep", "Glob", "Skill"]   # required for orchestrators — see Tool Grants below
model: inherit                   # inherit | sonnet | haiku | opus
color: blue                      # red | orange | yellow | blue | green
---
```

`tools:` MUST be a YAML list (`["A", "B", ...]`). A space-separated
scalar (`"Agent Bash Read ..."`) parses as a single string and Claude Code
will NOT expose the agent as a `subagent_type` — verified in the downstream
test run 2026-04-24, where 6 pipeline agents with the scalar form were
silently inlined at their dispatch site instead of being dispatched as subagents.

### Tool Grants (Platform-Constrained)

Claude Code does NOT forward the `Agent` tool to dispatched subagents,
regardless of what the subagent's frontmatter `tools:` field declares.
[Anthropic's official docs](https://code.claude.com/docs/en/sub-agents)
state this explicitly: *"subagents cannot spawn other subagents."*
Corroborated by [GH #19077](https://github.com/anthropics/claude-code/issues/19077),
[GH #4182](https://github.com/anthropics/claude-code/issues/4182), and three
independent 2026-04-24 runtime probes. See `agent-orchestration.md` §2 for
the full platform-constraint note.

**What this means for `tools:` frontmatter:**

| Dispatch context | `Agent` in `tools:` | Runtime behavior |
|---|---|---|
| **T0 (user's session directly)** | Allowed, functional | `Agent()` dispatches workers as declared |
| **Dispatched as a worker** (via `Agent(subagent_type=...)` from any caller) | **Misleading — do NOT declare** | `Agent` is stripped at runtime; any dispatch instruction in the agent body silently produces inline serial work instead |

**Invariant (revised 2026-04-24 to reflect the platform finding):**

| Agent role | `Agent` in `tools:`? | Rationale |
|---|---|---|
| **T0 orchestrator** (user invokes directly; never dispatched) | **Yes** — required for worker dispatch | Runs in user's session where `Agent` is available |
| **Dual-mode agent** (supports both T0 and worker modes — see `agent-orchestration.md` §10) | **Yes, for T0 mode only.** Worker-mode code path MUST NOT depend on `Agent` | An agent that lists `Agent` in `tools:` but is dispatched as a worker will have `Agent` stripped — dispatch instructions in its body become silent inline work |
| **Worker** (only ever dispatched as a subagent) | **No** — runtime strips it; declaring it is misleading | See worker constraints in `agent-orchestration.md` §3 |

**Standard T0-orchestrator tool set:**
`["Agent", "Bash", "Read", "Write", "Edit", "Grep", "Glob", "Skill"]`.

**Standard worker tool set:** same minus `Agent`. Workers MAY further narrow
the set (e.g., omit `Write`/`Edit` if read-only).

Runtime-verified pinning: `scripts/tests/test_orchestrator_tool_grants.py`
asserts this invariant. A Phase 2 refactor (planned 2026-04-24) will add a
`dispatched_from:` frontmatter field to every agent so the validator can
decide context-aware whether `Agent` is required (T0 orchestrators) or
forbidden (workers), plus a runtime-probe integration test that dispatches a
throwaway subagent and asserts `Agent` is absent from its tool list.

### Color Field (Severity/Importance)

Every agent MUST declare a `color` indicating the severity and importance of its work:

| Color | Severity | Use When | Examples |
|-------|----------|----------|---------|
| `red` | Critical | Security gates, quality blockers, breaking-change detection | `security-auditor-agent`, `code-reviewer-agent` |
| `orange` | High | Failure diagnosis, build repair, debugging | `debugger-agent`, `test-failure-analyzer-agent` |
| `yellow` | Medium | Code review, context management, session lifecycle | `context-reducer-agent`, `android-kotlin-reviewer-agent` |
| `blue` | Standard | Test execution, verification, learning, general workflows | `test-scout-agent`, `tester-agent` |
| `green` | Low | Documentation, research, planning, information gathering | `docs-manager-agent`, `web-research-specialist-agent` |

### Proactive Spawning Declaration

Agents that should be spawned **automatically** (without explicit user request) MUST include "Use proactively" or "Spawn proactively" in their description. This signals to Claude Code that the agent should be dispatched whenever its trigger conditions are met — not only when the user explicitly asks.

An agent is proactive if it:
- Performs quality or security checks (code review, security audit, quality gates)
- Catches problems early (test failure analysis, build failure diagnosis, debugging)
- Manages context or session lifecycle (context reduction, session summarization)
- Improves future work (learning capture, pattern detection)

An agent is reactive (no proactive language) if it:
- Orchestrates multi-step workflows (master agents, pipeline agents)
- Requires explicit user intent (planning, implementing, scaffolding)
- Is stack-specific and only relevant in certain projects

Plus `## Core Responsibilities` and `## Output Format` sections in the body. The agent's opening persona line (e.g., "You are a...") MUST specify domain expertise, common failure modes they watch for, and the mental model or framework they apply (when applicable) — vague personas like "expert in X" produce vague output.

## Rule Structure

Every rule in `core/.claude/rules/*.md` MUST have either:

1. **Scoped rule** — YAML frontmatter with `globs:` targeting specific file patterns:
   ```yaml
   ---
   description: What this rule enforces.
   globs: ["**/*.py", "**/*.ts"]
   ---
   ```

2. **Global rule** — A `# Scope: global` comment in the first 5 lines, indicating it applies to all files.

MUST NOT leave scope undefined — every rule must declare its activation scope.

## SemVer Policy for Patterns

All patterns MUST include `version` in frontmatter, following Semantic Versioning:

| Change Type | Version Bump | Examples |
|---|---|---|
| **MAJOR** | Breaking changes to output format, removed steps, renamed arguments | Changing structured JSON output schema, removing a step that downstream skills depend on |
| **MINOR** | New optional steps, added examples, new tool allowances | Adding a new mode, expanding a decision table |
| **PATCH** | Typo fixes, wording clarifications, formatting | Fixing a code block, rewording a step |

## Deprecation Lifecycle

When replacing a pattern, MUST NOT delete immediately. Add deprecation fields to frontmatter:

```yaml
deprecated: true
deprecated_by: replacement-skill-name
```

Maintain deprecated patterns for 2 version cycles before removal. `generate_docs.py` MUST surface deprecated patterns prominently in the dashboard.
