# Scope: global

# Design & Scope Single Source of Truth (SSOT)

version: "1.0.0"

Every design decision, screen/feature pattern, and unit of agreed scope MUST have
exactly one canonical home in the project's documentation — and that home MUST be
updated at the moment the decision is made, not after the code is written. This is
distinct from two sibling rules: `configuration-ssot.md` owns *Claude Code config*
layering, and `design-principles.md` (DRY) owns *code-level* knowledge duplication.
This rule owns the **design/scope decision record and the workflow that keeps it true.**

## The Canonical Design Document

Each design concern MUST resolve to one authoritative source — never duplicated across
`CLAUDE.md`, scattered notes, chat history, or code comments.

- Use the project's existing canonical doc (e.g., a `docs/DESIGN.md`, a per-feature
  `CONTEXT.md`, a screen/UI standard doc, or an ADR set). If none exists, create one
  before recording the first decision — do not scatter decisions across ad-hoc files.
- `CLAUDE.md` MUST point to the canonical doc with a one-line pointer, NOT reproduce it
  (see the Pointer Pattern in `configuration-ssot.md`).
- When the same design fact would appear in two places, one MUST be a pointer to the other.

## Capture at Decision Time (the discussion trigger)

When a new scope, pattern, or design decision surfaces **in conversation** — before any
implementation — it MUST be captured into the canonical doc in the same session.

- MUST NOT defer capture to "after I build it" — decisions made in chat evaporate when
  the session ends and silently drift from what gets built.
- The trigger is the *decision*, not the *edit*. A planning/discussion session that
  finalizes scope but writes zero code STILL MUST update the canonical doc.
- Record the decision, the rationale (why this over the alternative), and the date.

## Propagate on Change

When an approved pattern or scope changes, the change MUST be made in the canonical doc
AND propagated to every place that references it, in the same change set.

- MUST NOT edit a screen/feature to follow a new pattern while leaving the canonical doc
  describing the old one — that makes the doc lie.
- After updating the canonical doc, grep for references to the old pattern and update or
  re-point them. Stale references are a defect, not cosmetic.

## Goal Contract Before Finalized Scope

Before implementing finalized scope, the assistant MUST offer (and, once agreed, record)
a short goal contract: what "done" looks like, the acceptance signals, and what is
explicitly out of scope.

- Pin the contract in the canonical doc or the tracked work item before writing code.
- MUST NOT begin implementing finalized scope on unwritten, assumed acceptance criteria —
  surface the contract and get agreement first.
- Trivial, obvious changes (typos, one-line fixes) are exempt — a contract for those is
  overhead, not discipline.

## When This Rule Fires

| Situation | Capture / contract required? |
|---|---|
| New screen, feature, or scope agreed in discussion | YES — capture before building |
| Existing approved pattern changes | YES — update canonical doc + propagate |
| Finalized scope about to be implemented | YES — offer goal contract first |
| Typo, comment, mechanical refactor, or exploratory spike | NO — exempt |

## CRITICAL RULES

- MUST keep every design/scope decision in exactly one canonical doc — pointers, never copies
- MUST capture a decision into the canonical doc at decision time, including in discussion-only sessions
- MUST update the canonical doc AND propagate to all references when a pattern changes
- MUST offer and record a goal contract before implementing finalized scope
- MUST NOT defer design capture until after implementation, or start finalized scope on assumed acceptance criteria
- This rule is advisory (judgment-requiring). For the mechanically-checkable slice — "a screen/feature file changed but the canonical doc didn't" — add a project-level pre-commit hook (see `rule-writing-meta.md`); a rule raises adherence, a hook guarantees it
