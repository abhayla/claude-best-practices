Source: https://x.com/vartekxx/status/2074864291568664646
Captured: 2026-07-08

# vartekxx — "Context Engineering: the Karpathy-Cherny method that replaced prompting"

**Author:** vartekxx ([@vartekxx](https://x.com/vartekxx))
**Posted:** 2026-07-08 · **Engagement at capture:** 36 likes, 9 RTs, 7 replies, 17,394 views
**Format:** Single long-form X-native article (~11.3k chars), image-illustrated, 5 parts.
**Nature:** **Synthesis/explainer, not primary research.** Fuses two already-viral threads — Karpathy's
"context engineering" framing and Boris Cherny's "I don't prompt, I write loops" line — into one
how-to-build-it-yourself piece with copy-paste Claude Code prompts. Attributions to Karpathy and
Cherny are **second-hand paraphrase/quote-without-link** (a Sequoia AI Ascent talk, an unlinked
Cherny statement) — attribute, don't assert as verbatim-verified. The MMLU "0.637 vs 0.488" figure
and the "2-3x from verification" figure carry **no citation, link, or methodology** anywhere in the
piece.

> ⚠️ **Unverified claims — do not cite as fact:**
> - "Same model scores 0.637 or 0.488 on MMLU depending only on context structure" — no source,
>   paper, or benchmark link given.
> - "Cherny shared a data point: giving Claude effective verification typically improves output
>   quality by 2-3x" — no link to where this was shared, no methodology.
> - The Karpathy Sequoia AI Ascent "Software 3.0" talk and the Cherny "I have loops running that
>   prompt Claude" quote are both attributed but unlinked — same underlying claims already appear
>   (also unlinked/unverified) in the two overlapping captures below, so this is the third retelling
>   of the same unsourced quotes, not independent corroboration.

## What it is

A 5-part "bookmark this" tutorial arguing prompt engineering → context engineering → loop engineering
is a 3-stage progression, each layer building on (not replacing) the last:

1. **Karpathy's framework** — "Software 3.0": humans now program models through context, not code
   (1.0) or training data (2.0). The context window is RAM; the model is the CPU. Four canonical
   operations on context: **Write** (persist outside the window — CLAUDE.md, skills, state files),
   **Select** (retrieve only what's relevant now), **Compress** (summarize stale history, prioritize
   fresh tool results), **Isolate** (give subtasks their own clean context — Cherny's "context
   firewall" for subagents). Skipping these causes "context rot" — tokens accumulate, signal-to-noise
   drops, decisions get worse, even though the window itself didn't shrink.
2. **Cherny's framework** — loop engineering is context engineering automated on repeat. Every loop
   cycle re-runs the same four operations (write state to disk, select relevant state next cycle,
   compress old runs, isolate subagents). Cherny's **5 building blocks of a working loop**:
   Automation (`/loop` cadence, `/goal` stop condition), Skill (project knowledge in markdown, read
   every run), Sub-agents (split maker from checker), Connectors (act in the real environment — PRs,
   Slack, tickets), Verifier (the gate — tests/type-checks/builds that reject bad work). "Without a
   verifier you don't have a loop, you have the agent agreeing with itself on repeat."
3. **Build-it-yourself walkthrough on Claude Code** — CLAUDE.md as the persistent context layer
   (keep under ~200 lines, "every line must be earned"), writing specs not prompts, subagent context
   isolation, Stop-hook verification gates (CLAUDE.md is ~70% followed / advisory, hooks are 100%
   enforced), a self-improving context loop (each run writes learnings, next run reads them),
   automating with `/loop` + `/goal`, promoting to cloud Routines for 24/7 operation (schedule / API
   webhook / GitHub-event triggers), and "Dynamic Workflows" — Claude writing its own orchestration
   script to fan out tens-to-hundreds of parallel subagents with zero tokens spent on coordination.
4. **The honest part** — more context isn't always better (a lean, earned 200-line CLAUDE.md beats a
   2,000-line dump); the model still hallucinates inside perfect context, so the verifier stays
   mandatory; this is a genuinely new skill (thinking about what the model needs to see, not what
   you want to say), not prompt-writing or software engineering.

Thesis line: "Prompt engineering got you the first 10%. Context engineering gets you the next 90%."

## Relevance to this hub — LOW-MODERATE (near-total overlap with two already-captured clusters; one framing worth noting, nothing actionable)

This piece is a **fusion of content the hub already captured from its two primary sources**: the
Karpathy-side "context engineering" framing was captured (with the same "Write/persist,
AGENTS.md/CLAUDE.md, memory-file" mechanics) in
[noisyb0y1's context-engineering system](2026-07-04-noisyboy-context-engineering-system.md); the
Cherny-side "5 building blocks / maker≠checker / verifier-is-the-gate / Karpathy AutoResearch" content
is **near-verbatim identical** to what
[0xCodila's Loop Engineering piece](2026-07-01-0xcodila-loop-engineering-karpathy-bilevel.md) already
captured (same 5 blocks, same "agent agreeing with itself on repeat" line, same Karpathy `autoresearch`
attribution). This article adds no new primitive on either side — it is a synthesis/remix positioned as
a single narrative arc, written for a broader audience than either source article.

| Article concept | Existing hub implementation / prior capture |
|---|---|
| Software 3.0 / context window as RAM | Framing device only — no hub doctrine gap; conceptually consistent with `context-management.md` |
| Write / Select / Compress / Isolate (4 ops) | `context-management.md` rules 1–3, 6, 7 (progressive disclosure=Select, scratchpad/compaction=Write, subagent delegation=Isolate); no rule names "Compress" explicitly but `/end-session` + compaction-handoff cover the same function |
| "Context rot" from skipping the 4 ops | Same term already used in the hub's own [0xCodila capture](2026-07-01-0xcodila-loop-engineering-karpathy-bilevel.md) relevance section — not new vocabulary here |
| Cherny's 5 building blocks (Automation/Skill/Sub-agents/Connectors/Verifier) | Identical list already captured verbatim in [0xCodila's Part 3](2026-07-01-0xcodila-loop-engineering-karpathy-bilevel.md) — maps to trust-score hard-gates, `supervisor-verification.md`, `independent-test-verification.md`, `.claude/skills/`, `/loop`+`/goal`, loop-engineering plugin |
| CLAUDE.md ~200-line budget, "every line earned" | `.claude/rules/rule-curation.md` (reactive not speculative curation) + this repo's own CLAUDE.md discipline already enforces this instinct |
| Hooks are 100% enforced vs CLAUDE.md ~70% advisory | Consistent with why the hub backs conventions with hooks (`auto-git.sh`, `branch-choice-gate.sh`, etc.) rather than prose alone — restates existing hub practice, no new mechanism |
| Dynamic Workflows (Claude writes its own orchestration, zero-token coordination) | Closest hub analogue is `agent-team-selection.md`'s subagent/worktree/team primitive choice, but the article's "orchestration lives in code, not context" claim is a *feature description*, not a technique the hub can adopt without a concrete Claude Code capability reference — no action, flag as a term to watch for if/when `/loop`+Routines gain a native fan-out primitive |
| Routines (cron/webhook/GitHub-event cloud triggers) | Already covered by the hub's `schedule` skill / Routines feature; no new information |

**Genuinely new relative to both prior captures:** essentially nothing procedural. The one item worth
flagging as a *framing*, not a technique, is the explicit "Write / Select / Compress / Isolate" 4-verb
taxonomy for context operations — cleaner and more citable (echoes Anthropic's own public "context
engineering" terminology) than either prior capture's looser prose, and could be borrowed as vocabulary
if `context-management.md` is ever rewritten, but it does not currently name a gap in that rule file's
substance.

**No action recommended — redundant with the context-engineering and loop clusters.** Do not cite the
"0.637/0.488 MMLU" or "2-3x from verification" figures anywhere in hub docs; both are unsourced in this
piece and third-hand at best. Cross-reference alongside
[noisyb0y1 context-engineering](2026-07-04-noisyboy-context-engineering-system.md) (same context-layer
thesis) and [0xCodila Karpathy/Bilevel](2026-07-01-0xcodila-loop-engineering-karpathy-bilevel.md) (same
loop-building-blocks content, plus the one genuinely novel idea in the cluster — the Bilevel meta-loop
— which this article does not mention at all).
