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
tools: ["Agent", "Bash", "Read", "Write", "Edit", "Grep", "Glob", "Skill"]   # see Tool Grants below
dispatched_from: T0 | worker | dual-mode  # see Dispatch Context below — defaults to "worker" if absent
model: inherit                   # inherit | sonnet | haiku | opus
color: blue                      # red | orange | yellow | blue | green
---
```

### Dispatch Context (`dispatched_from:`)

Declares the runtime context this agent is designed to run in. Used by the
validator (`scripts/tests/test_orchestrator_tool_grants.py`) to check
whether `Agent` in `tools:` is appropriate for this agent's dispatch
context — see Tool Grants below for the full invariant.

| Value | Meaning | `Agent` in `tools:`? |
|---|---|---|
| `T0` | Agent is invoked directly by the user (never dispatched by another agent/skill) | MUST include `Agent` |
| `worker` | Agent is only ever dispatched by a T0 orchestrator | MUST NOT include `Agent` — hub convention keeps workers flat |
| `dual-mode` | Agent supports both modes; worker-mode code path MUST NOT depend on `Agent` | MAY include `Agent`; validator emits a body-scan warning |

If the field is absent, the validator defaults to `worker` (the safer choice).
Agents marked `deprecated: true` are skipped by the context-aware invariant
check (they're on the deprecation lifecycle and will be removed).

`tools:` MUST be a YAML list (`["A", "B", ...]`). A space-separated
scalar (`"Agent Bash Read ..."`) parses as a single string and Claude Code
will NOT expose the agent as a `subagent_type` — verified in the downstream
test run 2026-04-24, where 6 pipeline agents with the scalar form were
silently inlined at their dispatch site instead of being dispatched as subagents.

### Tool Grants (Single-Level Convention)

> **Single-level dispatch is a deliberate hub convention, not a platform limit.** Nested subagent
> dispatch is GA (Claude Code v2.1.172, ≤5 levels). The "workers don't declare `Agent`" invariant below
> is a KISS/YAGNI **convention** the hub keeps by choice (nesting adopted only per concrete need) — see
> the convention note in `agent-orchestration.md` and the guard rails in
> `plans/skill-at-t0-doctrine-relaxation.md`. `test_orchestrator_tool_grants.py` pins it.

The hub keeps subagent dispatch single-level by convention: hub workers don't declare `Agent`, so they
don't orchestrate further. The runtime would actually expose `Agent` to a worker below the 5-level cap —
keeping workers flat is a hub *choice* that makes dispatch predictable, not a platform restriction.
(History: the convention predates the GA, when Claude Code did NOT forward `Agent` to dispatched
subagents and [the docs](https://code.claude.com/docs/en/sub-agents) stated *"subagents cannot spawn
other subagents"* — verified 2026-04-24, [GH #19077](https://github.com/anthropics/claude-code/issues/19077),
[GH #4182](https://github.com/anthropics/claude-code/issues/4182), three runtime probes; superseded by
v2.1.172. See `agent-orchestration.md` for the full convention note.)

**What this means for `tools:` frontmatter:**

| Dispatch context | `Agent` in `tools:` | Convention |
|---|---|---|
| **T0 (user's session directly)** | Allowed, functional | `Agent()` dispatches workers as declared |
| **Dispatched as a worker** (via `Agent(subagent_type=...)` from any caller) | **By convention — do NOT declare** | Hub workers stay flat; they don't orchestrate further. (The runtime would honor `Agent` below the 5-level cap, but hub patterns deliberately don't nest from workers.) |

**Invariant (single-level convention; assertions pinned by the validator):**

| Agent role | `Agent` in `tools:`? | Rationale |
|---|---|---|
| **T0 orchestrator** (user invokes directly; never dispatched) | **Yes** — required for worker dispatch | Runs in user's session where `Agent` is available |
| **Dual-mode agent** (supports both T0 and worker modes — see `agent-orchestration.md` §10) | **Yes, for T0 mode only.** Worker-mode code path MUST NOT depend on `Agent` | When dispatched as a worker the agent stays flat by convention; and at the depth-5 cap `Agent` is genuinely absent — so a worker-mode path that assumes `Agent` would silently inline |
| **Worker** (only ever dispatched as a subagent) | **No** — flat by convention; declaring it would invite nesting the hub avoids | See worker constraints in `agent-orchestration.md` §3 |

**Standard T0-orchestrator tool set:**
`["Agent", "Bash", "Read", "Write", "Edit", "Grep", "Glob", "Skill"]`.

**Standard worker tool set:** same minus `Agent`. Workers MAY further narrow
the set (e.g., omit `Write`/`Edit` if read-only).

Validator pinning: `scripts/tests/test_orchestrator_tool_grants.py` asserts
this convention, keyed off the `dispatched_from:` frontmatter field (above) so
it decides context-aware whether `Agent` is required (T0 orchestrators) or
omitted (workers). The validator pins the hub convention; it does not probe
runtime nesting depth (the platform allows nesting ≤5 — the hub simply chooses
not to use it from workers).

### Agent registry session-pinning (Claude Code platform behavior)

Claude Code loads the agent registry at **session start** by scanning
`.claude/agents/*.md`, not on-demand at each `Agent()` call. Files added,
modified, or removed mid-session are NOT reflected in the runtime registry
until the next session is started.

**Implications for skill authors:**

- Skills that sync new agent files (e.g., `/update-practices`) MUST warn
  users that a session restart is required to dispatch the new agents.
  See `/update-practices` STEP 5.5 RESTART REQUIRED banner pattern.
- Skills that dispatch agents by name (e.g., `/test-pipeline` STEP 2)
  SHOULD probe the runtime registry early (STEP 1 sub-step) and BLOCK
  with `WORKER_REGISTRY_NOT_LOADED` if any required agent is missing.
  File-existence checks (`[ -f .claude/agents/<name>.md ]`) are NOT
  sufficient — they can pass while runtime dispatch fails.
- Updates to existing agent files (frontmatter changes, body edits)
  generally do NOT require restart — only NEW agent files do.
- The validator in `scripts/tests/test_orchestrator_tool_grants.py`
  enforces frontmatter invariants but does NOT validate runtime
  dispatchability. Runtime dispatchability is the responsibility of the
  invoking skill via early probe.

This finding was surfaced 2026-04-25 during FIREKaro-Vue downstream
validation when `/update-practices` synced 5 worker agents and the same
session's `/test-pipeline` call failed at SCOUT dispatch with
"Agent type 'test-scout-agent' not found" despite the file being on
disk and committed.

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
