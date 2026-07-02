Source: https://x.com/sairahul1/status/2072258045460226373
Article: X-native long-form article — "20 Loop Design Patterns Every AI Engineer Should Know"
Author: Rahul (@sairahul1)
Posted: 2026-07-01
Captured: 2026-07-01
Capture method: twitter-x skill STEP 1 → Option A (ADHX API) returned the complete `article.content` (11,236 chars) — verified-complete, not reconstructed
Media: 13 hand-drawn illustrative diagrams saved under ./img/sairahul-20loops-01..13.jpg. They RESTATE the prose (no unique info beyond it); two spot-checked and OCR'd inline below (the old-vs-new-loop cover and the unifying Act→Observe→Evaluate→Adjust map). The prose is authoritative and self-contained without them.
Engagement at capture: 57 likes · 9 retweets · 8 replies · 19,502 views (fresh — captured ~day of posting)
Relevance to this hub: **HIGH — the single most on-point external source for the hub's `loop-engineering` doctrine.** It's a taxonomy of 20 named loop patterns across 5 categories, and ~all 20 map onto patterns THIS hub already ships (multi-critic ≈ five-advisors, adversarial ≈ grill-me, reflexion/error-library ≈ lessons.md + post-failure-capture, judge-ensemble ≈ quality-gate-evaluator, memory-compression ≈ compaction-handoff, workflow-optimization ≈ trust-score self-improvement). Value = a **naming + coverage map**: it gives the hub a shared vocabulary and a checklist to see which loop patterns are covered vs. missing. Companion to [[2026-06-30-andrew-ng-3-product-development-loops]] (nested outer loops), [[2026-karpathy-loops-md-field-notes]] (loop mechanics), [[2026-06-13-claude-loops-while-you-sleep]] (unattended cron loops).

# Rahul (@sairahul1) — "20 Loop Design Patterns Every AI Engineer Should Know"

## Thesis
"An agent is a worker. A loop is what makes the worker improve." The most capable production AI
systems are not single model calls — they are **loops**: Generate → Evaluate → Learn → Improve,
repeated until the output is good. Teams shipping production AI aren't writing better prompts;
they're building better loops. The article catalogs 20 recurring loop patterns in 5 categories.

**Old way:** Prompt → Response → Done. **New way:** Generate → Critique → Rewrite → Score → Retry
→ Remember → Improve. (Cover diagram `img/sairahul-20loops-01.jpg`: "OLD WAY — single call: one
shot, no improvement" vs "NEW WAY — loop: Generate→Evaluate→Learn→Improve, gets better every cycle";
captioned "this gap is worth six figures.")

## CATEGORY 1 — Quality-improvement loops (make output better before it leaves)
1. **Generate → Critique → Rewrite** — generator produces, a *separate* critic reviews, generator rewrites to feedback, repeat until a quality threshold is met. Core insight: the generator is not the best judge of its own output. (writing, code review, reports, strategy docs)
2. **Score-and-Retry** — `score = evaluate(output)`; retry if below threshold. Best when quality is measurable (extraction accuracy, format compliance, factual correctness). Generator doesn't know it's graded; evaluator does — that separation is the pattern.
3. **Multi-Critic** — four independent critics (correctness / style / safety / domain); output must satisfy ALL before exit. (medical, legal, financial, regulated content)
4. **Adversarial Critique** — the critic's only job is to *break* the answer (what assumptions fail? what evidence is missing? where is it confidently wrong?); generator defends or rewrites; best answer survives the attack. (research synthesis, investment thesis, risk analysis)
5. **Judge Ensemble** — run output through multiple evaluators, aggregate scores, only high-consensus outputs advance. (unreliable single-model eval, high stakes)

## CATEGORY 2 — Memory loops (learn from what happened)
6. **Reflexion** — agent fails → analyzes *why* → stores the lesson → retries with that lesson in context. "The difference between a system that fails once and a system that only fails once."
7. **Memory Update** — after every task store {decision made, outcome, what to do differently}; future runs inherit it. The month-6 system has read 6 months of its own history.
8. **Error Library** — store every failure; before a new task, search the library first and apply the known fix. Stops repeating the same mistake. ("Most underused pattern in production AI.")
9. **Success Pattern** — store *successes* too (approach, context, what made it work); retrieve when facing similar tasks. Learn from wins, not just mistakes.
10. **Memory Compression** — after N items accumulate, compress many specific memories → fewer higher-level abstractions. Unlimited memory is unusable memory.

## CATEGORY 3 — Planning loops (adapt when reality changes)
11. **Plan → Execute → Replan** — create plan → execute step → observe → update plan → continue. Not a waterfall, a spiral; each lap tightens the approach. The common mistake is treating the plan as fixed.
12. **Dynamic Workflow** — pipeline shape changes at runtime on results (if A→branch X, if B→branch Y, if C→skip to step 5). (multi-doc research, support routing)
13. **Goal Decomposition** — recursively break goal → subgoals → tasks → steps until each unit is executable in one call.
14. **Progress Evaluation** — every N steps, stop and ask "are we actually getting closer?"; if no, change strategy/tools/plan. System monitors its own progress. (long-running research/debugging agents)
15. **Constraint Satisfaction** — keep running until *all* constraints/business rules pass; output isn't done until every rule passes.

## CATEGORY 4 — Exploration loops (find the best answer by trying many paths)
16. **Branch-and-Explore** — explore several paths simultaneously, compare, keep the best, discard the rest. (content variations, architecture decisions, debugging hypotheses)
17. **Tree Search** — Branch-and-Explore taken arbitrarily deep: expand promising nodes, prune weak ones, until solved. Expensive but finds solutions single-pass calls can't.
18. **Debate** — two agents argue opposite positions; each round challenges assumptions and demands evidence; the answer emerges through disagreement, not agreement.

## CATEGORY 5 — System-optimization loops (the loop improves the loop)
19. **Prompt Optimization** — system runs a prompt on a test set → scores outputs → finds where it fails → rewrites the prompt → reruns. The prompt improves automatically, no human touching it. "The best prompts in production were not written by a human — they were evolved."
20. **Workflow Optimization** — system measures its own latency/cost/quality and *modifies its own workflow* (too slow → parallelize; too expensive → swap in a smaller model where quality holds; quality dropping → add a critic). "Where truly self-improving systems begin — systems that redesign themselves."

## The pattern behind all 20 (unifying map — `img/sairahul-20loops-13.jpg`)
Every loop shares one structure: **Act → Observe → Evaluate → Adjust.** (The diagram places ACT/
OBSERVE/EVALUATE/ADJUST in a ring with the 5 categories — Exploration, Quality, Memory, Planning —
feeding in; caption: "20 patterns. One structure.") The output is never final on the first attempt;
it's a starting point, and the loop turns it into something production-worthy.

---

## Mapping to THIS hub (capture-time analysis — not yet an action)
| # | Pattern | Hub equivalent (already shipped) |
|---|---|---|
| 1 | Generate→Critique→Rewrite | `development-loop` / `fix-loop`; supervisor-verification (doer vs independent reviewer) |
| 2 | Score-and-Retry | `quality-gate-evaluator-agent`; workflow gate expressions |
| 3 | Multi-Critic | `five-advisors` (5 independent lenses); code-review dimensions |
| 4 | Adversarial Critique | `grill-me` / `grill-with-docs`; adversarial-verify in Workflow tool |
| 5 | Judge Ensemble | `five-advisors` peer-review + synthesis; blind-reviewer in prompt-auto-enhance |
| 6 | Reflexion | `lessons.md` (mistake→root-cause→rule); `learning-self-improvement` |
| 7 | Memory Update | auto-memory; `.remember/`; `/end-session` checkpoints |
| 8 | Error Library | `post-failure-capture.sh`; `lessons.md` |
| 9 | Success Pattern | the synthesize flywheel (promote what works to `core/`) |
| 10 | Memory Compression | `compaction-handoff.sh`; rolling-summary in context-management rule |
| 11 | Plan→Execute→Replan | `writing-plans`/`executing-plans`; plan-before-coding rule |
| 13 | Goal Decomposition | `goals.yml` G0–G6 + DoD proxies; project-manager-agent decomposition |
| 14 | Progress Evaluation | Atlas Goal Pulse; trust-score graduation checks |
| 18 | Debate | agent-teams `--team` modes (peers challenge mid-flight) |
| 19 | Prompt Optimization | `prompt-auto-enhance` (grade→diagnose→strengthen→blind-review) |
| 20 | Workflow Optimization | trust-score walk-phase; loop-engineering self-* meta-loop |

**Takeaways:**
- **Strong corroboration** that the hub's architecture already implements the leading edge of loop design — most of the 20 have a named hub home. Low novelty on individual patterns, high value as a **coverage checklist + shared vocabulary**.
- **Genuine gaps worth checking** (candidates, not decisions): **#12 Dynamic Workflow** (runtime-branching pipeline shape) and **#17 Tree Search** (depth-unbounded exploration) are the two least-covered — the hub's workflows are mostly fixed DAGs (`workflow-contracts.yaml`) and flat fan-out, not runtime-adaptive or tree-searching. **#9 Success Pattern** storage is implicit in the flywheel but not an explicit "store what worked" step in `lessons.md`.

## Deferred improvement-pass items (nothing acted on here, per the store's rule)
1. **Vocabulary alignment** — consider adding this 20-pattern taxonomy (or a link to this note) as a shared-vocabulary reference in `docs/specs/loop-engineering-spec.md`, so hub loop patterns can be named against an industry-recognizable set.
2. **Coverage-gap evaluation** — assess whether **Dynamic Workflow (#12)** and **Tree Search (#17)** are worth adding to the workflow toolkit, or are deliberately-YAGNI omissions; record the decision either way.
3. **Explicit success-capture** — evaluate adding a "what made this work" success-pattern line to the `lessons.md` / learning-self-improvement flow (currently failure-biased), matching pattern #9.
