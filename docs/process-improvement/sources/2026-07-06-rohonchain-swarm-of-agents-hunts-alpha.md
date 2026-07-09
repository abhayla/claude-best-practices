Source: https://x.com/RohOnChain/status/2074134246784921977
Captured: 2026-07-09

# RohOnChain — "How to Build a Swarm of AI Agents That Hunts Alpha 24/7"

**Author:** RohOnChain ([@RohOnChain](https://x.com/RohOnChain)) — backend/quant-systems builder, HFT-style execution + prediction-market behavior.
**Posted:** 2026-07-06 · **Engagement at capture:** 368 likes, 57 RTs, 33 replies, 575,525 views
**Format:** Single long-form X-native article (~15.9k chars), 6 parts + summary.
**Nature:** **Vendor-promotional how-to with a crypto/quant-trading domain.** Built around a third-party paid tool ("Slate" by @wearerandomlabs, `randomlabs.ai`) — the article is effectively a sponsored-style walkthrough ending in a sign-up CTA and DM-for-review offer ("first 20 setups," reply/DM). **All tool claims, pricing, and "replaces a research team" framing are vendor marketing, not independently verified.** **Domain caveat:** the entire worked example is a six-agent *quantitative alpha-research* pipeline (arXiv paper mining → feature engineering → backtesting → statistical validation → regime auditing → factor decomposition) — squarely crypto/trading-quant, not this hub's domain.

---

## The core claims (faithful summary)

**Mental model (Part 1):** prompt = one-shot question; loop = a job the agent keeps working until actually done; **swarm = many loops in parallel, each a specialist, output of one feeding input of the next.** Opens with an attributed quote: Boris Cherny (Anthropic, head of Claude Code) — *"I don't prompt Claude anymore. I have loops running that prompt Claude and figuring out what to do. My job is to write loops."* (Same Cherny quote/framing already surfaces across other captured pieces — treat as corroborated framing, not unique to this article.)

**The tool (Part 2):** "Slate" — a terminal AI coding harness with a feature called "Programs": a loop written in JavaScript that Slate runs continuously, holds state between runs, and lets the author assign different models to different steps (cheap model for easy work, frontier model for hard reasoning). **Unverified vendor claim** — no independent evidence Slate does what's described beyond the article's own screenshots/CTA.

**The six-agent swarm (Part 3)** — a maker/checker quant-research pipeline:
1. **Idea Generator** (fast/cheap model) — mines arXiv q-fin/SSRN overnight, extracts hypotheses into structured tickets.
2. **Feature Engineer** — builds/cleans the feature vector (missing data, outliers, look-ahead bias).
3. **Backtester** — runs 20-year historical backtest with transaction/borrow costs and slippage; outputs Sharpe, drawdown, turnover, capacity.
4. **Validator** (stronger reasoning model) — Newey-West t-stats, 10,000-iteration bootstrap, kills signals with >30% in-sample/out-of-sample degradation. Explicit rule: **"the maker never validates the maker's own work."**
5. **Regime Auditor** — HMM-segments 20 years by regime, kills signals that only work in one regime.
6. **Factor Decomposer** — regresses against Fama-French 5-factor + Carhart momentum + low-vol; only surviving residual alpha counts as genuine.

Runs as one Slate Program firing every 24 hours; author reports "20–40 minutes" per cycle and posting survivors to Slack.

**Three deployment patterns (Part 5):** overnight discovery, on-demand hypothesis-burst mode, and weekly alpha-decay monitoring (rerun validated signals against fresh data, flag Sharpe decay).

**Five failure modes (Part 6):**
1. Skipping the validator (data-snooping in disguise).
2. No state persistence (re-tests the same failed hypothesis daily).
3. No maker-checker split ("the agent that generated the hypothesis is the worst possible judge of whether it's real alpha" — attributes the practice to Renaissance/Two Sigma/Citadel, unverified).
4. One agent doing everything (quality collapse without specialization).
5. No stopping condition checkable by something other than the agent's own claim ("Sharpe above 1.5 over the last 30 out-of-sample trades," never "the agent says it is done").

Closing framing: "the infrastructure moat is real, the research moat is dead" — cross-references the author's earlier "loop engineering" / self-improving trading-execution article as the companion piece.

---

## Relevance to this hub — LOW-to-MODERATE (orchestration mechanics already covered; domain is out-of-scope; vendor/financial claims unverified)

The **mechanics** — specialist loops in parallel, maker≠checker, state-file memory so the loop doesn't repeat failed work, a hard non-self-reported stop condition, model-tiering by task difficulty, a scheduled 24h heartbeat — are the same primitives already documented (in more rigorous, non-vendor-tied form) elsewhere in the hub's own captures and doctrine:

| RohOnChain concept | Existing hub analogue |
|---|---|
| Swarm = many specialist loops, output→input chained | `loop-engineering` DISCOVER→PLAN→EXECUTE→VERIFY→SHIP; `core/.claude/rules/agent-orchestration.md`; the 8 workflow skills' step DAGs (`config/workflow-contracts.yaml`) |
| "The maker never validates the maker's own work" (Validator agent) | `core/.claude/rules/supervisor-verification.md` + `independent-test-verification.md` — maker ≠ checker is the hub's central rule, already stated more generally |
| State persistence so the loop doesn't retest failures | `.remember/`, `.claude/tasks/lessons.md`, scratchpad-to-disk pattern in `context-management.md` |
| Hard stop condition, not the agent's own "done" claim | `supervisor-verification.md`; trust-score hard gates (`config/trust-score.yml`) |
| Model-tiering (cheap model for volume, frontier for judgment) | `.claude/rules/model-routing.md` — haiku/sonnet/opus tiering by task, already codified hub-wide |
| Specialist agents, one stage each | `agent-team-selection.md` (subagent vs team vs worktree) + per-role `core/.claude/agents/*.md` |
| Scheduled 24h heartbeat firing the swarm | `ScheduleWakeup`/cron (`scan-*.yml`), `/schedule` skill, `loop-engineering` cadence |
| Notify-on-signal (Slack post of survivors) | `core/.claude/rules/notifier-integration.md` — owner-alerts via the shared Notifier gateway (already a hub-wide pattern, domain-agnostic) |

**Nothing new to adopt.** Every orchestration primitive named here (parallel specialist loops, maker≠checker, state-file memory, hard stop conditions, model-tiering, scheduled firing) is already present in the hub's own doctrine and in prior captures (khairallah's agent-team piece, 0xCodila's loop-engineering piece, the ClaudeDevs loop taxonomy) — this article is a **domain-specific re-skin** of the same mechanics for quantitative alpha research, not a new pattern.

**Why relevance stays LOW-to-MODERATE, not HIGH:**
- **Domain is out-of-scope.** The concrete worked pipeline (arXiv mining, Sharpe/drawdown backtesting, Newey-West bootstrap, Fama-French factor decomposition) is quant/crypto-trading specific and has no direct hub application.
- **Vendor-promotional structure.** The piece is built to sell "Slate"/`randomlabs.ai` (a paid third-party tool) via a sign-up CTA and a "DM me, first 20 only" scarcity hook — treat the tool's capabilities and the "replaces a research team" framing as **unverified marketing claims**, not evidence.
- **Financial/return claims are explicitly NOT to be propagated.** Any implied Sharpe/alpha/performance outcomes belong to the source's own (unverified) worked example — this hub has no trading system and should not cite or repeat these numbers as if validated.

**No action required.** Confirms (once again) that the hub's existing maker≠checker, state-persistence, and hard-stop doctrine matches the state of the broader "loop/swarm" discourse, including in a domain (quant trading) the hub doesn't operate in. **Cross-links:** [khairallah — first team of AI agents](2026-07-07-khairallah-first-team-of-ai-agents-cowork.md) (same specialist-role/handoff pattern, consumer framing), [0xCodila — Loop Engineering / Karpathy Method](2026-07-01-0xcodila-loop-engineering-karpathy-bilevel.md) (same maker≠checker + verifier + state + stop-condition primitives, argued more rigorously and without a vendor CTA), [ClaudeDevs loop taxonomy](2026-07-06-claudedevs-getting-started-with-loops.md) (first-party Proactive/Time loop types this swarm's "24h scheduled fire" instantiates).
