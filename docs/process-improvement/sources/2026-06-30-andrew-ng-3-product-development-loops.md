Source: https://x.com/AndrewYNg/status/2071988145667928442
Author: Andrew Ng (@AndrewYNg)
Posted: 2026-06-30 (originally published in *The Batch*)
Captured: 2026-07-01
Capture method: ADHX API (twitter-x skill Option A) returned the complete post `text` (verified-complete, not reconstructed); diagram cross-checked via fxtwitter and OCR'd by vision
Media: 1 image saved under ./img/andrew-ng-3-loops.jpg (the "3 key product development loops" figure)
Engagement at capture: 6,058 likes · 1,120 retweets · 236 replies · 346,940 views
Relevance to this hub: directly reinforces the hub's `loop-engineering` workflow (`docs/specs/loop-engineering-spec.md`, `core/.claude/skills/loop-engineering/SKILL.md`) and the human-in-the-loop / design-gate doctrine. Third loop-engineering source in this store, alongside [[2026-karpathy-loops-md-field-notes]] (agent-internal loop mechanics) and [[2026-06-13-claude-loops-while-you-sleep]] (unattended cron loops). Where those two are about the *inner* engineering loop, Ng's contribution is the **nested-loop hierarchy at three timescales** — it names the outer loops (developer-feedback, external-feedback) the hub already half-encodes as its design gate and dogfood/telemetry flywheel.

# Andrew Ng — The 3 Key Product Development Loops (for 0-to-1 products)

## Thesis
"Loop engineering" went viral after Boris Cherny (Claude Code's creator) and Peter Steinberger
(OpenClaw's creator) surfaced it. Loops are now central to getting AI agents to iterate at length
to build software. Ng shares his **3 key loops for building 0-to-1 products** — a framework that
guides not just *how* he builds software but *what* software he decides to build. The loops are
**nested and run at escalating timescales**: an inner fast loop wrapped by progressively slower
human-and-market feedback loops.

## The diagram (`img/andrew-ng-3-loops.jpg`)
Three chained circular loops, left to right, each labeled with its cadence:

| Loop | Cycles between | Cadence |
|---|---|---|
| **Agentic Coding Loop** | Coding agent ⇄ Product spec / evals | **~minutes** |
| **Developer Feedback Loop** | Product spec / evals ⇄ Developer vision | **~hours** |
| **External Feedback Loop** | Developer vision ⇄ External feedback | **~days** |

The output of the inner loop becomes the input the next loop out steers on: the coding agent
produces an implementation → the developer reviews it and refines the spec/vision → external
feedback reshapes the vision → which re-drives the spec → which re-drives the coding agent.

## Loop 1 — Agentic coding loop (~minutes)
Given a product specification (and optionally a set of **evals** — a dataset to measure performance
against), an AI agent writes code, tests its own work, and iterates until the code is bug-free and
meets spec. Closing this loop took off around late last year and has been a game changer: agents now
work productively for long stretches without human intervention. Ng's example — over a weekend he
built a typing-practice app for his daughter and the coding agent worked ~an hour on its own, using
a **web browser to check what it had built multiple times** before reporting back. The loop executes
fast: every few minutes the agent may build and test a new version. Finding more effective
engineering loops is "an active area of invention."

## Loop 2 — Developer feedback loop (~tens of minutes to hours)
The developer examines the current product and steers the agent to improve it. Last year developers
(Ng included) were the **QA function** — manually finding bugs and asking the agent to fix them. Now
that agents test their own code, that burden has dropped sharply, freeing developers for
**higher-level product decisions**: which features to offer, where the UI needs work, etc. Even with
a clear vision, translating vision → spec is real work; after seeing an implementation the developer
often **updates/clarifies the spec** to steer it. If the system repeatedly hits certain problems,
**building a set of evals** becomes worthwhile. In the typing-app example Ng changed his mind several
times on visual design, unlockable cat costumes, and the grown-up login/steering flow.

### On "taste" vs. context advantage (the human-in-the-loop justification)
AI-native teams increasingly use AI to help shape product direction (automating usage-data analysis,
summarizing customer feedback, competitive analysis). But for nearly all products Ng is involved in,
**humans hold a significant context advantage** over current AI — they know far more about the users
and the operating context. Many call this "taste"; Ng prefers "**context advantage**" because it
gives a clearer path to improving AI systems. This is *why the step can't be automated*: **so long as
the human knows something the AI does not, human-in-the-loop is needed to inject that knowledge.**

## Loop 3 — External feedback loop (~hours to days/weeks)
A wide range of tactics: asking a few friends, launching to alpha testers, or shipping to production
with A/B testing. These are slow — rarely under hours, sometimes days or weeks. This data informs the
**developer vision**, which drives the detailed **product spec**, which drives the **coding agent** —
closing the outermost loop back into the innermost.

## Closing observation — engineers becoming part-time PMs
As coding agents speed up development, more engineers are taking on a partial **product-management**
role. The hardest part for engineers growing into it: shaping the **product vision** and balancing
**building** (bridging vision → spec) against **getting user feedback to evolve the vision**. Both
matter. Ng frames it as encouraging that engineers are expanding their role — "just as product
managers and designers now do more engineering."

[Original text: *The Batch*]

---

## Why this matters to THIS hub (capture-time note — not yet an action)
- **Names the outer loops the hub already runs but hadn't formally nested.** The hub's inner
  agentic loop = `loop-engineering` + `development-loop`/`fix-loop` (build→test→iterate). Ng's
  **developer-feedback loop (~hours)** ≈ the hub's human **design gate** (only G1 design is
  human-gated; build/verify/deploy are autonomous — [[feedback_dogfood_only_design_gated]]) plus
  the supervisor-verification review. His **external-feedback loop (~days)** ≈ the hub's
  **dogfood + telemetry flywheel** (`aggregate_telemetry.py`, enrolled-repo learnings) and the
  synthesize flywheel.
- **The three cadences (minutes/hours/days) are a clean lens for the trust-score walk-phase** —
  reversible fast loops can graduate to autonomy first; the slower human/external loops are exactly
  where the hard gates and human escalation should stay. Consistent with per-stage graduation.
- **"Context advantage, not taste"** is a sharper articulation of the hub's human-in-the-loop
  doctrine — a candidate reframing for the design-gate rationale (`human-approval-gates.md`,
  `decision-authority.md` confidence gate): the gate exists *specifically where the human knows
  something the agent does not*, which is a testable criterion, not a vibe.
- **Potential improvement-pass items** (deferred to the dedicated improvement session, per this
  store's rule — nothing acted on here): (1) consider documenting the three-timescale nested-loop
  hierarchy in `loop-engineering-spec.md` so the spec explicitly covers the outer loops, not just
  the inner one; (2) evaluate reframing the design-gate justification around "context advantage."
