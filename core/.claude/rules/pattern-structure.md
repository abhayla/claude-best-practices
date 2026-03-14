---
description: Structural requirements for skills, agents, and rules in .claude/. Enforces frontmatter, versioning, type classification, and scope.
globs: [".claude/**/*.md"]
---

# Pattern Structure Standards

## Skill Structure

Every skill in `.claude/skills/*/SKILL.md` MUST have:

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

Every agent in `.claude/agents/*.md` MUST have:

```yaml
---
name: agent-name
description: When and why to use this agent.
model: inherit                   # inherit | sonnet | haiku | opus
---
```

Plus `## Core Responsibilities` and `## Output Format` sections in the body.

## Rule Structure

Every rule in `.claude/rules/*.md` MUST have either:

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

Maintain deprecated patterns for 2 version cycles before removal. Deprecated patterns MUST be surfaced prominently in documentation dashboards.
