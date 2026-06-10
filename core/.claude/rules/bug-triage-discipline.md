# Scope: global

# Bug Triage Discipline — miss-analysis and sibling-class audit

version: "1.0.0"

Every bug fix MUST answer two questions before it is considered closed: **"why
did our tests miss this?"** and **"where else does this same class of bug
live?"** A fix that patches only the reported instance, without a miss-analysis
and a repo-wide sibling sweep, leaves the same defect waiting in its siblings.

## One tracker is the SSOT

Bugs are tracked in **one** canonical system (the project's issue tracker — use
`/create-github-issue` where GitHub is the tracker). MUST NOT scatter bug
records into ad-hoc markdown files alongside the tracker — file/issue drift
makes the tracker lie. Skill/automation memory ("what this automation should
remember about the app") is a learning, not a bug — it stays where learnings live.

## Required structure of a filed bug

A bug is not "filed" until it contains, in order:

1. **Reproduction + root cause** — symptom, expected, repro steps, root-cause
   analysis pointing at the exact `file:line`, and a suggested fix.
2. **Why was this missed?** — names the test that *should* have caught it and
   why it didn't (assertion gap / happy-path-only / shape-not-substance /
   tolerance that buries the signal / no coverage at all), and lists the
   specific test additions that would catch the next regression of this class.
3. **Sibling audit (Class N: …)** — describes the *class* of the bug (not the
   instance) and reports a repo-wide search for other locations exhibiting the
   same class. Every sibling MUST be either (a) marked safe with evidence,
   (b) filed as its own bug, or (c) flagged for human spot-check with the reason
   automated search cannot confirm.

## Shape-vs-substance is a first-class miss

When a bug slips past a test that asserted "the card is visible" / "label X is
present" instead of asserting the card's actual **conveyed value**, the "why
was this missed?" section MUST name this as a **shape-vs-substance** miss, and
the fix MUST add a substance assertion (see `output-plausibility-verification.md`).

## Catch-test layering

Choose the **minimum viable layering** that closes the detection gap:

| Bug class | Recommended layer |
|---|---|
| Logic bug in a pure computation | Unit test — fastest, deterministic |
| Logic bug in a view-layer computed value | Component test with mocked data |
| Wrong value rendered to the user | E2E asserting the substance + a structural visual expectation |
| Class spans multiple components | One generic sweep (only when 3+ siblings exist) — prefer it over filing N identical bugs |

Catch-tests added *before* the fix MUST be marked skipped/pending with a
comment linking the bug id; MUST NOT skip a test without a tracking id.

## CRITICAL RULES

- MUST file each bug in the single canonical tracker; MUST NOT create parallel
  markdown bug files that drift from it.
- MUST include a **"why was this missed?"** miss-analysis and a **sibling-class
  audit** in every filed bug, in the same session — not deferred.
- MUST NOT assume a single occurrence is "contained" without running the
  sibling audit; the same defect commonly lives in an un-checked sibling.
- MUST treat shape-vs-substance gaps as a named miss class and add a substance
  assertion in the fix.
- MUST NOT skip/ignore a test without a tracking id referenced in the test.
