---
description: >
  Auto-enhance every user prompt with project-specific context before acting.
  Prefix every response with a brief *Enhanced: ...* indicator.
globs: ["**/*"]
---
# Scope: global

# Prompt Auto-Enhance

Every response MUST start with `*Enhanced: <what was checked>*` (under 15 words).
Examples: *Enhanced: git state, 3 rules, scanned skills/* | *Enhanced: git state, registry check, read 2 source files*

## Tier 1 — Always (every prompt)

1. **Existing `.claude/` patterns** — Know what exists. MUST NOT duplicate or contradict.
2. **CLAUDE.md** — Already loaded. Reference it, do not re-read unless modified.
3. **Git state** — Current branch, recent commits, uncommitted changes.

## Tier 2 — Conditional (only when prompt references specific files/features/patterns)

4. **Nearby files** — Read surrounding files for structural context.
5. **`registry/patterns.json`** — Check before suggesting new patterns.

Skip Tier 2 if Tier 1 suffices. MUST NOT read more than necessary.

## Resource CRUD Detection

If the prompt implies CREATING, UPDATING, or DELETING a Claude Code resource
(skill, agent, rule, hook), switch to **visible mode** and follow the batch
approval flow in `/prompt-auto-enhance`. Otherwise stay silent (indicator only).

## CRITICAL RULES

- NEVER skip the `*Enhanced: ...*` indicator — it is MANDATORY on every response
- NEVER skip Tier 1 context gathering
- NEVER create, update, or delete any resource without user approval
- NEVER web search when local context suffices — see `/prompt-auto-enhance` for the decision tree
- Resource CRUD MUST follow `pattern-structure.md`, `pattern-portability.md`, `pattern-self-containment.md`
