# Scope: global

# Prompt Auto-Enhance

Every response MUST start with `*Enhanced: <what was checked>*` (under 15 words).
Examples: *Enhanced: prompt graded (B, 2 fixes), git state, 3 rules*

## Tier 1 — Always (every prompt)

1. Existing `.claude/` patterns — know what exists, MUST NOT duplicate
2. CLAUDE.md — already loaded, reference it
3. Git state — branch, recent commits, uncommitted changes

## Tier 2 — Conditional (only when prompt references specific files/features)

4. Nearby files — structural context
5. `registry/patterns.json` — check before suggesting new patterns

## Prompt Grading & Strengthening

For **non-trivial prompts** (ambiguous, multi-file, or multi-step):
run the Grade → Diagnose → Fix pipeline from `/prompt-auto-enhance`.
Skip for direct instructions, single-file changes, and pure knowledge questions.

## Clarification Gate — Ask Before Acting

Trigger when: prompt is vague/broad, key decisions unresolvable from code, or task touches 3+ files without specified approach.
Skip when: direct unambiguous instruction, answer resolvable from Tier 1/2, pure knowledge question, or strengthening already resolved the ambiguity.
How: one question at a time with count ("Question 2 of ~4") and recommendation. Read code before asking — MUST NOT ask what you can answer yourself. 3-5 questions max. Present plan section by section.

## Resource CRUD Detection

If prompt implies creating/updating/deleting a Claude Code resource,
follow the batch approval flow in `/prompt-auto-enhance`.

## CRITICAL RULES

- NEVER skip the `*Enhanced:*` indicator
- NEVER skip Tier 1 context gathering
- NEVER skip the Clarification Gate for ambiguous prompts
- NEVER create/update/delete resources without batch approval
- NEVER ask questions answerable by reading the codebase
