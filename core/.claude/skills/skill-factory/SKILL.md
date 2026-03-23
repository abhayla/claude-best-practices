---
name: skill-factory
description: >
  Detect repeated workflows in session logs and classify them into the right
  automation type (skill, agent, hook, MCP server, or rule). Use when you notice
  recurring manual steps that should be automated. Modes: scan, propose, create, list.
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "<mode: scan|propose|create|list> [details]"
type: workflow
version: "3.0.0"
---

# Skill Factory — Pattern Detector & Automation Classifier

Detect repeated workflows and classify them into the right automation type.

**Arguments:** $ARGUMENTS

---

## Modes

| Mode | Description |
|------|-------------|
| `scan` | Analyze recent session work for repeated multi-step patterns |
| `propose` | Suggest new skills based on detected patterns |
| `create <name>` | Create a new skill from a description or detected pattern |
| `list` | Show all existing skills with descriptions |

---

## STEP 1: Mode Detection

Parse `$ARGUMENTS` to determine mode.

## Scan Mode

1. Read recent git history for repeated command patterns
2. Scan `.claude/` session logs if available (`~/.claude/projects/` JSONL files)
3. Look for multi-step sequences that appear 3+ times
4. Look for recurring tool-event responses (candidates for hooks)
5. Look for external service interactions (candidates for MCP servers)
6. Look for static corrections repeated across sessions (candidates for rules)

Report:
```
Detected Patterns ([N] total):

| # | Pattern | Frequency | Signals | Likely Category |
|---|---------|-----------|---------|-----------------|
| 1 | [name] | N times | [what was observed] | Skill/Agent/Hook/MCP/Rule |
| 2 | ... | | | |
```

## Propose Mode

Classify each detected pattern into exactly one of these 5 categories:

| Category | Location | When to Use | Examples |
|----------|----------|-------------|---------|
| **Skill** (`.claude/skills/`) | Multi-step workflow triggered by user command. Has clear start/end, requires judgment, runs in conversation context. | `/fix-issue`, `/implement`, `/tdd`, test-debug-fix cycles |
| **Agent** (`.claude/agents/`) | Autonomous sub-task that runs in isolation with own tool access. Delegatable work without continuous user interaction. | Code reviewer, test runner, build validator, dependency auditor |
| **Hook** (`.claude/hooks/`) | Automatic trigger on tool events (PreToolUse/PostToolUse). Enforcement gates, auto-formatting, validation. No user invocation. | Auto-format on save, block commits without tests, screenshot resize |
| **MCP Server** (`.mcp.json`) | External tool integration via Model Context Protocol. Bridges to third-party services or local tools that need a persistent server. | Database queries, browser automation, Slack notifications, CI status |
| **Rule** (`.claude/rules/`) | Static constraint or convention that should always be in context when matching files are edited. No logic — just knowledge. | Naming conventions, architecture decisions, anti-patterns to avoid |

### Classification Decision Tree

For each detected pattern, ask in order:

1. **Is it a static constraint with no steps?** → **Rule** (scoped via `globs:`)
2. **Must it run automatically on every tool call with zero exceptions?** → **Hook** (deterministic, no user invocation)
3. **Does it need a persistent connection to an external service?** → **MCP Server** (database, browser, API bridge)
4. **Can it run autonomously without user interaction?** → **Agent** (delegatable, isolated context)
5. **Does it need user judgment during execution?** → **Skill** (interactive, multi-step)

If a pattern spans multiple categories (e.g., "could be a skill OR an agent"), explain the trade-off and recommend one.

### Conflict Check

Before proposing a new resource:
1. Search `.claude/skills/`, `.claude/agents/`, `.claude/hooks/`, `.claude/rules/` for existing coverage
2. If an existing resource partially covers the pattern, recommend **enhancing** it instead of creating a new one
3. Flag any patterns where the category is ambiguous

### Output Format

```
Proposed Automations ([N] detected):

| # | Pattern | Category | Name | Trigger | Steps/Scope | Effort |
|---|---------|----------|------|---------|-------------|--------|
| 1 | Test-fix loop | Skill | /fix-loop | User runs after test failure | 5-step iterative cycle | Medium |
| 2 | Auto-format on save | Hook | auto-format.sh | PostToolUse (Write/Edit) | Run black + ruff | Low |
| 3 | Code review delegation | Agent | code-reviewer | PR opened or /review | Analyze diff, report issues | Medium |
| 4 | DB query tool | MCP Server | db-query | Tool call from conversation | Expose query execution | High |
| 5 | Endpoint naming rule | Rule | backend-endpoint-naming | When editing api/**/*.py | Naming constraints | Low |

Category mix: [N] skills, [N] agents, [N] hooks, [N] MCP servers, [N] rules

Conflicts with existing:
  - [name]: partially covered by existing [resource] — recommend enhancing instead
```

## Create Mode

Create the resource using the appropriate authoring tool for its category:

| Category | Authoring Tool | Output Location |
|----------|---------------|-----------------|
| **Skill** | Delegate to `/writing-skills` | `.claude/skills/{name}/SKILL.md` |
| **Agent** | Apply `pattern-structure.md` Agent Template | `.claude/agents/{name}.md` |
| **Rule** | Delegate to `/claude-guardian` | `.claude/rules/{name}.md` |
| **Hook** | Write shell script manually | `.claude/hooks/{name}.sh` |
| **MCP Server** | Add entry to `.mcp.json` | `.mcp.json` config + server code |

### Skill Creation

Delegate to `/writing-skills` which handles templates, quality checklists, and trigger overlap scans.

### Agent Creation

Write directly using this structure:

```markdown
---
name: {name}
description: When and why to use this agent.
model: inherit
---

## Core Responsibilities

1. {Primary responsibility}
2. {Secondary responsibility}

## Output Format

{What the agent returns and in what structure.}
```

### Rule Creation

Delegate to `/claude-guardian` which handles scope declaration, placement, and format validation.

### Hook Creation

Write a shell script with appropriate event triggers:

```bash
#!/bin/bash
# Hook: {name}
# Event: PreToolUse | PostToolUse
# Description: {what it enforces}

# Read tool input from stdin
INPUT=$(cat)
TOOL_NAME=$(echo "$INPUT" | jq -r '.tool_name // empty')

# Hook logic here
```

Register in `.claude/settings.json` under the appropriate event matcher.

### MCP Server Creation

Add to `.mcp.json`:
```json
{
  "mcpServers": {
    "{name}": {
      "command": "{command}",
      "args": ["{args}"]
    }
  }
}
```

## List Mode

List all existing automations across all 5 categories:

1. **Skills**: Scan `.claude/skills/*/SKILL.md` — show name and description
2. **Agents**: Scan `.claude/agents/*.md` — show name and description
3. **Hooks**: Scan `.claude/hooks/*.sh` — show name and event trigger
4. **MCP Servers**: Read `.mcp.json` — show server names and commands
5. **Rules**: Scan `.claude/rules/*.md` — show name and globs scope

Output as a grouped table:
```
Existing Automations:

Skills ([N]):
  /fix-loop — Iterative test-fix cycle with escalation
  /implement — Feature implementation with TDD workflow
  ...

Agents ([N]):
  code-reviewer — Comprehensive code quality assessment
  ...

Hooks ([N]):
  auto-format.sh — PostToolUse: Run formatters after edits
  ...

MCP Servers ([N]):
  playwright — Browser automation for screenshots
  ...

Rules ([N]):
  workflow.md — [global] Development workflow guidelines
  backend-endpoint-structure.md — [backend/app/api/**] Endpoint conventions
  ...

Total: [N] automations
```

## CRITICAL RULES

- NEVER propose a new resource without checking all 5 categories for existing coverage first
- NEVER default to "skill" — use the classification decision tree to pick the right category
- NEVER create hooks for advisory guidance — hooks are for deterministic enforcement only
- NEVER create MCP servers when a simple Bash command suffices — MCP is for persistent service connections
- NEVER create rules for multi-step procedures — rules are static constraints, use skills for workflows
