Source: https://x.com/undefinedKi/status/2073422824299978929
Captured: 2026-07-08

# undefinedKi — "How To Build Anything With Claude Fable 5" (usage guide)

**Author:** undefinedKi ([@undefinedKi](https://x.com/undefinedKi))
**Posted:** 2026-07-04 · **Engagement at capture:** 190 likes, 22 RTs, 30 replies, 428k views
**Format:** Single long-form X-native article (~9k chars).
**Nature:** **Fable-5 usage/how-to guide.** Dense with **model-specific claims (pricing, benchmarks, capabilities) — verification block below.** Notable because it is the **third independent source** to describe the Fable **refusal→Opus-fallback** mechanism (after Avid and Codez), and it carries strong `model-routing.md` corroboration.

---

## ⚠️ Verification gate — model claims (do NOT propagate as fact until checked vs `claude-api`/official docs)

- **Pricing:** "$10/M input, $50/M output — exactly double Opus 4.8"; Sonnet 5 "~5x cheaper."
- **Tier framing:** "Mythos is a new tier above Opus; Fable 5 = public safety-tuned, Mythos 5 = less-restricted, gov/vetted-cyber only; same model."
- **Benchmarks:** "SWE-bench Verified 95% (self-reported), leads Cognition FrontierCode."
- **Specs:** "1M-token context, up to 128k output tokens/request."
- **Headline anecdote:** "Stripe migration across 50M lines, est. 2 months by hand, finished in a single day." **Treat as marketing anecdote — unverified.**
- **Timeline:** "dropped June 9, pulled worldwide 3 days later by an export-control order, back July 1 unchanged"; "included up to 50% of weekly Pro/Max/Team limits until July 7, then paid credits; free plan gets no Fable"; "30-day data retention, no zero-retention option."

Some *non-controversial* facts here ARE corroborated by this session's own environment context — the `claude-fable-5` model string, Fable 5 being a real current public model, and `/model` switching all exist. The **pricing / benchmark / Stripe / retention** specifics are the ones to **verify before any hub doc repeats them.**

---

## The usable workflow doctrine (this is the hub-relevant part)

The article's core "how to actually use it" workflow is **a near-verbatim restatement of `model-routing.md`** plus a concrete escalation recipe:

1. **Plan with a cheaper model first** — don't burn $50/M tokens on planning; have Opus 4.8 / Sonnet write a detailed spec (goal, constraints, stack, file structure, edge cases, definition of done) "specific enough that the agent never has to guess."
2. **Hand the full plan + codebase + docs to Fable at once** — "the 1M window is the point: Fable performs best seeing everything up front instead of discovering context mid-task."
3. **Use `/goal` to run until a verifiable condition** ("all tests pass, lint clean, builds with no errors") — **"a separate model checks the condition, so the agent that wrote the code isn't the one grading it."**
4. **Review the output, not the process** — "if you're steering every step, the task was too small for Fable or the plan too vague."

**Token-discipline settings:** (a) **prompt caching** (90% off cached input; stable block first, changing part last); (b) **effort parameter down for mechanical stages** (renames/formatting/boilerplate), max effort only for hard reasoning — "you're paying for thinking, spend it where thinking matters"; (c) **refusal fallback** (below); (d) **CLAUDE.md for conventions** so Fable doesn't re-learn them every session ("every instruction you stop repeating is tokens you stop paying for").

**The refusal mechanism (3rd independent corroboration):** Fable's tightened safety classifier flags more borderline requests (debugging, security research, vuln work). A refusal returns as **a normal response with `stop_reason: "refusal"` (NOT an error), naming which classifier fired**; **rerouted/refused requests aren't billed at Fable prices.** Recommended: wire a fallback that retries on Opus 4.8.

---

## Relevance to this hub — MODERATE (workflow doctrine = model-routing corroboration; one action gated on verification)

The *workflow* content is high-quality corroboration; the *model claims* are quarantined. Map:

| undefinedKi element | Existing hub analogue |
|---|---|
| Plan-with-cheap-model → execute-with-expensive-model; effort down for mechanical | `model-routing.md` "cheapest sufficient model per dispatch" + escalate-one-tier — **verbatim agreement, with a concrete recipe** |
| `/goal` + **separate model grades the code it didn't write** | `independent-test-verification.md` maker≠checker; [ClaudeDevs `/goal` evaluator](2026-07-06-claudedevs-getting-started-with-loops.md) |
| Review output not process; flag ambiguity don't guess | `supervisor-verification.md`; `decision-authority.md` intent gate |
| CLAUDE.md for conventions (token savings) | the hub's CLAUDE.md auto-load |
| Prompt caching (stable-first ordering) | already load-bearing in the hub's tooling (5-min cache-window discipline) |

**The one genuine action — the refusal→Opus fallback doctrine (now flagged by THREE sources: this, [Avid](2026-07-06-avid-agentic-os-fable5-8-builds.md), [Codez](2026-06-11-codez-self-improving-fable5-14-steps.md)):** three independent captures now describe the same mechanism — a Fable refusal comes back as `stop_reason:"refusal"` (a success-shaped response, not an exit-code error), so a naive pipeline that checks exit codes silently ships a non-answer. **The triple corroboration raises this from "one influencer's claim" to "worth verifying and, if real, codifying."** Action: **verify `stop_reason:"refusal"` behavior against the `claude-api` skill / official docs FIRST**, then — if confirmed — add a fallback-on-refusal rule to `model-routing.md` (Fable/Mythos dispatch → detect refusal → reroute to Opus 4.8, not treat as failure). This is already the #2 item in the Avid pending block; **this capture strengthens the case for prioritizing that verification.** Do NOT encode until verified.

**Everything else** is corroboration (workflow) or quarantined vendor claims (pricing/benchmarks/Stripe/retention) — no other action. **Cross-links:** [Avid Agentic OS](2026-07-06-avid-agentic-os-fable5-8-builds.md) + [Codez self-improving](2026-06-11-codez-self-improving-fable5-14-steps.md) (same refusal-fallback flag + Fable-verification posture); [ericosiu Revenue Playbook](2026-06-11-ericosiu-fable5-revenue-playbook.md) (same Mythos/tier framing); [ClaudeDevs loop taxonomy](2026-07-06-claudedevs-getting-started-with-loops.md) (`/goal` primitive).
