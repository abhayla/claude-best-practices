# Scope: global

# Output Plausibility Verification — catch "wrong-but-working", not just "broken"

version: "1.0.0"

A user-facing value that **renders cleanly, type-checks, and passes the unit
tests** can still be **domain-absurd**. Mechanical-green ≠ correct. Every
verification of a user-facing output — above all a computed number (money,
dates, scores, projections, rates) — MUST include a **semantic plausibility
check** ("is this value SANE for this scenario?"), not only the mechanical
gates ("does it render / persist / pass?").

This rule owns the **substance** axis of verification. It complements, and does
not duplicate, `claude-behavior.md` rule 4 (verify your work) and
`testing.md` (which assert shape: does it render, persist, pass).

## Why this rule exists (the failure it kills)

A computed headline can be wrong while every gate stays green: the type-check
passes, the component renders, the console is clean, and the test asserts the
value *matches the current computation* (shape) rather than *being domain-sane*
(substance). The classic miss: a tool shows a 30-year-old retiring at age 81 —
absurd on sight — yet it ships because no gate asked *"is this plausible?"* and
the reviewer accepted mechanical-green without the flinch.

A second trap rides along: the test exercised a **non-default configuration**
(a convenient code path) while the **product default** is something else — so
the test was green on a path no user actually sees.

## CRITICAL RULES

- MUST apply a **semantic sanity check** to every user-facing output value
  before declaring done — especially computed numbers. Ask "would a domain
  expert (or the target user) flinch at this?" An out-of-range age, a negative
  or infinite total, a rate of 3% or 90%, a tax greater than income → STOP and
  investigate the **root cause**. Do NOT accept it because the suite is green.
- MUST verify on the **DEFAULT product path** — the exact inputs/mode/lens a
  user sees by default. Never substitute a convenient configuration; a test
  green on a non-default path is a divergence that hides real bugs.
- MUST add a **plausibility bound** (a domain-sane range asserted on the
  default path) for any NEW headline/flagship output field, so an
  absurd-but-rendering value is a CI failure, not a silent ship.
- MUST treat tests that assert "matches the current computation" as **shape
  locks, not correctness proofs** — pair every such lock with at least one
  **substance** assertion (sane bounds, a coherence invariant such as
  numerator/denominator drawn from the same set, or agreement with an
  independent computation path).
- MUST run a **sibling sweep** across the same output class on the default path
  before closing a fix — a one-spot patch leaves the other consumers wrong
  (see `bug-triage-discipline.md`).
- MUST NOT accept "renders / no console error" as proof a computed value is
  correct — that is a claim about shape, never about substance.

> **Salience note:** this gate is **advisory-only** — plausibility is semantic, so no
> deterministic hook can detect a domain-absurd-but-rendering value (unlike the
> verifier-edge gates, which `verifier-edge-guard.sh` now backstops). The codifiable slice
> is the **plausibility bound** above — encode it as a CI assertion on the default path so an
> absurd value fails the build; the prose rule carries the rest and demands extra self-discipline.
