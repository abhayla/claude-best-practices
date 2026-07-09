Source: https://x.com/Raytar/status/2069212188619805179
Captured: 2026-07-08

# Raytar — "Stop Being the Loop. Here's How to Make Claude Work While You Sleep."

**Author:** Raytar ([@Raytar](https://x.com/Raytar))
**Posted:** 2026-06-23 · **Engagement at capture:** 860 likes, 143 RTs, 14 replies, 3.35M views
**Format:** Single long-form X-native article (~6.5k chars).
**Nature:** **Conceptual loop explainer.** One second-hand attribution to verify (Boris Cherny "I don't prompt Claude anymore," June 2026). **High overlap with the existing loop-capture cluster** — captured for completeness + two crisp framings; largely corroboration.

---

## What it says

Opens on **Boris Cherny** (built Claude Code) saying June 2026 *"I don't prompt Claude anymore — loops prompt Claude for me; my job now is writing loops."* Frames the reader as currently **being the loop** (type → edit → run test → paste error → retry = babysitting).

**The killer example:** ask for a one-page brief; the sources look real but **some are fabricated** — a single prompt can't catch it *"because Claude stays confident it's right until something opens the link."* Rerun as a loop with a **measurable bar** ("every claim needs ≥3 sources, every link must open to a page that backs the claim") and Claude goes link-by-link, discards dead/fake ones, finds replacements, checks until every source opens, then stops. *"It never gets bored. It never skips the boring ones."*

**The 5 beats of every loop:** (1) **Find the work** (open tasks, failing tests, unread emails, files); (2) **Do it** (one item at a time); (3) **Check itself** (a second pass confirms done + correct, "not just produced"); (4) **Remember** (write down what's finished — "the state file is the quiet hero; without it every run starts from zero"); (5) **Go again** (repeat until nothing's left, then stop or ping you). *"Prompting is doing the work. Loop engineering is managing the worker."*

**"Isn't this just a cron job?" No** — *"a cron job runs a script; a loop runs Claude. The decision-maker in the middle is the entire point. A script can't look at a broken test and figure out a different fix. Claude can."*

**The two commands:** `/goal` = "work until this is true" (a second copy of Claude checks the goal after every turn; *"that self-check is the whole difference between a real loop and a prompt that runs once and hopes"*); `/loop` = "check this again and again" on a rhythm (`/loop 30m`, or "every morning triage my inbox"). *"Most strong loops start with `/goal`."*

**When NOT to build a loop** (three honest caveats): one-off tasks (a plain prompt is faster); loops cost more (several Claude runs per item → hit usage limits faster); vague work doesn't belong in a loop ("think of a better product strategy" isn't a loop — figure out the actual goal first).

---

## Relevance to this hub — MODERATE (redundant with the cluster; two sharp framings; verify one attribution)

Every mechanic here is already covered by the first-party [ClaudeDevs taxonomy](2026-07-06-claudedevs-getting-started-with-loops.md) and the [0xCodila Karpathy/Bilevel note](2026-07-01-0xcodila-loop-engineering-karpathy-bilevel.md) — the 5 beats = the hub's DISCOVER→PLAN→EXECUTE→VERIFY→SHIP; `/goal`+separate-checker = maker≠checker + DoD gating; state file = `.remember/`/scratchpad; when-not-to-build = the 4-part loop-worth test / YAGNI. **No new mechanism.** Two things worth keeping:

1. **The fabricated-sources example is the single best concrete teaching case for "a verifier is non-negotiable"** in the whole capture cluster — a single confident prompt silently ships fake citations; only a measurable, link-opening loop catches it. If the hub ever writes a *why-verify* explainer for `loop-engineering-spec.md` or onboarding, **this is the example to use** (LOW-priority, documentation-only). It's the operational face of `independent-test-verification.md`.
2. **"Prompting is doing the work; loop engineering is managing the worker"** + **"a loop runs Claude, not a script — the decision-maker in the middle is the point"** — the crispest one-liners distinguishing a loop from a cron job, useful framing for the same spec.

**One attribution to verify:** the Boris Cherny "I don't prompt Claude anymore" quote (June 2026) — appears here and (as "Cherny stopped prompting") in the [0xCodila note](2026-07-01-0xcodila-loop-engineering-karpathy-bilevel.md). Two captures now cite it; still second-hand — **attribute, don't assert as fact** until sourced. **No other verification prerequisite** (no model-capability claims). **Cross-links:** the whole loop cluster — [ClaudeDevs](2026-07-06-claudedevs-getting-started-with-loops.md) (first-party), [0xCodila](2026-07-01-0xcodila-loop-engineering-karpathy-bilevel.md), [hanako while-you-sleep](2026-06-13-claude-loops-while-you-sleep.md), [Andrew Ng 3 loops](2026-06-30-andrew-ng-3-product-development-loops.md).
