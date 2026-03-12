---
description: Guidelines for curating rules added to the distributed core/.claude/ template.
globs: ["core/.claude/**/*.md"]
---

# Rule & Skill Curation for Distributed Template

## Reactive, Not Speculative

MUST NOT add rules to `core/.claude/` based on speculation or theoretical best practices. Every rule MUST originate from a real correction, observed failure, or documented community pattern with evidence.

Before adding a new rule, ask: "Has this actually caused a problem, or am I guessing it might?" If guessing — don't add it.

## Evidence Required

When proposing a new rule for `core/.claude/`, provide:
1. **Source** — Where the rule came from (user correction, community thread, research paper)
2. **Problem it solves** — What goes wrong without this rule
3. **Proof it's not already covered** — Check purpose overlap with existing rules, not just text similarity

## Skill Curation

### Gap Analysis Before Adding

Before proposing a new skill for `core/.claude/skills/`, MUST compare its unique parts against ALL existing skills. Identify what is genuinely new vs. what already exists elsewhere. Recommend either creating a new skill OR enhancing existing ones — never both for the same concept.

### Self-Contained Skills

Each skill MUST be self-contained with all required details to execute its workflow. MUST NOT spread related concepts across multiple skills. A skill MUST have everything it needs without depending on enhancements scattered elsewhere. If a concept belongs to a skill's workflow, put it IN that skill — not as a patch to another skill.
