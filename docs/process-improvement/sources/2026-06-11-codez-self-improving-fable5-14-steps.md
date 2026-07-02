Source: https://x.com/0xCodez/status/2065089060104720776
Article: X-native long-form article — "Build self-improving agent system with Fable 5 in 14 steps: loops, dynamic workflows, routines"
Author: Codez (@0xCodez) · Substack: https://movez.substack.com/
Posted: 2026-06-11
Captured: 2026-07-02
Capture method: twitter-x skill STEP 1 → Option A (ADHX API) returned the complete `article.content` (24,373 chars) — verified-complete, not reconstructed
Media: 11 diagrams/charts saved under ./img/codez-fable5-01..11.(jpg|png). Two OCR'd inline (the 4-layer "compound stack" architecture = codez-fable5-02.png; the "FrontierCode accuracy-vs-cost" benchmark = codez-fable5-05.jpg). Prose is authoritative and self-contained without the rest.
Engagement at capture: 1,204 likes · 146 retweets · 36 replies · 1,619,133 views
Relevance to this hub: **VERY HIGH — the closest external mirror of what THIS hub IS.** It's a 14-step blueprint for a "self-improving agent SYSTEM" whose entire thesis — "self-improvement is a property of the system you build around a stateless model, not the model itself" — is the hub's own north-star (G5). Nearly every step maps to a shipped hub pattern (verifier sub-agent, state file, skills-that-compound, worktrees, dynamic workflows, routines, model-routing, vision-verify). Companion to [[2026-07-01-sairahul-20-loop-design-patterns]] (loop taxonomy), [[2026-06-30-andrew-ng-3-product-development-loops]] (nested outer loops), [[2026-karpathy-loops-md-field-notes]], [[2026-06-13-claude-loops-while-you-sleep]].

## ⚠️ VERIFICATION CAVEAT (read before citing any fact from this note)
This article asserts many **specific, load-bearing factual claims** about Claude "Fable 5" that
this capture has **NOT independently verified** — treat them as *the author's claims*, not
hub-established fact, and cross-check against the `claude-api` skill / official Anthropic docs
before repeating any of them:
- Fable 5 = "first publicly available **Mythos-class** model," launched **June 9, 2026**, one tier
  above Opus; pricing **$10/M input · $50/M output**.
- A "**Mythos Preview**" via "**Project Glasswing**"; "**Mythos 5**" without classifiers is Glasswing-only.
- Experiments named "**Parameter Golf**" (8h on 8×H100; Fable 5 ~6× Opus 4.7) and "**Continual
  Learning Bench 1.0**" (Fable 5 73% verification coverage vs Opus 4.7 ~17%).
- A "**319-page system card**" with buried downgrade behaviors; auto-fallback to Opus 4.8 on
  cyber/bio/chem/distillation classifier blocks.
- Product names: **/goal**, **Outcomes**, **Claude Managed Agents (CMA)**, **Routines** (launched
  Apr 14 2026), **Dynamic Workflows** (launched May 28 2026).
Some of these are plausible (Fable 5 exists as a model id `claude-fable-5`; Dynamic Workflows exist),
but dates, benchmark numbers, codenames, and the system-card page count are **unconfirmed** and some
read as marketing synthesis. The *architectural patterns* below are the durable, hub-relevant takeaway
regardless of whether every Fable-5 specific is accurate. **Unverified:** all model-specific numerics.

# Codez (@0xCodez) — "Build a Self-Improving Agent System with Fable 5 in 14 Steps"

## Thesis
"9 out of 10 users have never run an agent system that **compounds** — where every run leaves the
next run smarter, every state file accumulates, every skill sharpens." The model is stateless; the
**system around it** is what compounds. Three tiers: what the model unlocks → three primitives
(loops, dynamic workflows, routines) → the self-improvement layer.

## PART 1 — What the model unlocks
- **01. Days-long autonomy** is the headline (planning across stages, delegating to sub-agents, checking its own work) inside a harness (Claude Code / CMA).
- **02. Self-improving ≠ self-learning.** *Self-learning* = the model updates its own weights (no production model does this; RSI is a warned-about direction, not shipping). *Self-improving* = the environment compounds: each session writes lessons to memory, skills sharpen, state files accumulate verified facts, eval loops refine prompts/rubrics. Quoted Anthropic engineering guidance: *"Rather than directly prompting and steering … it's often better to design loops that let the model self-correct in response to environment feedback (e.g., /goal or Outcomes) and manage its own context (e.g., via memory)."*
- **03. The compound stack — 4 layers, one feedback loop** (OCR of `img/codez-fable5-02.png`):
  - **Layer 1 · Primitives** — the model, sub-agents, worktrees, tools. Raw capability. (What most people use today.)
  - **Layer 2 · Orchestration** — /goal & Outcomes (self-correcting loops), Dynamic Workflows, Routines.
  - **Layer 3 · Memory** — state file, Skills, Knowledge Bases, lessons. "What the agent forgets, the repo remembers."
  - **Layer 4 · Self-improvement** — vision self-check, eval loops, rule distillation. "Agent grades its own output, refines skills, writes rules back to memory."
  - Every layer-1 output flows up to layer 4, gets graded/distilled, and is written back to layer 3; tomorrow's layer-1 run inherits it.
- **04. Cost-capability routing** (benchmark chart `img/codez-fable5-05.jpg` — "FrontierCode: Accuracy vs Cost", Fable 5 > Opus 4.8 > GPT-5.5 across effort tiers low→max): orchestrator on the top tier, hard-bounded subtasks on Opus 4.8, high-volume workers on Sonnet 4.6, **graders on Haiku 4.5** (independent context, cheap — the verifier role). Route by task complexity, not by default.

## PART 2 — The three primitives
- **05. /goal vs Outcomes** — same shape (independent grader checks work; not-met → next iteration; exit on pass). `/goal` = in-session Claude Code loop with a measurable end state; `Outcomes` = CMA, hours/days on hosted infra, file-based rubric + sub-agent grader + hard `max_iterations`.
- **06. Verifier sub-agent beats self-critique** — *"a verifier sub-agent tends to outperform self-critique."* Structural, not effort: a model grading its own output sees its own reasoning trail and prefers conclusions consistent with what it wrote; a separate model sees only the artifact + rubric. **This is the hub's supervisor-verification / independent-test-verification doctrine, stated identically.**
- **07. Dynamic Workflows** (Claude writes its own JS harness with `agent()`, `parallel()`, `pipeline()`). Three of six patterns matter for self-improvement: **fan-out-and-synthesize**, **adversarial verification** (per-task independent verifier), **loop-until-done** (pair with /goal). The other two: classify-and-act (model routing) and tournament (taste ranking).
- **08. Worktrees for parallel safety** — the moment >1 agent runs, files collide; a git worktree gives each a separate checkout on its own branch. Maker in worktree A, verifier reads B; parallel experiments each in their own worktree; failed phase doesn't poison the rest. Exposed as `git worktree`, a `--worktree` flag, and `isolation: worktree` on subagents.
- **09. Routines for days-long orchestration** (laptop closed, cloud infra, trigger-fired). Three trigger→pattern maps: **schedule** = morning-briefing (re-run eval suite, distill failures into Skills, digest to Slack while you sleep); **API** = fire-on-event (CI fails → investigate; Sentry → triage); **GitHub event** = learn-from-real-work (on PR open, eval against latest Skills; on merge, write new patterns back to the Skill).

## PART 3 — The self-improvement layer
- **10. The 5-stage memory progression** (from "Continual Learning Bench"): **Fail → Investigate → Verify → Distill → Consult.** Weaker models exit early (just log failures); the strongest completes the progression (distills verified facts into general rules and consults them next time). **= the hub's `lessons.md` mistake→root-cause→rule discipline, formalized as a 5-stage ladder.**
- **11. The state file** — where each stage's output lives (mounted FS in CMA; a markdown file or Linear board locally). Five sections matching the five stages (verified facts / general rules / open failures / lessons learned / last-session resume pointer). Two operational rules: **write before walking away** (session ends by updating STATE.md) and **read at session start**. = the hub's `.remember/` + `/end-session`+`/continue` + auto-memory.
- **12. Skills that compound** — write the lesson into the **Skill**, not just the chat. STATE.md is project-scoped and dies with the project; Skills live in `~/.claude/skills/` and travel. A skill compounding for two weeks grows "known failure modes / anti-patterns / post-mortem rules" sections. = exactly the hub's skill-authoring + `writing-skills` + rule-curation philosophy.
- **13. Self-verification via vision** — maker writes UI + renders screenshot; verifier reads the screenshot with vision, compares against goal + design tokens + previous screenshot; verdict returns to the loop. = the hub's `web-deploy-readiness` visual-responsive-verification + `feedback_responsive_visual_verification` (screenshots at breakpoints).
- **14. The safety boundary** — built-in classifiers decline cyber/bio/chem/distillation, auto-falling back to Opus 4.8. Design for it: route blocked tasks explicitly, surface to a human, make Skills document which tasks may hit the classifier; a loop that silently fails on a block looks like a real error. Audit the system card before production.

## The mistakes that keep it at 10% of potential (§)
Using it like a bigger-context chat; self-critique instead of an independent verifier; no STATE.md
(every session restarts from zero — "70%+ of the memory advantage disappears"); Skills that never
get written to; top-tier model on tasks a cheaper tier handles; long sessions on a laptop; ignoring
the safety boundary; no vision-verify on visual tasks; skipping /goal-or-Outcomes objective stop
conditions; no data-retention policy review.

---

## Mapping to THIS hub (capture-time analysis — not yet an action)
| Article step | Hub equivalent (already shipped) |
|---|---|
| 02 self-improving = system property | G5 north-star; `loop-engineering`; trust-score walk-phase |
| 03 compound stack (4 layers) | primitives→workflows→memory→self-improve — the hub's own layering |
| 04 model routing by complexity | `agent-team-selection.md`; agent-orchestration cheapest-sufficient rule |
| 06 verifier > self-critique | `supervisor-verification.md` + `independent-test-verification.md` + blind reviewer |
| 07 dynamic workflows (fan-out / adversarial / loop-until-done) | the Workflow tool patterns; `five-advisors`; loop-until-dry |
| 08 worktrees | `using-git-worktrees`; `isolation: worktree`; git-branch-lifecycle `work` |
| 09 routines (schedule/API/GitHub triggers) | scheduled CI (`scan-*.yml`, `aggregate-telemetry.yml`); `/schedule`, `/loop` |
| 10 5-stage memory (Fail→…→Consult) | `lessons.md`; `learning-self-improvement`; `post-failure-capture.sh` |
| 11 state file (write-before-walk / read-at-start) | `.remember/`; `/end-session`+`/continue`; compaction-handoff |
| 12 skills that compound | skill-authoring, `writing-skills`, rule-curation |
| 13 vision self-verify | `web-deploy-readiness` visual verification; responsive-screenshot rule |
| 14 safety-boundary fallback | (partial) — no explicit classifier-block fallback doctrine in hub rules |

**Takeaways:**
- **Strongest single validation yet** that the hub's architecture *is* a self-improving system in the exact sense a 1.6M-view industry piece describes. Most of the 14 steps have a named hub home — high-confidence corroboration.
- **Genuine gaps worth checking** (candidates, not decisions): **step 14** (explicit safety-classifier-block fallback: route to a different model / surface to human, and have Skills document which tasks may hit it) has **no** current hub-rule analogue; and **step 04's model-tier routing** (orchestrator/worker/grader on specific model tiers) is done ad-hoc in the hub, not codified as a routing table.
- Reinforces the two gaps flagged from [[2026-07-01-sairahul-20-loop-design-patterns]] — this article treats **Dynamic Workflows** and **Routines** as first-class primitives, suggesting the hub's lighter coverage of runtime-branching workflows is a real (if deliberate) delta.

## Deferred improvement-pass items (nothing acted on here, per the store's rule)
1. **Safety-boundary fallback doctrine** — evaluate a hub rule (or an addition to `decision-authority.md` / a new pattern) for handling model safety-classifier blocks: explicit model fallback, human surfacing, and Skills documenting which tasks may trigger it — so an autonomous loop doesn't silently mistake a policy block for a code error.
2. **Model-tier routing table** — assess codifying an orchestrator/worker/grader → model-tier routing table (Fable/Opus/Sonnet/Haiku) in `agent-team-selection.md` or `engineering-roles.md`, vs keeping it ad-hoc.
3. **5-stage memory framing** — consider aligning `lessons.md` / learning-self-improvement to the explicit **Fail→Investigate→Verify→Distill→Consult** ladder (adds "Verify" + "Consult" as named steps).
4. **VERIFY the Fable-5 factual claims** — before any of this article's model-specific facts (pricing, Mythos/Glasswing, benchmark numbers, system-card size) are repeated anywhere in the hub, confirm against the `claude-api` skill / official docs. Do NOT propagate unverified.
