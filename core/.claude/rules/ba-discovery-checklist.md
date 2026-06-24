# Scope: global

# BA Discovery Completeness Checklist — the matrix discipline that stops "simple misses"

version: "1.1.0"

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

## Step 0 — establish the FORM FACTOR first (before any other question)

The FIRST BA question on any new app/product MUST establish the **form factor / platform**:
**web app · mobile app · desktop app · CLI · browser extension · something else** — and give the
user ALL the options to choose from. MUST NOT assume it, and MUST NOT carry it over from a prior
build or a sibling project. Everything downstream (UI/UX, stack, deployment, the checklist below)
depends on this answer, so it cannot be deferred or guessed. Only after the form factor is fixed do
you work basic → specific (platform → actors → value → lifecycle → matrix → variants → aha-outputs).

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

## Two product-acceptance gates after discovery (present substance, get an explicit yes)

After discovery and BEFORE building, the BA MUST pause for two explicit user approvals — each
presents the concrete artifact and waits, never infers approval from silence:

1. **BA approach approval** — present the RECOMMENDED solution approach + scope (what's IN, what's
   explicitly OUT) and get the user's explicit approval. Running the discovery is NOT enough; the
   user signs off on the approach the BA recommends before any design or build.
2. **UI/UX design approval** — present the user-facing design (screens/layout for visual apps;
   command surface + output formatting for a CLI) and get explicit approval. This is the G1 design
   gate (`human-approval-gates.md`) — a data/storage/technical-design sign-off does NOT count as
   UI/UX approval; they are different gates.

Sequence: form-factor → discovery → BA-approach approval → UI/UX design approval → build. These
pauses are required clarification, exempt from the decide-don't-ask ban (`decision-authority.md`).

## Independent completeness audit BEFORE G1 (the anti-recurrence gate)

Self-review does not catch what the BA never thought to look for. So before G1, a
**fresh-context reviewer** (separate agent, `independent-test-verification.md` pattern)
audits the written discovery against items 1–6 and asks: "what actor, component, cost,
benefit, variant, or lifecycle stage is MISSING or silently ASSUMED?" Its dissent
BLOCKS G1 — the mockup is not shown for approval until the audit is clean. This is what
converts "the BA should remember" (unreliable) into "an independent check enforces it"
(reliable).

## CRITICAL RULES

- MUST establish the FORM FACTOR (web · mobile · desktop · CLI · extension · other, user picks
  from ALL options) as the FIRST question — never assume it or carry it over from a prior build.
- MUST get explicit user approval of (a) the recommended BA APPROACH + scope and (b) the UI/UX
  DESIGN — as two separate gates, presenting the concrete artifact each time — before building. A
  technical/storage design sign-off is NOT a UI/UX approval.
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
