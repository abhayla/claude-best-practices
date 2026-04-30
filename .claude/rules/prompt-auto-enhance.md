# Scope: global

# Prompt Auto-Enhance

Every response starts with `*Enhanced: <what was checked>*` (under 15 words).
Examples: *Enhanced: prompt graded (B, 2 fixes), git state, 3 rules*

The hook (`prompt-enhance-reminder.sh`) gates triggering: prompts ≤15 chars
and known continuation phrases skip injection at the deterministic layer,
so the strengthening pipeline only runs on substantive prompts.

## Tier 1 — Always (every prompt that reaches this rule)

1. Existing `.claude/` patterns — know what exists, do not duplicate
2. CLAUDE.md — already loaded, reference it
3. Git state — branch, recent commits, uncommitted changes

## Tier 2 — Conditional (only when prompt references specific files/features)

4. Nearby files — structural context
5. `registry/patterns.json` — check before suggesting new patterns

## Prompt Grading & Strengthening

For non-trivial prompts (anything that reaches this skill — i.e., the hook
did not filter it out), run the Grade → Diagnose → Fix pipeline from
`/prompt-auto-enhance`. Skip strengthening only for Grade A or pure
knowledge questions; the pipeline still produces the step transcript and
final prompt preview in those cases.

After strengthening, render every time:
- The grade card + before/after comparison (Step 4)
- The pipeline step transcript (Step 4.5)
- The final strengthened prompt that will execute (Step 4.6)

The final prompt is shown for transparency, not approval — execution
proceeds in the same response.

## Clarification Gate — Ask Until Confident

**Trigger:** the prompt is > 15 characters (the only floor — handled
deterministically by the hook). Every prompt that reaches this skill is
evaluated for residual ambiguity after strengthening.

**Question budget:** no upper limit. Ask one question at a time and keep
asking until you have full confidence in the user's intent. Stop when
confidence is reached, not when a question count is hit.

**How:** one question per turn with a count and a recommendation. Read
the codebase before asking — do not ask what you can answer yourself.
Each question must be unanswerable from Tier 1/2 context.

**Sequencing:**
1. Strengthening runs first (Steps 0-3)
2. Grade card (Step 4)
3. Clarification Gate runs here, if ambiguity remains
4. Step transcript (Step 4.5) and final prompt preview (Step 4.6) reflect
   the resolved intent
5. Execution (Step 5)

## Resource CRUD Detection

If the prompt implies creating/updating/deleting a Claude Code resource,
follow the batch approval flow in `/prompt-auto-enhance`.

## Pipeline Rules

These are the load-bearing contracts:

- The `*Enhanced:*` indicator is on every response that reaches this rule
- Tier 1 context is gathered before responding
- Strengthening runs for any non-trivial prompt that the hook did not filter
- The grade card, step transcript, and final prompt preview are shown for
  every non-trivial prompt — even Grade A
- The Clarification Gate runs until confidence is reached, not until a
  question count is hit
- Resource CRUD requires the batch approval table — no creates / updates
  / deletes happen without explicit user approval
- Code is read before asking a clarification question
