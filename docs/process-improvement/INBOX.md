# Process-Improvement Inbox

Durable capture of documents, links, and images shared for improving this hub's processes.
**Take notes now, improve the processes later.** Each source is saved as a self-contained
note under `sources/` (full text/transcription + any images on disk), so it stays retrievable
even if the original is deleted or edited. Nothing here is acted on until the dedicated
improvement pass — this is the holding store.

How a capture is saved: one markdown note per source with `Source:` + `Captured:` headers,
the full extracted content (article text + image transcriptions, not just a link), any media
saved alongside under `sources/img/`, and a short "relevance to this hub" note.

## Captured

| Date captured | Source | Topic | Note |
|---|---|---|---|
| 2026-06-29 | Uploaded image (attr. **Andrej Karpathy**) | **"LOOPS.md: Field Notes on Agents That Run for Days"** — 9 rules for long-running agent loops (write the loop not the prompt; separate planner/generator/evaluator; contract-first; state on disk; let it restart; score taste; read traces; delete the harness; the bottleneck always moves) | [2026-karpathy-loops-md-field-notes.md](sources/2026-karpathy-loops-md-field-notes.md) |
| 2026-06-29 | [@hanakoxbt X post](https://x.com/i/status/2065807526268920103) | Claude cron **loops** that run unattended ("while you sleep") — single loop → parallel fleet → server routines; narrow-job discipline | [2026-06-13-claude-loops-while-you-sleep.md](sources/2026-06-13-claude-loops-while-you-sleep.md) |
| 2026-07-01 | [@AndrewYNg X post](https://x.com/AndrewYNg/status/2071988145667928442) | **Andrew Ng — "3 key product development loops"** (from *The Batch*): nested loops at escalating timescales — agentic coding loop (~minutes) ⊂ developer-feedback loop (~hours) ⊂ external-feedback loop (~days); "context advantage, not taste" as the human-in-the-loop justification | [2026-06-30-andrew-ng-3-product-development-loops.md](sources/2026-06-30-andrew-ng-3-product-development-loops.md) |
| 2026-07-01 | [@AnatoliKopadze X article](https://x.com/AnatoliKopadze/status/2063985608381362576) | **Anatoli Kopadze — "AI Agents… Build Your Own Step by Step"** (3.36M views): agent = **tools + memory + loop** around a model (a spectrum, not a category); build a Claude-Code→Telegram bot on a VPS; the **memory-loss problem + 4 fixes** map 1:1 onto the hub's context-management rule (external corroboration) | [2026-06-08-anatoli-kopadze-build-your-own-ai-agent.md](sources/2026-06-08-anatoli-kopadze-build-your-own-ai-agent.md) |
| 2026-07-01 | [@sairahul1 X article](https://x.com/sairahul1/status/2072258045460226373) | **Rahul — "20 Loop Design Patterns Every AI Engineer Should Know"**: taxonomy of 20 named loop patterns in 5 categories (Quality / Memory / Planning / Exploration / System-optimization), unified as **Act→Observe→Evaluate→Adjust**. ~All 20 map onto existing hub patterns — a coverage-checklist + shared vocabulary; two least-covered gaps: Dynamic-Workflow (#12) + Tree-Search (#17) | [2026-07-01-sairahul-20-loop-design-patterns.md](sources/2026-07-01-sairahul-20-loop-design-patterns.md) |

## Pending the improvement pass
- **Andrew Ng 3-loops** → (1) consider documenting the three-timescale nested-loop hierarchy in `docs/specs/loop-engineering-spec.md` so the spec covers the *outer* loops (developer-feedback, external-feedback), not just the inner agentic loop; (2) evaluate reframing the human design-gate rationale (`human-approval-gates.md` / `decision-authority.md`) around "**context advantage**" — the gate belongs specifically where the human knows something the agent does not (a testable criterion).
- **Kopadze build-your-own-agent** (low priority — mostly validates existing hub rules) → (1) consider a crisp "**tools + memory + loop**" one-line definition + the four memory-fixes cross-reference in `context-management.md` / `loop-engineering-spec.md`; (2) consider an auth-lock reminder for any user-facing bot in `notifier-integration.md` ("restrict to your account or others burn your API credits").
- **sairahul 20 loop patterns** (HIGH relevance) → (1) add the 20-pattern taxonomy (or a link to this note) as a shared-vocabulary reference in `docs/specs/loop-engineering-spec.md` so hub loops can be named against an industry-recognizable set; (2) evaluate the two least-covered gaps — **Dynamic Workflow (#12)** runtime-branching pipelines and **Tree Search (#17)** depth-unbounded exploration — as adds vs deliberate-YAGNI omissions, and record the decision; (3) evaluate adding explicit **success-pattern capture (#9)** ("what made this work") to the failure-biased `lessons.md` / learning-self-improvement flow.
