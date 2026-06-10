# Scope: global

# Learnings Routing — one canonical home, typed before filed

version: "1.0.0"

When a session produces a learning (a correction, a gotcha, a "next time do X"),
it MUST be **typed first, then routed to exactly one canonical home** — not
dumped wherever the session happens to be. A learning filed in the wrong layer,
or duplicated across layers, rots: it is either never re-read or it drifts from
its sibling copy. This is the capture-side complement to the SSOT rules
(`configuration-ssot.md`, `design-ssot.md`) and the self-improvement loop
(`/self-improve`, `/learn-n-improve`).

## Type the learning before filing it

Classify every learning as **GENERIC** or **PRODUCT-SPECIFIC** — the type
determines the home:

| Type | Means | Canonical home |
|------|-------|----------------|
| **GENERIC** (process / tooling / craft) | True regardless of *this* product — a workflow improvement, a Claude-Code usage lesson, a language/tool gotcha | A skill (if it's a procedure), a rule (if it's a constraint), or the project's lessons log — the layer that owns that *kind* of knowledge per `configuration-ssot.md` |
| **PRODUCT-SPECIFIC** (domain / this codebase) | Only true for this product's domain, schema, or business rules | The product's own docs / domain rule / design doc (`design-ssot.md`) — never a generic skill or hub-distributable pattern |

Mixing the two is the common error: a product-specific quirk written into a
generic skill pollutes every project that uses it; a generic craft lesson buried
in product docs is never reused.

## Prefer a deterministic gate over prose

When a learning *can* be enforced mechanically, encode it as a gate (a hook, a
linter rule, a test, a CI check) rather than as advisory prose — prose lessons
lose to time pressure (`rule-writing-meta.md`). File the prose lesson too, but
treat the gate as the real fix.

## Dedup and propose, don't auto-apply

- Before filing, search the target home for an existing entry on the same point
  — **update it** rather than adding a near-duplicate.
- Routing a learning into a **rule change** is PROPOSE-only: surface the proposed
  rule and get explicit approval before applying it (`claude-behavior.md` rule 5).
  Filing a lesson or a product doc is autonomous; changing a behavioral rule is not.

## CRITICAL RULES

- MUST classify each learning as GENERIC or PRODUCT-SPECIFIC before filing it,
  and route it to exactly one canonical home for that type.
- MUST NOT write a product-specific learning into a generic/distributable
  pattern, or a generic craft lesson into product docs.
- MUST prefer a deterministic gate (hook/lint/test) over advisory prose when the
  learning is mechanically enforceable.
- MUST dedup against the existing home (update, don't duplicate); MUST treat any
  rule-change routing as PROPOSE-only pending approval.
