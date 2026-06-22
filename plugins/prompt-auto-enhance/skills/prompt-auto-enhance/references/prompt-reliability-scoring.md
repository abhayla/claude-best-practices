# Prompt Reliability Scoring — RETIRED

This standalone scoring system was retired in SKILL.md v3.0.0 and replaced
by **Verbose Grade Mode** in the unified Quick Grade rubric.

## Why retired

The previous design ran two parallel scoring systems:

| System | Scale | Dimensions | Triggered By |
|--------|-------|-----------|-------------|
| Quick Grade (auto-strengthening) | 1-5 weighted | 6 dims | non-trivial prompts |
| Reliability Scoring (manual audit) | 1-10 unweighted | 5 dims | "score" / "evaluate" / "audit" |

Two scales, two dimension lists, two report templates — same job. The
v3.0.0 unification keeps one rubric (1-10, 6-7 weighted dimensions, A-F
grading) and adds a verbose mode for explicit audits.

## Where the functionality lives now

**Read:** `references/grading-rubric.md`, section "Verbose Mode (entry point:
'score' / 'evaluate' / 'audit')".

Verbose mode runs the same Quick Grade rubric with three additions:

1. **Quote-as-evidence** — every dimension score cites a phrase from the
   prompt that justifies it (the requirement that was unique to the old
   reliability flow).
2. **Use case input** — ask the user to describe the prompt's use case
   before scoring; same prompt scores differently per use case.
3. **Launch-risk flagging** — dimensions scoring below 7 are labeled
   "launch risks" with offending quote, failure mode, and fix.

## Migration mapping

| Old (Reliability Scoring) | New (Verbose Grade Mode) |
|---|---|
| Instruction Clarity (1-10) | Intent Clarity (1-10, weight 0.25) |
| Output Format (1-10) | Output Specification (1-10, weight 0.15) |
| Constraint Strength (1-10) | Constraint Precision (1-10, weight 0.20) |
| Edge Case Handling (1-10) | Subsumed under Context Sufficiency (1-10, weight 0.20) — edge cases are a context-completeness signal |
| Tone Consistency (1-10) | Tone Consistency (conditional weight 0.10 when prose/creative/UX) |
| — | Role & Framing (1-10, weight 0.10) — newly explicit |
| — | Example Grounding (1-10, weight 0.10) — newly explicit |

## Verdict mapping

| Old Verdict | New Grade |
|---|---|
| 9.0+ Production ready | A (8.0-10.0) |
| 7.0-8.9 Viable with hardening | B (6.0-7.9) |
| 5.0-6.9 Significant rework | C (4.0-5.9) |
| Below 5.0 Redesign | D (3.0-3.9) or F (1.0-2.9) |

## File preservation

This reference file is kept (not deleted) so existing links from external
sources resolve to a redirect rather than a 404. Future updates to verbose
scoring should land in `grading-rubric.md`, not here.
