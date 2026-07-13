# Fable-window external scan — what others do with Fable 5, and the harvest candidates (2026-07-13)

Source: 3-agent web scan (X/Twitter via Jina ladder, Reddit/HN via relays + Algolia, blogs/Anthropic docs)
Captured: 2026-07-13, by the hub session that ran the scan (owner request: "find what others are doing
with Fable; list features worth adopting; prioritize; no implementation")
Relevance: Fable-window harvest planning — what to have Fable produce BEFORE paid-only access resumes.

## Method + dedup baseline

Findings were cross-checked against (a) the 25 Fable captures already in this INBOX and (b) the shipped
fable-window program (PRs #313–#327: operating manual + parity exam, trust recorder, standing-goals
ledger, cost ledger, refusal→Opus fallback, bilevel mutation, loop taxonomy, plugin validation) so the
list below is NET-NEW only. The "clone Fable into an operating manual" thesis — the loudest external
pattern — is already this hub's `fable-operating-manual` plugin (v2.0, ahead of every public variant
found: none has our blind 3-arm parity exam or incident-driven revision policy).

## Verified context worth knowing (from the scan)

- Anthropic cut Claude Code's system prompt ~80% because "Fable 5 models want a smaller system prompt";
  over-specification/examples now DEGRADE frontier output (the-decoder + MindStudio, corroborated).
- Community relay economics: Fable-orchestrator + Sonnet-workers ≈ 96% of all-Fable quality at 46% cost
  (Developers Digest; single-source figures, cited-not-verified) — external validation of
  `model-routing.md`, no change needed.
- Anthropic actively intercepts naive "distill Fable" requests (classifier → reroute to Opus 4.8);
  procedure/discipline extraction (manuals, skills, rubrics) is the pattern that works and circulates.
- Access-window dates are volatile (June 22 cutoff → July 7 extension → July 12 → reports of reversion);
  treat any date as a snapshot — the owner's statement ("a few days left") governs planning.
- Reviewers converge: Fable's edge = long/ambiguous/failure-recovery work + verification-as-judgment;
  use it for structured machine-consumed artifacts (rubrics, tests, manuals), not prose deliverables.

## Candidate list (owner decides; sizes are rough)

| # | Idea | Value in one line | Size | Needs Fable before window closes? |
|---|---|---|---|---|
| 1 | **Fable rule-stack contradiction audit** — Fable reads ALL rule/CLAUDE.md/hook-injected text end-to-end; flags contradictions, rules that exist only to manage weaker models, rules that teach by bad example (PM-guide pattern + Anthropic's own 80%-cut precedent) | A frontier semantic pass `lint_rule_compliance.py` (telemetry-only) cannot do; directly attacks the 24/7d enhance-miss overhead | S (one Fable session) | **YES** — frontier judgment is the point |
| 2 | **Failure-archaeology → skill library** — 3-phase Fable run (mine git history + `lessons.md` + reverted/churned commits across hub + 5 downstream repos → interview → author 10–16 SKILL.md files → self-review) (r/ClaudeAI "Rodbourn" / PrajwalTomar pattern) | Converts 400+ commits of recorded failure into durable skills cheaper models inherit; the hub is uniquely positioned (lessons.md already exists as seed) | M | **YES** — skill quality is the asset |
| 3 | **Rubric-mining from own ledgers** — feed Fable known-good vs known-bad artifacts (merged-clean PRs vs reverted/red ones from the trust ledger) → scoring rubrics for checker agents (code-reviewer, quality-gate-evaluator) | Fable-quality judgment encoded once, run forever by Sonnet checkers; strengthens maker≠checker | M | **YES** — rubric authorship |
| 4 | **Fable-authored trap/eval batteries for top-N skills** — extend the parity-exam trap technique to per-skill evals, burning down the 165-skill eval grandfather list for the ~10–20 highest-traffic skills | Frontier-authored evals keep gating quality after Fable leaves; directly shrinks queue item #8 | M–L | **YES** — trap authorship |
| 5 | **Verification skill with weakened-test hunting** (community `/fable-judge` pattern: re-run every claimed check, diff what actually changed, hunt weakened/deleted assertions, verdict VERIFIED/CAVEATS/REFUTED) | Test-weakening detection is a real gap in our gates (nothing today catches a fix that passes by gutting the test) | M | Partially — Fable authors it now, Opus runs it later |
| 6 | **Injected-prompt volume audit for frontier dispatches** — measure whether our distilled-core + rules + hook-reminder volume degrades Fable/Opus output (Anthropic's 80%-cut finding + "weaker steerability, give it latitude" reviews) | Potentially better output AND lower cost from LESS harness; evidence-driven trim | S–M | Partially — best A/B'd while Fable is cheap |
| 7 | **Full-manual audit-subagent surface** — mechanism-matched installer idea: distilled core stays injected, but a fresh-context audit subagent carries the FULL manual for zero-decay strategic review | New delivery surface for the manual we already own; cheap composition | S | No — plugin work any model can do |
| 8 | **SkillSpector-style pre-install skill/plugin security scan** (+ Graphify knowledge-graph memory, weaker) — the one real gap from the earlier 10-repos capture | Hub installs third-party skills/plugins with no automated security intake today | M | No |
| 9 | **Novelty tracking in self-improvement rounds** (diversity-collapse guard from the New-AI-Stack capture; embedding-similarity dedup of improvement proposals) | Stops repeated improvement cycles converging on one strategy; last open gap from that capture | M | No |
| 10 | **Doc-level adds** — cite orchestrator-economics numbers + effort-tier arbitrage ("medium Fable ≈ max Opus", unverified) in `model-routing.md`; subagent-branching budget note (one Fable task can spawn 4–6 subagents silently); native `/goal` adoption evaluation (first-party) | Legibility/citation value only; mechanics already exist | S | No |

Filtered out as already-built: operating-manual cloning (plugin v2.0), refusal→Opus fallback, cost
ledger, standing-goals ledger, barbell routing, escalate-one-tier, loop taxonomy, trap-test technique
(parity exam), bilevel meta-loop.

## Recommended priority (window-first, then value)

1. **#1 contradiction audit** — smallest, purest Fable-reserved task; every other item benefits from a cleaner rule stack.
2. **#2 failure-archaeology skills** — highest durable-asset yield per Fable token; seed material already on disk.
3. **#3 rubric-mining** — compounds with maker≠checker forever; our ledgers make it evidence-driven, not vibes.
4. **#4 trap/eval batteries (top-N)** — same technique we validated in the parity exam, aimed at the eval-debt queue item.
5. **#5 weakened-test hunter** — closes a real verification gap; authorship now, execution later.
6. **#6 prompt-volume audit** — evidence exists (Anthropic's own cut); cheap experiment, possible big harness saving.
7. **#7–#10** — not window-sensitive; queue normally.

## Caveats

- X attributions beyond Cherny/Rieseberg/@claudeai are secondhand (roundup repos/blogs); all cost/percentage
  figures (58% savings, 96%@46%, $600/day) are single-source, cited-not-verified — do not propagate as fact.
- Reddit was unreachable directly (403); r/ClaudeAI patterns arrived via blog relays naming the threads.
- Window dates conflict across sources; verify live before scheduling anything date-dependent.
