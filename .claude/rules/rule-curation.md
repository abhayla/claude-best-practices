---
description: Guidelines for curating rules added to the distributed core/.claude/ template.
globs: ["core/.claude/**/*.md"]
---

# Rule Curation for Distributed Template

## Reactive, Not Speculative

MUST NOT add rules to `core/.claude/` based on speculation or theoretical best practices. Every rule MUST originate from a real correction, observed failure, or documented community pattern with evidence.

Before adding a new rule, ask: "Has this actually caused a problem, or am I guessing it might?" If guessing — don't add it.

## Evidence Required

When proposing a new rule for `core/.claude/`, provide:
1. **Source** — Where the rule came from (user correction, community thread, research paper)
2. **Problem it solves** — What goes wrong without this rule
3. **Proof it's not already covered** — Check purpose overlap with existing rules, not just text similarity
