Source: https://x.com/0xChaseTM/status/2074812548684083542
Captured: 2026-07-08

# 0xChaseTM — "How To Build Your Own Loop (Boris Cherny's Method)"

**Author:** 0xChaseTM ([@0xChaseTM](https://x.com/0xChaseTM))
**Posted:** 2026-07-08 · **Engagement at capture:** 50 likes, 11 RTs, 7 replies, 46,134 views
**Format:** Single long-form X-native article (~7.8k chars).
**Nature:** **Conceptual loop explainer + walkthrough tutorial.** One second-hand attribution to verify (Boris Cherny "My job is to write loops" / "I don't prompt Claude anymore"). **Heavy overlap with the existing loop-capture cluster — especially with the [Raytar note](2026-06-23-raytar-stop-being-the-loop.md)**, which also opens on the same Cherny quote. Captured for completeness; low incremental signal.

---

## What it says

Opens on Boris Cherny (creator of Claude Code) reportedly no longer writing prompts — his line: *"My job is to write loops."* Instead of typing instructions and reading results, he builds a process that prompts itself, checks its own work, and stops only when done.

**Why prompting doesn't scale:** a loop is a small program that repeats act → check → (if not done) feed back → run again, with no one clicking "send." The stopping condition is what separates a real loop from a script — it must be **machine-checkable** ("all auth tests pass"), not a vague judgment call ("make the code cleaner"). **The judge can't be the worker** — a separate AI verifies, because a model grading its own output declares victory too soon; per Cherny this is worth roughly a 3x quality jump. Last ingredient: **persistent memory** — a file the loop reads every run so mistakes don't repeat.

**The cost of doing it by hand:** the human is the slow part of every AI interaction — not model intelligence. Cherny's fix: remove the person pressing "send" so the AI runs as fast as it thinks.

**Inside Cherny's setup (as reported):** he no longer prompts Claude at all; "a couple hundred agents" read his GitHub, team chat, and feedback channels, then decide what to build next. He deleted his code editor months ago; most of his work happens from his phone. Every line of his code is now written by Claude Code — his job is designing the loops. The loops are unglamorous: babysitting PRs, fixing broken builds, clustering feedback, pruning dead branches — each loop owns one narrow slice and runs continuously because the codebase never stops changing.

**Build-your-first-loop walkthrough** (worked example: a daily research digest): (1) define a job you already repeat and resent; (2) write a **finish line the loop can verify** — "a file with linked, deduplicated, time-bounded items" is checkable, "write a good digest" is not; (3) describe the work as a repeatable instruction — `/goal` sets the target, `/loop` runs against it repeatedly until met, unattended (Ctrl+C to step back in); (4) put it on a schedule — `/loop` with an interval runs recurring up to ~3 days unattended on your machine; for surviving a closed laptop, save as a cloud routine; (5) supervise the first few runs in manual mode, then switch to auto once the output earns trust — "the shift from checking every turn to trusting the finish line is the entire skill."

**What actually changed:** the reframe isn't syntax — it's replacing "what should I tell the AI to do next" with "what does done look like, and how will I know when it's reached."

---

## Relevance to this hub — LOW (redundant with the cluster, confirmed against Raytar; no new mechanism)

Every mechanic here — machine-checkable stop condition, maker≠checker verification (3x quality claim), persistent state file, `/goal` + `/loop` as the two commands, manual-then-auto graduation, "what does done look like" reframe — is already captured, in more depth and with a first-party citation, by:

| 0xChaseTM point | Existing hub mapping |
|---|---|
| Machine-checkable finish line, not a vague goal | `goals.yml` DoDs; trust-score `threshold` + `hard_gates` |
| Separate verifier AI ("judge can't be worker"), ~3x quality claim | `independent-test-verification.md` + `supervisor-verification.md` (maker≠checker) — same claim already surfaced via the [ClaudeDevs first-party note](2026-07-06-claudedevs-getting-started-with-loops.md) ("reviewer with fresh context is less biased") |
| Persistent memory file read every run | `.remember/` handoff log; `context-management.md` rule 6 (state-on-disk survival) |
| `/goal` sets target, `/loop` runs repeatedly, manual→auto graduation | `loop-engineering` skill (DISCOVER→PLAN→EXECUTE→VERIFY→SHIP) + native `/goal`/`/loop` primitives already mapped in the ClaudeDevs capture's adoption table |
| "A couple hundred agents" watching GitHub/chat/feedback, phone-only workflow | Anecdotal color on Cherny's personal setup — no new hub-actionable mechanism |
| "What does done look like" reframe | `plan-before-coding.md` + `decision-authority.md` (decide, don't ask, against a stated DoD) |

**No genuinely new angle survives comparison with the cluster.** This capture adds narrative color (the personal-workflow anecdote about Cherny's phone-only, editor-deleted setup) but zero new mechanism, primitive, or actionable doctrine gap. The [Raytar note](2026-06-23-raytar-stop-being-the-loop.md) already opens on the identical Cherny quote and covers the same `/goal`/`/loop` pair, the same verifier-is-non-negotiable point, and the same state-file argument — with a sharper concrete example (fabricated-sources catch). The [ClaudeDevs note](2026-07-06-claudedevs-getting-started-with-loops.md) remains the authoritative, first-party citation for all of it.

**Attribution note:** the Boris Cherny quotes here ("My job is to write loops," "I don't prompt Claude anymore," the ~3x quality-jump figure) are second-hand, un-sourced-in-article claims — attribute to Cherny via this secondary account, do not assert as fact. This is now the **third** capture repeating this same Cherny quote lineage (Raytar, 0xCodila, this one); treat it as recurring folklore around a real Anthropic-team member until a primary source (his own post/talk) is located.

**Action:** no action — confirmation-only capture, redundant with the Raytar/ClaudeDevs cluster. Do not duplicate anything into `loop-engineering-spec.md` from this source; if a why-verify example is ever needed there, use Raytar's fabricated-sources example (already flagged as the best teaching case) instead.

**Cross-links:** [Raytar — Stop Being the Loop](2026-06-23-raytar-stop-being-the-loop.md) (same Cherny quote, sharper example), [ClaudeDevs — Getting Started with Loops](2026-07-06-claudedevs-getting-started-with-loops.md) (first-party authoritative source, cite this one), [0xCodila — Karpathy/Bilevel loop](2026-07-01-0xcodila-loop-engineering-karpathy-bilevel.md).
