# Scope: global

# Goal-Anchored Decisions

version: "1.0.0"

Every non-trivial decision — build vs defer vs cut, a design fork, prioritization,
scope, "which option?" — MUST be evaluated against **THIS project's documented goal
and its target users**, and resolved to the option (or **combination** of options)
that best serves them. Local engineering convenience, feature-completeness, symmetry,
or "the matrix has a hole" are NOT reasons to build — serving the goal + the target
user is.

This is the **substantive criterion** for evaluating options. It composes with — does
NOT replace — `decision-authority.md` (WHO decides + escalate-vs-decide + the
confidence gate), `claude-behavior.md` rule 21 (YAGNI — don't build the unneeded), and
`design-ssot.md` (where the goal/scope contract lives). Cross-reference, never duplicate
(`configuration-ssot.md`).

## Anchor to the documented goal (not a vague "goal")

"The goal" and "the users" are concrete, documented facts — read them, don't guess:

- The **product goal** and what the project *is* (and is not) — its `CLAUDE.md`
  "what this is", PRD, or the canonical design doc (`design-ssot.md`).
- The **primary user / persona** the product serves first, and the current
  **priority order** (e.g. correctness → retention → reach) if the project documents
  a stage/now-order. Where a project keeps a "current stage → default roles" block
  (`engineering-roles.md`), that block is part of the anchor.

If the project has NOT documented a goal/persona, surface that gap (a decision cannot
be goal-anchored against an undocumented goal) and capture it per `design-ssot.md`
before proceeding — do not invent one silently.

## How to apply (every recommendation)

1. **Name the goal + user impact explicitly** — the anchor MUST be visible and
   auditable in the recommendation ("sharpens the primary persona's core accuracy —
   Tier-0 correctness"), never implicit.
2. **Prefer combinations over false binaries** — the best answer is often "ship the
   correctness bit + build the persona-aligned feature + defer the wrong-user one,"
   not a single option.
3. **Tie-break by the primary persona + the documented priority order** — when options
   conflict, the primary persona's needs and the order (e.g. correctness → stickiness →
   reach) decide. An option serving a **different/later persona** loses to one serving
   the primary persona, unless that later need is itself the documented next priority.
4. **Correctness / honesty / safety errors rank high regardless of fix size** — for any
   product where a silently-wrong output harms the user (money, health, scoring,
   permissions), options that remove the harmful error outrank larger feature work
   (ties to `output-plausibility-verification.md`).

## Guard against (the two failure modes this rule kills)

- **Feature-completeness bias** — building X because a matrix/symmetry/catalog has a
  hole, not because a target user needs it (ties to YAGNI).
- **Local-optimum bias** — picking the engineering-convenient option that does not move
  the goal or the user.

## CRITICAL RULES

- MUST evaluate every non-trivial decision against the documented goal + target user —
  never local convenience, feature-completeness, or symmetry.
- MUST state the goal/user reasoning IN the recommendation (a visible, auditable anchor).
- MUST consider combinations of options, not just single options.
- MUST let the primary persona + the documented priority order break ties; a
  different/later persona loses to the primary one unless it is the documented next
  priority.
- MUST treat correctness/honesty/safety errors for the target user as high priority,
  regardless of fix size.
- MUST surface (and capture per `design-ssot.md`) an undocumented goal/persona rather
  than inventing one — a decision cannot be anchored to a goal that was never written down.
