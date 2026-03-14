---
description: Guidelines for curating all patterns (skills, agents, rules) added to the distributed core/.claude/ template.
globs: ["core/.claude/**/*.md"]
---

# Pattern Curation for Distributed Template

## Reactive, Not Speculative

MUST NOT add patterns to `core/.claude/` based on speculation or theoretical best practices. Every pattern MUST originate from a real correction, observed failure, or documented community pattern with evidence.

Before adding, ask: "Has this actually caused a problem, or am I guessing it might?" If guessing — don't add it.

## Evidence Required

When proposing a new pattern for `core/.claude/`, provide:
1. **Source** — Where it came from (user correction, community thread, research paper)
2. **Problem it solves** — What goes wrong without it
3. **Proof it's not already covered** — Check purpose overlap with existing patterns, not just text similarity

## Quality Gates

All new patterns MUST pass these checks before merging. See the companion rules for full details:
- **Portability** (`pattern-portability.md`) — No hardcoded paths, no project-specific references, least-privilege tools
- **Structure** (`pattern-structure.md`) — Required frontmatter with `version`, `type`, scope declaration, SemVer policy
- **Self-containment** (`pattern-self-containment.md`) — Complete content, no placeholders, size limits, cross-reference integrity

## Skill Curation

### Gap Analysis Before Adding

Before proposing a new skill for `core/.claude/skills/`, MUST compare its unique parts against ALL existing skills. Identify what is genuinely new vs. what already exists elsewhere. Recommend either creating a new skill OR enhancing existing ones — never both for the same concept.

### Self-Contained Skills

Each skill MUST be self-contained with all required details to execute its workflow. MUST NOT spread related concepts across multiple skills. A skill MUST have everything it needs without depending on enhancements scattered elsewhere. If a concept belongs to a skill's workflow, put it IN that skill — not as a patch to another skill.

### Skill Type Declaration

Every skill MUST declare `type: workflow` or `type: reference` in frontmatter. Workflow skills require numbered steps. Reference skills require organized sections but no step numbering.

## Agent Curation

Agents MUST declare `model` in frontmatter and include `## Core Responsibilities` and `## Output Format` sections. Agent descriptions must explain WHEN to use the agent, not just WHAT it does.

## Rule Curation

Every rule MUST declare its activation scope — either `globs:` in frontmatter or `# Scope: global` in the first 5 lines. Unscoped rules cause context pollution in projects where they don't apply.
