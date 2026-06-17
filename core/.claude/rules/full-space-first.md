# Scope: global

# Full-Space-First — discover the whole space before acting, at every stage

version: "1.0.0"

The biggest failure mode surfaced building real features: executing the NARROW
literal input instead of first discovering the FULL relevant space from the
user's/consumer's perspective. It is NOT BA-only — it recurs at every SDLC +
loop-engineering stage (the canonical 10-step SDLC and the DISCOVER→PLAN→EXECUTE
→VERIFY loop). Before acting at ANY stage, expand to the full space (research /
enumerate it; WEB-SEARCH when the domain isn't fully known), then act to MAXIMIZE
the consumer's benefit — never satisfy only the literal input handed to you.

## Per-stage manifestation (pointer pattern — detail lives in the named SSOT)

| Stage | "Full space" to discover FIRST | SSOT (detail) |
|---|---|---|
| Requirements / BA | all use-cases + actors + the value proposition (who/why) | `engineering-roles.md` PM mandate |
| Design / UI-UX | the full option space (multiple distinct designs), all UX states | `engineering-roles.md` UI/UX role |
| Build / code | all code paths + edge cases + the DEFAULT product path (not happy-path only) | `error-handling.md`, `output-plausibility-verification.md` |
| Test | the full test-case/combination space; coverage completeness; substance not shape | `testing.md`, `output-plausibility-verification.md`, `dod-verbs.md` |
| Bug fix | the whole bug CLASS — sibling sweep across all occurrences | `bug-triage-discipline.md` |
| Review | the full changed surface + all siblings, not the first finding | `supervisor-verification.md`, `bug-triage-discipline.md` |
| Deploy / Ops | all failure + rollback + post-deploy-verify paths | `decision-authority.md`, `human-approval-gates.md` |
| Loop DISCOVER | the full actionable work/triage space, ranked by user benefit | `goal-anchored-decisions.md` |

## How to apply (every stage / workflow)

- **Discover first.** Enumerate the full space (domain + user perspective); WEB-SEARCH to enumerate
  it when the space isn't fully known — before questions, design, code, tests, or ship.
- **Anchor to benefit.** Coverage serves the consumer's benefit + the documented goal
  (`goal-anchored-decisions.md`), never feature-symmetry or local convenience.
- **Verify completeness before "done".** Ask "what case / actor / path / sibling did I NOT cover?"
  and route it through the independent check where one exists (`independent-test-verification.md`,
  `supervisor-verification.md`).
- **No benefit → challenge the work.** If you cannot state the consumer benefit, question whether to
  do it at all.

## CRITICAL RULES

- MUST discover the full relevant space (from the consumer's perspective; research / web-search when
  unknown) BEFORE acting at any stage — never execute only the narrow literal input.
- MUST anchor coverage to user benefit + the documented goal, not symmetry or convenience.
- MUST verify completeness before "done" (what's uncovered?), via an independent check where one exists.
- MUST cross-reference the per-stage SSOTs above — this rule NAMES the cross-cutting principle; it
  MUST NOT duplicate their detail (`configuration-ssot.md`).
