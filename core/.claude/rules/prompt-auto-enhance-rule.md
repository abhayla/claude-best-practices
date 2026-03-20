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

## Clarification Gate — Ask Before Acting

Before starting any implementation, clarify requirements by asking questions one at a time.

### When to Trigger

- The prompt is vague, broad, or could be interpreted multiple ways
- Key decisions (scope, approach, affected files) cannot be resolved by reading the codebase
- The task would touch more than 3 files and the user hasn't specified the approach

### When to Skip

- The prompt is a direct, unambiguous instruction (e.g., "rename X to Y", "run tests", "fix the typo on line 42")
- The answer is fully resolvable from codebase context gathered in Tier 1/2
- The prompt is a question (just answer it)

### How to Ask

- State how many questions remain (e.g., "Question 3 of ~6")
- For each question, provide your recommendation with reasoning (cite codebase patterns, standards, or docs you read)
- Before each question, read relevant files/docs to ground your recommendation in what actually exists — MUST NOT ask things you can answer by reading code
- Target 3-5 questions max. Stop as soon as you have enough confidence to act.

### After Clarification — Present Plan Section by Section

- Present the plan **section by section** for review (not all at once)
- For each section, wait for approval or feedback before showing the next
- Only begin implementation after all sections are approved

### What NOT to Do

- MUST NOT ask generic questions you could resolve by reading the codebase (e.g., "What tech stack do you use?" — read CLAUDE.md)
- MUST NOT ask the user to confirm things that have obvious best-practice answers — state your recommendation and move on unless the user disagrees
- MUST NOT present the entire plan in one shot expecting blanket approval

## Resource CRUD Detection

If the prompt implies CREATING, UPDATING, or DELETING a Claude Code resource
(skill, agent, rule, hook), switch to **visible mode** and follow the batch
approval flow in `/prompt-auto-enhance`. Otherwise stay silent (indicator only).

## CRITICAL RULES

- NEVER skip the `*Enhanced: ...*` indicator — it is MANDATORY on every response
- NEVER skip Tier 1 context gathering
- NEVER skip the Clarification Gate for ambiguous prompts — ask before acting
- NEVER ask questions answerable by reading the codebase — read first, then ask
- NEVER create, update, or delete any resource without user approval
- NEVER web search when local context suffices — see `/prompt-auto-enhance` for the decision tree
- Resource CRUD MUST follow `pattern-structure.md`, `pattern-portability.md`, `pattern-self-containment.md`
