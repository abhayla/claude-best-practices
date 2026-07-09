Source: https://x.com/VK_ROXy/status/2073157377927372941
Captured: 2026-07-08

# VK_ROXy (@VK_ROXy) — "How To Actually Use Fable 5 (The Playbook) PART 2"

**Author:** VK_ROXy ([@VK_ROXy](https://x.com/VK_ROXy))
**Posted:** 2026-07-03 · **Engagement at capture:** 13 likes, 0 RTs, 11,301 views
**Format:** Single long-form X-native article (~6.1k chars), Part 2 of a 2-part series (Part 1: https://x.com/VK_ROXy/status/2072430144761782517, not separately captured).
**Nature:** **Fable-5 usage playbook / cost-collapse narrative.** Summarizes a third-party piece — "A Field Guide to Fable: Finding Your Unknowns" by Anthropic dev advocate Thariq (@trq212), said to be published 2026-07-03 — into an 8-prompt workflow spanning pre/during/post-implementation, framed around Rumsfeld's known/unknown knowns-unknowns quadrant and heavy $-savings-per-feature arithmetic.

---

## ⚠️ Verification gate — do NOT propagate as fact until checked vs `claude-api` / official docs

- **All dollar figures are unverified, unsourced arithmetic** — "~$8,000 saved pre-implementation," "~$6,000 during," "~$4,000 post," "~$18,000 total per feature," loaded-rate assumptions ("~$200/hour"), and "$20/month" Fable pricing. No methodology, no citation, no controlled comparison — treat as rhetorical framing, not a benchmark.
- **The existence and authorship of "A Field Guide to Fable: Finding Your Unknowns" by Thariq (@trq212), and its 2026-07-03 publish date — unverified**, not fetched/confirmed in this capture. If this hub ever cites that guide's content directly, fetch and cache it per `claude-docs-cache.md` first.
- **The "Fable launch video edited entirely by Claude Code" anecdote (including the "didn't know what color grading was" detail) — unverified anecdote**, sourced secondhand from the same unconfirmed article.
- **"287,400 people saw the post" and all engagement/reach figures — unverified**, self-reported.
- No model-capability, pricing-tier, or benchmark claim in this piece should be treated as confirmed Fable 5 fact absent independent verification.

---

## The 8-prompt playbook (faithful summary)

Framed as three phases, each with a "$X saved vs. old labor stack" pitch:

**1/3 Pre-implementation** (~$8,000/feature claimed saved vs. a staff engineer's discovery week):
- Prompt 1: Blindspot pass
- Prompt 2: Brainstorm and prototype
- Prompt 3: Interview me
- Prompt 4: References
- Prompt 5: Implementation plan
- Mistake to avoid: skipping the blindspot pass out of confidence — "confidence is what unknown unknowns exploit."

**2/3 During implementation** (~$6,000/feature claimed saved vs. senior review/revert cycles):
- Prompt 6: Implementation notes — a single `implementation-notes.md` file logging every decision and deviation from plan, defaulting to the conservative option on deviation, read once by a human to catch drift before it compounds.
- Metric to watch: count of deviations logged — zero means either a trivial task or an agent hiding decisions.

**3/3 Post-implementation** (~$4,000/feature claimed saved vs. tech-writer/senior-walkthrough/PM stack):
- Prompt 7: Pitch and explainer — demo-first framing so reviewers start from the same unknowns the author did.
- Prompt 8: Quiz me before merge — a comprehension check before merging.
- Mistake to avoid: merging on a passing quiz score alone if the quiz was "too easy" — ask the agent to write the hard questions first.

**Closing framing:** the old per-feature labor stack (~$18,000) collapses to "the same $20/month" subscription; "the map isn't the moat anymore, asking better questions is."

---

## Relevance to this hub — LOW-MODERATE (restates existing doctrine via a promotional cost narrative; one workflow artifact worth noting)

This is Part 2 of a series already thin on hub-actionable content; it overlaps heavily with the Fable-5 cluster already captured. Map:

| VK_ROXy's playbook item | Existing hub analogue |
|---|---|
| Prompt 1 Blindspot pass, Prompt 3 Interview me | `prompt-auto-enhance.md` Clarification & Confidence Gate; `/grill-me` |
| Prompt 2 Brainstorm and prototype | `/brainstorm` skill |
| Prompt 4 References, Prompt 5 Implementation plan | `/writing-plans`, `plan-before-coding.md` |
| Prompt 6 `implementation-notes.md` deviation log | Partial analogue: `record_task_run.py` / trust-score ledger records signals, but the hub has no single human-readable "deviations from plan, defaults to conservative" running log per task — closest existing artifact is the plan file itself plus commit messages; not an exact match, no action proposed absent a concrete gap report |
| Prompt 7 Pitch and explainer (demo-first) | No direct hub analogue — documentation pass (`workflow.md` Step 7) is closer to changelog/docs than a "reviewer pitch," low value to add speculatively (YAGNI) |
| Prompt 8 Quiz me before merge | `supervisor-verification.md` / `independent-test-verification.md` (maker≠checker) cover the underlying discipline — a literal "quiz" mechanic is a lighter-weight variant, not a gap |
| Overall "known unknowns vs unknown unknowns" framing | `decision-authority.md` (state assumptions, flag uncertainty per `claude-behavior.md` rule 3) |
| $ savings / cost-collapse narrative | Not hub-relevant; marketing framing, not a verifiable operating fact |

**Net-new for the hub: none confirmed.** The `implementation-notes.md` running-deviation-log idea is the one item with a shape the hub doesn't have verbatim (a human-readable, single-file plan-deviation log distinct from commit history or the trust-score ledger) — flagged for awareness only, not proposed as a rule since it rests entirely on an unverified secondhand article and no concrete pain point has surfaced in hub usage to justify adding it (YAGNI per `claude-behavior.md` rule 21).

**Action: none.** File for corroboration-count purposes only; do not cite the dollar figures or the Thariq guide's existence anywhere outside this capture without independent verification. Cross-links: [kanikabk 10 mistakes](2026-07-08-kanikabk-10-mistakes-with-fable5.md), [undefinedki build anything](2026-07-04-undefinedki-build-anything-with-fable5.md), [mahaximus 12 prompting moves](2026-07-09-mahaximus-fable5-12-prompting-moves.md), [0xmoysei 6 rules](2026-07-02-0xmoysei-master-fable5-6-rules.md).
