Source: https://x.com/Av1dlive/status/2074169173178212621
Captured: 2026-07-08
Author: Avid (@Av1dlive)
Posted: 2026-07-06
Engagement (at capture): 642 likes, 82 RTs, 50 replies, ~991k views
Delivered-via: `/remote-control CBP081` (remote task hand-off) this session

# "How to Build An Agentic OS using Fable 5 (Builder's Guide)"

> ⚠️ **Model-claim caveat (same as the Codez note):** this article makes Fable-5
> specifics — pricing (`$10/M in, $50/M out`), `max_tokens` caps thinking+text,
> `xhigh` = "30-min+ agentic tasks with million-token budgets", refusals return
> HTTP 200 with `stop_reason: "refusal"`, a `reasoning_extraction` refusal
> category triggered by "show your thinking", old skills degrading Fable output.
> Several ALIGN with the hub's existing `model-routing.md` + environment notes
> (Fable 5 is real; effort tiers exist), but the **pricing and the
> refusal-as-HTTP-200 / reasoning_extraction behaviors are UNVERIFIED** against
> official docs. **Do NOT propagate any of these as fact** without checking the
> `claude-api` skill / Anthropic docs first. Captured as the author's claims.

## Relevance to this hub (VERY HIGH — the closest external blueprint of what the hub IS)

This is an 8-build recipe for the exact architecture the hub has been assembling
toward its **G5 north-star** (autonomous, self-improving machine). It is the
second source in this store (after the [Codez note](2026-06-11-codez-self-improving-fable5-14-steps.md))
to independently converge on the hub's design — but this one maps almost 1:1 onto
named hub components, which makes it a **coverage checklist**: what the hub already
has, and the handful of things it genuinely lacks.

### Build → hub component map (honest gap analysis)

| Build | What the article prescribes | Hub status |
|---|---|---|
| **0 Engine config** | `max_tokens` large at high/xhigh; check `stop_reason:"refusal"` not exit code; reroute refusals to Opus 4.8; **never** ask for echoed reasoning (triggers `reasoning_extraction` refusal + degrades); delete over-prescriptive old skills | **PARTIAL / GENUINE GAP.** `model-routing.md` covers tier routing + "delete the instruction if default is better". No refusal-as-HTTP-200 fallback doctrine anywhere (also flagged in Codez note — now reinforced by a 2nd source). "Never ask for echoed reasoning" is a **potential live conflict** with `prompt-auto-enhance` (which mandates rendering reasoning transcripts/grade cards) — worth an explicit audit for Fable-model dispatches. |
| **1 Constitution (CLAUDE.md)** | 4 blocks, **under 150 lines**, laws-not-tips, mostly stop-signs; test each line: "could the model comply 80% and claim success?" | **TENSION, not a defect.** Hub `CLAUDE.md` is a multi-thousand-line architecture INDEX, deliberately not a lean constitution. The "80%-comply-and-claim-success" line test is a sharp lint the hub does not apply. Worth recording the deliberate divergence. |
| **2 Walls + gate (contract.md + verify.sh)** | Declare blast radius before tick 1; a bash script holds the final deterministic vote | **COVERED.** `config/workflow-contracts.yaml`, the `validate` required check, `verify.sh` analogues, `pre-git-merge-checker-agent`. |
| **3 Heartbeat (conductor/worker/verifier)** | Fable conducts (10-20% of tokens, 100% of decisions); cheap models do work; independent verifier grades; JSON work-order handoff | **WELL COVERED.** `loop-engineering` + `model-routing.md` (cheapest-sufficient tiering) + maker≠checker rule. The cost framing ("model that reads the quiet ticks decides the bill") directly validates `model-routing.md`. |
| **4 Trust ledger** | Per-**skill** autonomy TSV; 20 runs AND 95% → `auto`; auto-demotion loud on stderr | **PARTIAL.** Hub trust-score is per-**stage**, 30-run graduation, shadow-mode, hard-gates. The article's per-skill roster (fix-lint-debt, fix-flaky-test, bump-deps, triage-issues each graduating independently) is a finer granularity the hub does not track. |
| **5 Standing goals + goal ledger** | **One file per FINISHED thing**, re-verified **daily forever** by a read-only predicate (exit 0 = invariant holds); "finishing IS enrollment"; graduate, don't close | **GENUINE CONCEPTUAL GAP.** `goals.yml` is G0-G6 with machine-checkable DoDs — high-level, not a *growing directory of every finished deliverable* re-verified daily. "A goal you only verify once is an assumption with a timestamp" is the sharpest idea in the article and the hub does not yet implement the invariant-ledger form. |
| **6 Self-enforcing budget** | Daily cost ledger + `cost-check.sh`; cadence is a cost decision; quiet tick must cost cents; effort never > high in loops | **PARTIAL GAP.** Workflow tool + trust-score have budget hooks, but there is no daily cost ledger / cost-check for the autonomous loop, and no "quiet tick costs a penny or the loop costs a grand" discipline codified. |
| **7 Optional loops (install-on-condition)** | Quorum (3 cheap voters, Fable wakes on 2/3), Ratchet (monotonic-or-revert), Sparring (builder vs breaker), Compost (failures→laws, weekly, human-signed) | **MOSTLY COVERED, not named/conditional.** Quorum/Sparring ≈ agent-teams peer review; Ratchet ≈ eval-coverage ratchet; Compost ≈ `learn-n-improve`/`lessons.md`. The **"install only when the condition appears" doctrine** (anti-speculative-bloat) is a discipline the hub could name explicitly (echoes YAGNI rule 21). |
| **8 Ops (Makefile, cron, runbook, 30-day trust schedule)** | Per-alarm runbook; 30-day graduated-trust schedule supervised→self-extending | **PARTIAL GAP.** Hub has CI/cron; no explicit per-alarm runbook or 30-day graduated-trust onboarding schedule. |

### The three principles (verbatim — these are the reusable core)

1. **Laws, not tips.** Every rule has a number, a never, or a command that checks it. Anything softer gets optimized away.
2. **Nothing grades its own homework.** Planner, worker, verifier, and gate are four different parties; the last is deterministic.
3. **Nothing that passed once goes unwatched.** Finished work graduates into a re-verified invariant.

### "The Rules (print this)" — the 16-line law card (verbatim)

1. Laws, not tips: a number, a never, or a command that checks it.
2. The conductor plans, workers execute, neither verifies. `--allowedTools` enforces it.
3. Agents talk in work orders. `done_when = spec + stop condition + future invariant`.
4. Spend effort where the loop branches. Never above `high` in a loop.
5. The quiet tick costs a penny or the loop costs a grand.
6. If a shell script couldn't check it, don't write it as a goal.
7. Goals graduate; they do not close. `verify-goals.sh` runs daily, forever.
8. Autonomy per skill: 20 runs, 95%, auto. Demotion automatic and loud.
9. Two ledgers: trust (workers) and goals (work). Read both with coffee.
10. Compute the metabolism before you cron.
11. Contract in the repo: acts-alone / queues / wakes-me.
12. Never iterate on output from a model you didn't choose.
13. The sentinel detects; the pipeline fixes.
14. Quorum before waking Fable. Ratchet then weld. Spar daily. Compost weekly.
15. One graduation criterion at a time. Every month, delete something.
16. From the official docs: `max_tokens` caps thinking plus text, refusals are HTTP 200, never ask for echoed reasoning, old skills degrade Fable, fresh-context verifiers beat self-critique.

## Full article text (verbatim, as extracted)

> This is a complete A–Z breakdown of Claude Fable 5 — what it is and how to use it like a 100x engineer. Bookmark these 8 builds before you forget.

**Introduction.** You have the most capable model ever made generally available, and you are still typing prompts at it one at a time. This guide fixes that. Here is the situation as of July 2026. Fable 5 can run for hours unattended, dispatch its own subagents, and do a week of work in a night. It is also metered ($10/M in, $50/M out through usage credits), it over-delivers when scope is not fenced, and it argues for its mistakes more convincingly than most people argue for their correct answers. Used casually, it is an expensive way to generate impressive wrong things. Used inside a system, it is the closest thing to an employee you can rent for three dollars a day.

What you will have at the end: a CLAUDE.md the model cannot negotiate with (BUILD 1); a daily loop where Fable 5 makes every decision but writes almost no tokens, cheap models do the work, an independent verifier grades it, and a bash script holds the final vote (BUILDs 2-3); a trust ledger that grants and revokes autonomy per skill, automatically, based on measured pass rates (BUILD 4); a goals directory where everything you ever finish keeps getting re-verified daily, forever, so nothing rots silently (BUILD 5); a budget that enforces itself (BUILD 6); four optional loops (quorum, ratchet, sparring, compost) each with the condition that tells you when to install it (BUILD 7); a cron schedule, a runbook for every alarm, and a 30-day trust schedule that takes it from supervised to self-extending.

**BUILD 0 — Configure the Engine (from the official Fable 5 docs).** Five official facts: (1) `max_tokens` is a hard cap on thinking PLUS response text — at high/xhigh set it large (start 64k) or Fable runs out of room mid-thought. (2) `xhigh` is officially for "long-running agentic tasks (over 30 minutes) with token budgets in the millions" — the conductor seat and nothing else; lower effort on Fable 5 "often exceeds xhigh performance on prior models," so resist upgrading workers. (3) Refusals are HTTP 200 — Fable 5 runs safety classifiers (offensive cyber, biology/life-sciences, reasoning-extraction); a declined request returns `stop_reason: "refusal"` as a SUCCESS response, so scripts must check the stop reason, not the exit code; official remedy is server-side fallbacks / SDK middleware re-routing to Opus 4.8. (4) Never ask Fable to echo its reasoning — prompts saying "show your thinking" trigger the `reasoning_extraction` refusal category and elevate fallbacks; read structured thinking blocks instead. (5) Turns are long by design — check on runs asynchronously (scheduled jobs, not blocking waits); this is why the heartbeat is cron. The official prompt pack ships tested language for: anti-overplanning, anti-gold-plating, grounded progress claims, autonomous-pipeline reminder, official memory format, and the official verifier instruction ("separate, fresh-context verifier subagents tend to outperform self-critique"). Two scaffolding orders: start at the top of your difficulty range, and refactor/delete old over-prescriptive skills (they DEGRADE Fable 5). CHECK 0: every `claude -p` has explicit large `max_tokens`; scripts check for `stop_reason:"refusal"`; no prompt says "show your thinking."

**BUILD 1 — The Constitution (CLAUDE.md).** Fable follows laws and optimizes around tips, so every line needs a number, a never, or a command that checks it. Four blocks, under 150 lines, no "think step by step" (reasoning is always on — paid tokens), no predefined agent personas (Fable designs better teams than you can predefine), mostly stop signs. Workflow-specific material (PR procedure, release checklist) goes in `skills/`, not here. CHECK 1: for every line ask "could the model comply 80% and claim success?" — if yes, rewrite with a number or a never.

**BUILD 2 — Walls and Gate.** Blast radius must be declared before the first tick; a bash script holds the final vote. Create `loop/contract.md` and `loop/guardrails/verify.sh`. CHECK 2: `./loop/guardrails/verify.sh` runs and exits 0 on your current repo — the whole system stands on this script.

**BUILD 3 — The Heartbeat.** Fable as worker is a four-figure bill (500k-1M token sessions at $50/M out); Fable as conductor emits 10-20% of tokens while making 100% of decisions; a $0.01 model reads the quiet ticks. Agents hand off through a JSON schema so any model fits any seat. Files: `loop/triage.md`, `loop/conductor.md`, `loop/workers/implement.md`, `loop/workers/verify.md`, `loop/loop.sh`. Exit map: 0 quiet/done, 1 cap, 2 reroute, 3 budget. CHECK 3: run `./loop.sh` once by hand — a quiet repo exits 0 for a penny; an actionable repo produces `work-order.json` (5 fields) and a verdict line in `STATE.md`.

**BUILD 4 — The Trust Ledger.** "Turn up autonomy as trust grows" is not a mechanism; a TSV with tier rules is. Autonomy is per skill. `loop/scripts/trust-log.sh`. Tier rules: `auto` = 20+ runs AND 95%+ pass (ships unattended); `queue` = verified drafts wait for you; `watch` = under 10 runs or under 90% (draft-only). Demotion is automatic and prints to stderr (cron mails it). Seed the roster with `loop/skills/<name>/SKILL.md` for each recurring chore (fix-lint-debt, fix-flaky-test, bump-deps, triage-issues); every skill starts at `watch`. CHECK 4: `trust-log.sh demo pass` 21 times → `--tier demo` prints `auto`; a fail on a 10+ run skill prints the ALERT on stderr.

**BUILD 5 — Standing Goals + the Goal Ledger.** A goal you only verify once is an assumption with a timestamp, so finished goals graduate into invariants re-verified daily and logged. One file per finished thing, `goals/<name>.md`. Predicate rules: a command; exit 0 = invariant holds; cheap, deterministic, read-only; adjectives banned — if a shell script can't check it, the checker can't either. Non-code predicates work the same (`find invoices/overdue -mtime +45 | wc -l` prints 0). `loop/verify-goals.sh` is the sentinel (detection only; fixes go through the normal pipeline). The graduation law lives in CLAUDE.md: every passed `/goal` writes its own standing goal — finishing IS enrollment. Flaky predicate: quarantine (`status: retired`), never delete. CHECK 5: add a goal with `predicate: true` and one with `predicate: false` — `verify-goals.sh` exits 1, flips the second to VIOLATED, both appear in the ledger.

**BUILD 6 — The Budget.** Daily cost = ticks × triage + hits × (conductor + worker + verifier). At real prices (triage $0.01, conductor $0.35, worker $0.10, verifier $0.40): a daily janitor is ~$2.56/day; a 15-minute babysitter with Fable in the triage seat is $34/day for the identical outcome. The model that reads the quiet ticks decides the bill. `loop/scripts/log-cost.sh` + `cost-check.sh`. Rules: cadence is a cost decision (halving the interval doubles the floor); the quiet tick must cost cents; effort never above high in loops (xhigh is for one-shot reviews). CHECK 6: after a week, `cost-check.sh --report` matches the formula within noise.

**BUILD 7 — The Optional Loops (install when their condition appears).** Quorum (install when dispatch shows Fable wake-ups that produced `action: stop`) — three cheap models vote, Fable wakes on 2 of 3, voters never see each other's answers. Ratchet (install when one number matters) — monotonic improvement or self-revert; the metric may not be gamed; the finished floor becomes a standing goal. Sparring (install when you ship code daily) — builder and breaker, opposed; neither touches the other's output; disputes go to you. Compost (install always, weekly) — failures become laws; three proposals max; human signature required. CHECK 7: each optional loop has its install condition written next to it — installing speculatively is how systems bloat.

**BUILD 8 — Ops.** `Makefile`; cron when Week 2 starts; a runbook for what each alarm means and what to do; a 30-day trust schedule (do not skip graduations; each unlocks the next).

**Closing.** Thirty days from now, if you did the checks: one loop ships boring work unattended, a goals directory re-verifies everything you ever finished, two ledgers tell you the truth about your workers and your work, and a weekly compost run proposes the system's own next improvement for your signature. The model was never the hard part. The hard part was building something around it that stays honest when you stop watching.

*Disclaimer (author's): "This article was written by using the user's notes and edited by Claude Opus 4.8 max."*
