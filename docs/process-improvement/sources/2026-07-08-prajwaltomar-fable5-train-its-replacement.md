Source: https://x.com/PrajwalTomar_/status/2074810260271800596
Captured: 2026-07-08

# Prajwal Tomar — "Fable 5 Leaves July 12. Make it train its replacement before it does."

**Author:** Prajwal Tomar ([@PrajwalTomar_](https://x.com/PrajwalTomar_)) — runs an AI agency at $20K MRR + an AI app studio.
**Posted:** 2026-07-08 · **Engagement at capture:** 59 likes, 5 RTs, 2 replies, 135,063 views.
**Format:** Single long-form X-native article (~12.2k chars), a follow-up to the author's earlier 600K-view/4,600-bookmark tweet on the same idea, prompted by Anthropic extending the Fable 5 free window.
**Nature:** **Fable-5 usage/how-to guide with a concrete GitHub prompt artifact.** Contains multiple **model-capability/pricing/date claims — verification block below.** Sits in both the hub's saturated **Fable-5 cluster** and its **self-improvement/skill-authoring** cluster; captured because the mechanism (a 3-phase, git-history-driven skill-generation prompt) is more concrete/actionable than prior captures in either cluster, not because the framing is new.

---

## ⚠️ Verification gate — model/pricing/date claims (do NOT propagate as fact until checked vs `claude-api`/official docs)

- **Deprecation date/pricing:** "Fable 5 window closes July 12, then bills at $10/M input + $50/M output — double the price of Opus [4.8]." (Matches the figure already quarantined in the alex-prompter and undefinedKi captures — still unverified, now a fourth restatement, not independent confirmation.)
- **Plan inclusion:** "Right now included in every paid plan" — unverified plan-tier claim.
- **Usage-cost anecdote:** "The full run burned a bit over 40% of my weekly Fable usage on the 20x Max plan" and, elsewhere in the same piece, "the run can eat 30% of your weekly Fable usage" (the two figures are inconsistent within the source itself — flag both as unverified, first-person, single-account anecdotes, not measured benchmarks).
- **Attribution claims:** credits "u/oj93-rd" (idea) and "u/Rodbourn" (prompt) on r/ClaudeAI, and links a third-party GitHub repo (`github.com/tomicz/fable-5-train-opus-skills-after-it-retires`) as the prompt source — unverified provenance; the hub has not fetched or reviewed that repo's actual prompt text.
- **Outcome anecdote:** "My skills came out 30% shorter on average… one skill dropped from 210 lines to 80 with zero behavior change" — a single-author, self-reported before/after with no independent measurement.

None of these figures should be repeated in any hub rule/doc/pattern until checked against the `claude-api` skill or official Anthropic docs. This is the same posture already applied to every other Fable-5 capture in the store (`2026-06-11-codez-*`, `2026-06-11-ericosiu-*`, `2026-07-04-undefinedki-*`, `2026-07-06-avid-*`, `2026-07-06-alex-prompter-*`).

---

## What it actually describes

The play: before Fable 5 starts billing, point it at your most important repo with a specific persona framing — **"You are a distinguished fellow on this project who is retiring. Your final task: build a complete skill library so junior engineers and smaller models can carry this project forward without you."** — and let it write the skill library that cheaper models (Opus/Sonnet) will run on every future session.

A three-phase system (per the linked, unreviewed GitHub prompt):

1. **Phase 1 — discovery only, no writing.** Fable reads the README, build system, test suite, CI config, and — the piece's own emphasis — **git history**: what changed, what got reverted, what stalled on dead branches ("your repo's scar tissue"). Ends with **Fable interviewing the user**, at most 5 questions the repo can't answer itself (hardest live problem; unwritten rules; who the library is for and what they don't know; costliest past failures; what "beyond state of the art" would mean here).
2. **Phase 2 — parallel authoring.** One agent per skill, 10–16 skills total, following a taxonomy: change control (with the historical incident behind each rule), a symptom-to-triage debugging playbook, "failure archaeology" mined from git history (dead ends/reverts so nobody re-fights a settled fight), an architecture contract (decisions + known weak points), and operational runbooks (build/run/config/validate/docs). An "advanced" skill is a decision-gated campaign for the project's single hardest live problem — numbered phases, exact commands, expected observations per gate, wrong paths explicitly fenced off. Every skill states when NOT to use it.
3. **Phase 3 — Fable reviews its own output.** Three parallel reviewers check for factual errors/contradictions/usability, then a fixer applies corrections; the run ends with an inventory of what was spot-checked vs. still uncertain.

Aftercare the author insists on: **review the judgment calls** (Fable encodes opinions the user may disagree with), and **prune without mercy** (delete non-load-bearing skills — "a bloated library makes every future session dumber"). A second, smaller move: point Fable at an *existing* skill library with "Read every skill, optimize each for brevity and correctness without changing behavior, show me a diff per skill" — the author reports it un-bloated their own library (see verification gate). Explicit caveat in the piece itself: **"a skill library transfers process, not intelligence"** — no one is getting Fable's reasoning in a cheaper model through one file.

---

## Relevance to this hub — MODERATE (a concrete git-history-driven authoring recipe; mostly corroboration of things already captured/practiced)

| Piece element | Existing hub analogue |
|---|---|
| "Model was never the asset, portable process is" / assets-vs-conversations framing, same July-12 clock | Same thesis, same date, already captured verbatim in [Alex Prompter's clone-Fable-into-Opus note](2026-07-06-alex-prompter-clone-fable5-into-opus.md) — **no new ground here**, a third-party restatement |
| Retiring-senior-engineer persona → produce a skill library for cheaper models to run | `model-routing.md` (cheapest-sufficient dispatch; escalate a frontier model to author a durable asset, run cheap afterward) + the hub's own `/writing-skills` skill-authoring workflow |
| Phase 1 discovery mining **git history** for "failure archaeology" / reverted dead ends | Not directly codified anywhere in the hub today — `.claude/tasks/lessons.md` captures correction patterns going forward, but nothing currently mines *past* git history for dead-end reverts as a skill-authoring input. This is the one piece of the recipe with no existing hub analogue. |
| Phase 1 interview: 5 questions before writing (hardest problem, unwritten rules, audience, past failures, target bar) | Loosely maps to `/brainstorm`'s Socratic requirements-gathering and the BA-discovery checklist, but those are pre-build discovery tools, not a skill-*generation* interview — adjacent, not identical |
| Phase 3: 3 reviewers + fixer QAs the skill set before handoff | `independent-test-verification.md` / maker≠checker, and `/skill-evaluator`'s full evaluation mode — same principle (author ≠ grader), already the hub's default posture for any new skill |
| "Prune without mercy… bloated library makes every session dumber" / 30%-shorter re-optimization pass | Directly corroborates the hub's own writing-skills quality bar and the "fewer skills loaded, not more" discipline already noted from the author's companion article (cited inline, not separately captured) |
| "Trap-test"-style claim that a skill transfers *process not intelligence* | Same caution as the trap-test verification idea in the [Alex Prompter note](2026-07-06-alex-prompter-clone-fable5-into-opus.md) — reasoning can be captured, model capability cannot |

**What's genuinely new, gated on verification:** the specific idea of mining **git history** (reverted branches, stalled changes) as a first-class input to skill/lesson authoring — an angle not present in `writing-skills.md`, `lessons.md`, or any prior Fable capture. **Action (low priority, no urgency before July 12):** if this thesis is later revisited, consider whether `/writing-skills` or `/self-improve` should add "scan git log for reverted/abandoned work on this area" as an optional discovery input when authoring a skill for a mature codebase — but this is a nice-to-have idea harvested from an unverified third-party prompt, not something to adopt sight-unseen. **No other action** — the rest of the piece (persona framing, asset/conversation split, prune-don't-bloat, review-before-trust) is corroboration already on record via the Alex Prompter and undefinedKi captures, and the pricing/date/usage-percentage claims stay quarantined per the verification gate above.

**Cross-links:** [Alex Prompter — clone Fable 5 into Opus 4.8](2026-07-06-alex-prompter-clone-fable5-into-opus.md) (same thesis, same clock, the system-prompt-transplant variant of this exact play); [undefinedKi — build anything with Fable 5](2026-07-04-undefinedki-build-anything-with-fable5.md) (workflow doctrine + refusal-fallback corroboration, same pricing claim); [Eric Siu — Fable 5 Revenue Playbook](2026-06-11-ericosiu-fable5-revenue-playbook.md) (same Mythos/pricing quarantine posture); [Avid — Agentic OS in 8 builds](2026-07-06-avid-agentic-os-fable5-8-builds.md) and [Codez — self-improving Fable 5](2026-06-11-codez-self-improving-fable5-14-steps.md) (refusal-fallback mechanism, same verification doctrine).
