---
description: Guidelines for curating patterns (skills, agents, rules) added to the distributed .claude/ template.
globs: [".claude/**/*.md"]
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

## Hub-only vs Distributable Scoping (+ dual-home sync)

For EVERY new resource (skill / agent / rule / hook), decide its home BEFORE building: does it operate **the hub itself** (→ hub-only `.claude/`) or is it generically useful to **any project** (→ distributable `core/.claude/` + registry)? **Default to distributable** — the hub's mission is to distribute, and `core/` patterns are opt-in (provisioned, never auto-active). Build/dogfood in the hub first, then promote once proven (genericizing hub-specific deps). Promotion is bidirectional (hub→core when proven generic; core→hub when the hub must use it operationally).

A resource that lives in BOTH trees (dual-home) MUST be classified in `config/dual-home-resources.yml` as `synced` (must stay identical), `shared` (shared skeleton identical; hub/downstream-specific lines fenced `DUAL-SYNC:HUB-ONLY`/`DOWNSTREAM-ONLY` so they cannot intermingle), or `divergent` (documented variant). The CI gate (`scripts/tests/test_dual_home_sync.py`) blocks drift + unclassified resources. Full doctrine: `docs/HUB-CORE-SYNC.md`.
