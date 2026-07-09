Source: https://x.com/KanikaBK/status/2074780613236887567
Captured: 2026-07-08

# Kanika (@KanikaBK) — "10 biggest mistakes people are making with Claude Fable 5"

**Author:** Kanika ([@KanikaBK](https://x.com/KanikaBK)) — "Building practical AI workflows and Obsidian systems for creators"
**Posted:** 2026-07-08 · **Engagement at capture:** 24 likes, 14 RTs, 5 replies, 59,600 views
**Format:** Single long-form X-native article (~8.4k chars).
**Nature:** **Fable-5 usage/mistakes listicle.** Anecdotal opener (a loop run "burned through thirty thousand tokens," ignored stop conditions), then 10 numbered mistakes, each with what-people-do-wrong / why-it's-worse-on-Fable-5 / fix. Lighter on hard model-capability claims than most captures in this cluster — mostly behavioral/workflow advice — but still carries a few unverified specifics flagged below.

---

## ⚠️ Verification gate — do NOT propagate as fact until checked vs `claude-api` / official docs

- The "burned through thirty thousand tokens on a single loop run" anecdote — **unverified personal anecdote**, not a benchmark.
- Implicit claim that Fable 5 is meaningfully "more agentic" than Opus/Sonnet such that identical prompts produce overreach — **unverified behavioral claim**, no measurement given.
- Links to `https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5` as the "official doc" — **not fetched/verified in this capture**; if this hub ever cites Fable-5-specific prompting guidance, fetch and cache that URL per `claude-docs-cache.md` first rather than trusting the tweet's characterization of it.
- No pricing, benchmark, or tier (Mythos) claims in this piece — narrower claim surface than the `undefinedKi` / `ericosiu` captures, so less to quarantine.

---

## The 10 mistakes (faithful summary)

1. **Reusing old Opus/Sonnet prompts unchanged** — vague prompts that were safe on older models become overreach on a more agentic model ("analyze this" turns into a full audit + rewrite + side quests). Fix: rewrite prompts to state scope, limits, and stopping rules explicitly.
2. **No stop rules or budget caps on long `/loop` runs** — the agent won't self-limit; it keeps refining until something external stops it or the bill arrives. Fix: set hard stop conditions before the run starts.
3. **No memory/context system** — treating the model as if it remembers prior sessions; scattered notes mean every run re-discovers the same information. Fix: a single context file as source of truth, loaded at the start of each session.
4. **Running everything on Fable 5 instead of a barbell strategy** — using the expensive model for summaries/formatting/small admin work. Fix: match task cost to model cost — the cheapest-sufficient model for the job.
5. **Using `/goal` and `/loop` as decorative labels** — vague goals aren't caught and corrected by the model; it just optimizes the wrong target harder. Fix: give each command a real, specific job — `/goal` defines success, `/loop` defines how far to push.
6. **Ignoring the model's clarifying questions** — steamrolling past them or answering vaguely; the model then fills gaps itself, causing expensive misunderstandings. Fix: answer clarifying questions fully and specifically.
7. **Poor skill creation/reuse** — one-off prompts instead of packaged, reusable skill files; every task re-invents the workflow from zero. Fix: create reusable skill files for repeat tasks.
8. **Not using vision capabilities** — manually describing screenshots/diagrams/dashboards instead of feeding the image directly. Fix: use images when the problem is visual.
9. **No human checkpoints on high-stakes work** — handing off a serious task and walking away; the model can be confidently wrong. Fix: add checkpoints at risky points in the workflow.
10. **Not tracking token costs until the bill arrives** — no usage monitoring during loops/long-context work. Fix: track usage proactively, especially in loops.

Closing framing: "the people who win with Fable 5 are the ones who ask better, stop cleaner, and review smarter" — treat it as an operating layer, not a smarter autocomplete.

---

## Relevance to this hub — LOW-MODERATE (broad corroboration of existing doctrine; zero net-new mechanism)

Every one of the 10 mistakes maps cleanly onto a rule this hub already enforces — this is the most thoroughly-covered-in-advance capture in the Fable-5 cluster to date. Map:

| Kanika's mistake | Existing hub analogue |
|---|---|
| #1 Stale prompts, no scope/stop rules | `plan-before-coding.md`; `decision-authority.md` (state assumptions, scope the ask) |
| #2 No budget caps on `/loop` | `loop-engineering`'s hard budgets + escalation-report on exhaustion; `config/trust-score.yml` hard gates |
| #3 No memory/context system | `context-management.md` (scratchpad, progressive disclosure); CLAUDE.md itself as the context SSOT |
| #4 Barbell strategy / right-model-for-the-job | `.claude/rules/model-routing.md` — **verbatim**: "cheapest sufficient model per dispatch," escalate one tier on failure |
| #5 `/goal`/`/loop` given a real job | `goals.yml` (host-owned goal SSOT, machine-checkable DoDs); `loop-engineering` skill's DISCOVER→PLAN→EXECUTE→VERIFY loop |
| #6 Answer clarifying questions fully | `prompt-auto-enhance.md` Clarification & Confidence Gate |
| #7 Reusable skills over one-off prompts | `writing-skills`, the entire pattern-curation model of this hub |
| #8 Use vision, don't transcribe manually | No direct hub rule (image-input is a UX behavior, not a governance gap) — no action |
| #9 Human checkpoints on high-stakes work | `supervisor-verification.md`, `human-approval-gates.md`, `independent-test-verification.md` (maker≠checker) |
| #10 Track token cost before the bill | `config/trust-score.yml` signals + `collect_signals.py`; no hub cost-telemetry gap identified here specifically |

**Net-new for the hub: none.** Unlike prior Fable-5 captures in this cluster, this piece does **not** mention the refusal→Opus-fallback mechanism (`stop_reason:"refusal"`) — so it neither adds nor strengthens that pending verify-then-codify item. It also carries no pricing/benchmark/tier claims to quarantine beyond the two flagged above. This is a plain-language restatement of `model-routing.md` + `context-management.md` + `supervisor-verification.md` for a general audience — useful as external corroboration signal (one more independent source arriving at the same operating discipline), not as a source of new rules.

**Action: none.** File for corroboration-count purposes only. Cross-links: [undefinedKi Fable guide](2026-07-04-undefinedki-build-anything-with-fable5.md) (same model-routing + `/goal` corroboration, plus the refusal-fallback mechanism this piece omits), [ericosiu Revenue Playbook](2026-06-11-ericosiu-fable5-revenue-playbook.md) (same human-review-before-delivery principle, independently re-derived here as mistake #9).
