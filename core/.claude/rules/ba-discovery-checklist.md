# Scope: global

# BA Discovery Completeness Checklist — the matrix discipline that stops "simple misses"

version: "1.0.0"

The recurring failure: the BA discovers a NARROW slice, ships it, the user spots an
obvious hole, we patch it — then the SAME class of hole reappears next time from a
different angle. Observed three times on one tool: missed actors → missed the
recurring/operating cost lifecycle → missed which cost COMPONENTS benefit which actor.
Patching instances does not fix the class. This rule is the **explicit, enumerated
checklist + an independent audit** the BA runs EVERY time, on EVERY domain, so the whole
class is caught before build — not discovered by the user later.

This is the operational SSOT for BA completeness. It composes with `engineering-roles.md`
(PM mandate — the WHO/WHEN), `full-space-first.md` (the cross-stage principle), and
`human-approval-gates.md` (G1). Those state the principle; THIS is the checklist.

## The completeness checklist — answer ALL before leaving discovery

Discovery is NOT done (no questions → UI → build) until each is enumerated, researched
(web-search when the domain isn't fully known), and written down:

1. **ACTORS** — every distinct user/beneficiary type (by role, legal form, tax status,
   segment, lifecycle stage). Mark the PRIMARY one. *(miss #1: modeled 2, the space was 9.)*
2. **VALUE per actor** — the concrete benefit each gets that they can't easily get
   elsewhere. An actor with no benefit is dropped; a tool with no benefit is challenged.
3. **LIFECYCLE** — the full cost/benefit stream over the realistic usage/ownership
   HORIZON: acquisition + recurring/operating + financing (with tax treatment) + exit/
   resale — never just the triggering transaction. *(miss #2: modeled the purchase, not
   the years of ownership.)*
4. **COMPONENT × ACTOR MATRIX** — decompose the headline figure into its line-item
   COMPONENTS; cross EVERY component against EVERY actor; fill each cell with
   benefit / dead-cost / N-A + the mechanism. *(miss #3: never asked which price
   components a company recovers that a salaried buyer cannot.)*
5. **VARIANTS / AXES** — asset/product variants, regimes, modes, %-of-use, thresholds,
   and rules-in-flux (with dates) that change the answer.
6. **THE "ANSWER" / AHA OUTPUTS** — the decision the tool actually informs; the
   high-value insights (break-evens, thresholds, where the cheaper choice flips).

## The matrix discipline (the technique that kills "simple misses")

Never reason about the headline number as a **scalar**. Always reason about it as a
**matrix: ACTORS × COMPONENTS × LIFECYCLE-STAGES**. For every cell ask "does this differ
by actor / over time?" — the ASYMMETRIES (what benefits actor A but is dead cost for
actor B) ARE the product's differentiated value, not an afterthought. Any axis or cell
you cannot fill is an OPEN discovery question — research it; do NOT silently assume it
away. A scalar mental model is how every "simple thing" gets missed.

## Independent completeness audit BEFORE G1 (the anti-recurrence gate)

Self-review does not catch what the BA never thought to look for. So before G1, a
**fresh-context reviewer** (separate agent, `independent-test-verification.md` pattern)
audits the written discovery against items 1–6 and asks: "what actor, component, cost,
benefit, variant, or lifecycle stage is MISSING or silently ASSUMED?" Its dissent
BLOCKS G1 — the mockup is not shown for approval until the audit is clean. This is what
converts "the BA should remember" (unreliable) into "an independent check enforces it"
(reliable).

## CRITICAL RULES

- MUST complete all six checklist items (actors · value-per-actor · lifecycle ·
  component×actor matrix · variants · aha-outputs), with research, before leaving
  discovery for questions/UI/build.
- MUST reason in the ACTORS × COMPONENTS × LIFECYCLE matrix, never as a scalar; MUST
  fill or flag every cell — an unfillable cell is an open question, never a silent assumption.
- MUST surface the cross-actor ASYMMETRIES explicitly — they are the value proposition.
- MUST pass an INDEPENDENT completeness audit (fresh-context reviewer vs items 1–6)
  before G1; a dissent BLOCKS G1. MUST surface a skipped audit verbatim.
- MUST NOT treat a user-caught omission as a one-off patch — file it as a checklist gap
  and confirm the checklist (or its audit) would now catch that class (`learnings-routing.md`).
