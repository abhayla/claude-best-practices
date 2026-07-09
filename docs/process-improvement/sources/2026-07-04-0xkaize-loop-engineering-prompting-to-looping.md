Source: https://x.com/0x_kaize/status/2073438517775003671
Captured: 2026-07-08

# 0x_kaize — "Loop Engineering: From Prompting to Looping"

**Author:** 0x_kaize ([@0x_kaize](https://x.com/0x_kaize))
**Posted:** 2026-07-04 · **Engagement at capture:** 349 likes, 48 RTs, 21 replies, 595,775 views
**Format:** Single long-form X-native article (~21.3k chars) — the longest item in the loop-capture cluster.
**Nature:** **Tutorial/workshop restatement of the loop-engineering discourse**, framed as 5 hands-on "lessons" (each with a task, a named failure mode, and 3 self-check questions) building one worked example: a morning-triage loop for a small team. Cites the same June 2026 discourse (Steinberger, Cherny, Osmani, Andrew Ng) already captured elsewhere in this store. **High overlap with the existing cluster** — captured for its distinctive teaching device (5 named "diseases") and two attributed anecdotes worth flagging as unverified.

---

## What it says

Opens with the same three-people-in-a-week origin story as the rest of the cluster: Peter Steinberger's viral two-liner, Boris Cherny's "I don't prompt Claude anymore, I have loops that are running," Addy Osmani's "loop engineering is replacing yourself as the person who prompts the agent," and Andrew Ng's three-nested-loops-by-timescale framing (innermost fastest, outermost slowest, outer loop's input = inner loop's output). Frames loop engineering as adding three things a harness alone lacks: it runs on a timer, spawns helpers, and feeds itself (today's output → tomorrow's input) — "that last one is what makes it a loop, not the same task run N times."

Builds one worked example (a morning-triage loop) across 5 lessons, each mapped to one move and one named failure mode ("disease"):

1. **Discovery** (`.claude/skills/morning-triage/SKILL.md`) — Read / Judge / Stop sections. **Judge is "the ceiling of your entire loop"** — the loop must decide actionable-vs-noise itself, not receive a curated list every morning ("you automated the doing but not the choosing... choosing is usually the more expensive step"). Stop must spell out red lines (never merge, never push to main, uncertain → `./inbox/`). **Disease: Blind Loop** — runs, but a human is still assigning the work each morning; it never surprises you.
2. **Handoff** — one git worktree per finding (`fix/<slug>`), never work on `main` (the landing strip for human review), cap `MAX_PARALLEL` by "how many PRs can I actually review," not compute budget. Cites **Stripe** running 1,000+ PRs/week through loops like this with a human reviewing every one, and using a *smaller* model with strict deterministic gates instead of the biggest available — "a tight verification gate beats raw model power for loop work." **Disease: Tangled Loop** — parallel agents editing the same directory, merge day becomes archaeology.
3. **Verification** (called "the heaviest lesson") — attributes to Anthropic engineer **Prithvi Rajasekaran**: an agent grading its own just-written code will almost always praise it, because by the time it's done its context is stuffed with the self-justification for why it wrote things that way — "it doesn't see the result, it sees the argument for the result." Quote: *"Tuning a standalone evaluator to be skeptical is far more tractable than making a generator critical of its own work."* Prescribes a separate evaluator agent (`.claude/agents/reviewer.md`: ROLE/ASSUME/CHECK/USE/VERDICT) + a `/goal` stop condition judged by a fresh model — ideally a *different model*, not just a different prompt on the same one, since "same model, different prompt" often preserves the same blind spots. Default-skeptical ("ASSUME BROKEN"), judge behavior not intent (run the tests / click the button, don't read-and-vibe), reject with reasons. Acid test: "has your evaluator actually rejected something in the last 5+ turns?" — if not, it's decoration. **Disease: Nodding Loop** — the agent grades its own homework and every turn self-approves.
4. **Persistence** — memory = state written to disk (markdown/DB/board), never context ("context is cleared every refresh; memory is what survives"). Prescribes a `./state/triage.md` with ≥4 columns (finding/source/priority/status) and a discipline of reading one sample PR a day so your mental model of the codebase doesn't silently drift out of date. **Disease: Amnesiac Loop** — the loop rediscovers or redoes yesterday's work because the result only lived in a flushed context.
5. **Scheduling** — hang a real trigger (GitHub Actions cron in the example); "the most dangerous part isn't getting cron wrong, it's getting cron right" — because then it truly runs alone. Set three caps *before* the first autonomous run: per-run budget, daily budget, max retries — "a token cap isn't about saving money, it's a circuit breaker." Cites **Uber** capping engineers at $1,500/person/tool/month after burning through its AI budget in four months. Keep one human door open (PRs never auto-merge, uncertain → inbox, read one sample daily) — "not because a human will always walk through it, but because the door existing keeps you in a position where you can." **Disease: Manual Loop** — four moves built beautifully, no trigger; a script you ran once and forgot ("dazzling on demo day, dead by Thursday").

Closes on **"the 4 debts"** — four things that pile up quietly with no alarm and feed each other (unverified output erodes understanding → eroded understanding invites surrender → surrender lets the loop run longer/spend more → which produces more unverified output). A pre-launch self-audit checklist (evaluator actually rejects / read one sample PR daily / kept the habit of saying "this is wrong" / caps set before the first run). Closing framing from Osmani: "build the loop like someone who intends to stay the engineer, not just the person who presses go" — "a loop is a faithful multiplier: bring understanding, it amplifies understanding; bring laziness, it amplifies laziness."

---

## ⚠️ Unverified claims — do not propagate as fact

- **Prithvi Rajasekaran quote/attribution** ("Anthropic engineer... tuning a standalone evaluator to be skeptical is far more tractable...") — plausible and consistent with Anthropic's public maker≠checker guidance, but **not independently verified from a primary Anthropic source** in this capture. Attribute to this article, don't assert as an Anthropic-official position.
- **Stripe "1,000+ PRs/week through loops, human reviews every one, smaller model + strict gates"** — a specific vendor case-study claim with no citation in the article. **Unverified** — treat as an anecdote, not a benchmark.
- **Uber "$1,500 per person per tool per month" AI budget cap after 4 months**figure — same treatment: **unverified specific number**, cite only as an illustrative anecdote if repeated.
- No Fable/Claude model-capability, pricing, or benchmark claims appear in this article.

## Relevance to this hub — LOW-MODERATE (fully redundant mechanically; two teaching devices worth stealing, no new mechanism)

Every mechanic here is already covered, usually more authoritatively, by the existing cluster — principally the first-party [ClaudeDevs taxonomy](2026-07-06-claudedevs-getting-started-with-loops.md) (official Turn/Goal/Time/Proactive types, maker≠checker, token discipline) and [0xCodila's Karpathy/Bilevel note](2026-07-01-0xcodila-loop-engineering-karpathy-bilevel.md) (5 building blocks, comprehension-debt). The 5 lessons map 1:1 onto hub doctrine already in place:

| 0x_kaize lesson / disease | Existing hub analogue |
|---|---|
| Discovery skill + "Judge is the ceiling" / Blind Loop | `loop-engineering` DISCOVER stage; `goal-creator` DoD contracts |
| Handoff via `git worktree` per finding, cap by review capacity / Tangled Loop | `context-management.md` worktree guidance; `agent-team-selection.md` (worktree for parallel file isolation) |
| Verification: separate evaluator, ASSUME BROKEN, judge behavior not intent / Nodding Loop | `independent-test-verification.md` + `supervisor-verification.md` (maker ≠ checker) — the article's central point is already the hub's central point |
| Persistence: state on disk, not context / Amnesiac Loop | `context-management.md` rule 6 (compaction survival, state-on-disk); `.remember/` handoff log |
| Scheduling: caps before first run, human door / Manual Loop | trust-score `hard_gates` safety floors; `config/trust-score.yml` threshold; Execute-tier still human-supervised per `plans/agent-teams-incorporation.md` |
| "4 debts" (unverified output → eroded understanding → surrender → more spend) | `claude-behavior.md` rule 4 (verification before completion) + the hub's shadow-mode/walk-phase discipline (don't build for autonomy, prove the trust score first) |

**Honest assessment — no action, confirmation only.** This is the same discourse the hub has already captured and mapped three times over (ClaudeDevs, 0xCodila, Raytar). It surfaces no new hub-doctrine gap, no new primitive, and no first-party fact. The two things worth keeping are teaching devices, not mechanisms:

1. The **5 named "diseases"** (Blind / Tangled / Nodding / Amnesiac / Manual Loop) are a clean mnemonic for a failure-mode checklist — usable if the hub ever writes a `loop-engineering` onboarding doc or a pre-launch self-audit, but this is optional documentation polish, not a doctrine change.
2. The **Stripe/Uber anecdotes**, if ever cited in hub docs, must carry the ⚠️ unverified flag above — they are unsourced numbers in a secondary article, not confirmed case studies.

**Cross-links:** [ClaudeDevs official taxonomy](2026-07-06-claudedevs-getting-started-with-loops.md) (primary source, cite this first), [Raytar — Stop Being the Loop](2026-06-23-raytar-stop-being-the-loop.md), [0xCodila — Karpathy/Bilevel](2026-07-01-0xcodila-loop-engineering-karpathy-bilevel.md).
