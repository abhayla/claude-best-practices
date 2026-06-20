---
name: cc-adoption-scout
description: >
  Scout the latest Claude Code / Anthropic platform releases and decide, against THIS
  hub's adoption doctrine, which new features to ADOPT, KEEP-hand-rolled, REJECT, or
  MEASURE-FIRST — then file migration issues for the adopt/measure candidates. The FREE,
  on-demand, in-session form of the platform-migration self-updating loop (Layer 1): run
  it in a session you are already in — no scheduled cloud agent, no recurring spend. Use
  when you want to check "what new Claude Code features should this hub adopt?" after a CC
  release, periodically, or before planning hub work. NOT for general external pattern
  scanning (use /self-improve), and NOT the paid scheduled-routine version (tracked
  separately as a recurring-spend owner decision — see issue #153).
type: workflow
allowed-tools: "Read Grep Glob Bash Edit WebFetch WebSearch Agent"
argument-hint: "[--apply (file issues) | --dry-run (default, report only)] [--since vX.Y.Z]"
version: "1.0.0"
---

# /cc-adoption-scout — free in-session Claude Code feature-adoption judgment

This is the **agentic judgment half** of the hub's self-updating Layer 1. The mechanical
half already exists and is free: `scan-internet.yml` (weekly) → `scan_web.py` →
`discovery_to_issue.py` surface new-feature discoveries as issues. What was still **manual**
is the JUDGMENT — *"should this hub adopt / keep / reject / measure this feature?"* — which
is exactly the work the 2026-06-20 platform-migration session did by hand. This skill makes
that judgment a repeatable, **free, on-demand** procedure (runs in your current session;
costs only the usage of the session you are already in — no scheduled cloud agent).

> **Cost contract (load-bearing):** this skill MUST NOT create a scheduled cloud routine,
> call any billed/`ultra` feature, or spend money. It runs in-session only. The paid
> scheduled-routine version is a separate owner decision (issue #153) — never auto-enact it.

**Arguments:** `$ARGUMENTS` — default is `--dry-run` (report only; file nothing).

---

## STEP 1: Load the doctrine + the release sources

1. Read the hub's adoption doctrine so judgments are anchored, not ad-hoc:
   - `plans/platform-migration-2026H2.md` — the ledger + the adopt/keep/reject/measure precedents.
   - `core/.claude/rules/rule-curation.md` (reactive-not-speculative), `claude-behavior.md`
     rules 16/21/22 (KISS / YAGNI / measure-before-optimize), `agent-orchestration.md`
     (single-level + the S2 "adopt only if measured better" precedent).
2. Read the wired release-tracking URL entries from `config/urls.yml` (a flat list of `url:`
   entries, added in Phase 5.1a) — the official Claude Code docs: `whats-new`, `sub-agents`,
   `skills`, `hooks`, `worktrees`, `scheduled-tasks`, `agents-and-tools` (+ any added since).
3. Resolve the baseline: the last-reviewed CC version. Default = the most recent version
   named in `plans/platform-migration-2026H2.md`; override with `--since vX.Y.Z`.

## STEP 2: Fetch what shipped since the baseline (adversarial, not single-source)

Fetch the current release docs with `WebFetch` (or dispatch parallel web-research workers via
`Agent()` at T0 for breadth). For higher-stakes verification, prefer the native `/deep-research`
harness so a claim is cross-checked, not taken from one page. Extract every feature/primitive
**new since the baseline** — name, ship version, GA-vs-experimental status, and the exact
doc quote (never paraphrase a GA/availability claim — the 2026-06-20 audit caught a
"research-preview vs GA" conflation that cost a wrong deferral).

## STEP 3: Judge each feature against the doctrine (the core step)

For EACH new feature, classify into exactly one bucket, with a one-line reason:

| Verdict | When | Example precedent |
|---|---|---|
| **ADOPT** | A concrete hub caller benefits AND it beats the hand-rolled version (KISS win, real capability) | SubagentStart/ConfigChange hooks (verified live) |
| **MEASURE-FIRST** | Plausible benefit but unproven for a hub workflow — needs an A/B before adopting | Dynamic Workflows tool → S2 A/B |
| **KEEP hand-rolled** | The native primitive exists but the hub's version is equal/better or migrating is churn | Routines vs the deterministic GH-Action crons (negative ROI) |
| **REJECT / not-ready** | Experimental, flag-gated, or breaks a hub guarantee | Agent Teams (experimental, breaks session resumption) |

Hard rules for the judgment (these ARE the doctrine):
- **Reactive, not speculative** — ADOPT only with a concrete caller; never "because it's new."
- **Measure before adopting** a feature whose benefit is a performance/parallelism claim
  (the S2 precedent: identical wall-clock → not adopted).
- **Additive / opt-in for anything downstream inherits** — never change a distributable
  default without flagging it as an owner decision.
- **Spend / policy = owner decision** — a feature that costs money (billed review, scheduled
  cloud agent) or changes execution policy is PROPOSE-only; file it, never enact it.

## STEP 4: Dedupe against what the hub already decided

Before filing anything, check it is genuinely new:
- Search the plan ledger + `registry/changelog.md` for an existing adopt/keep/reject record.
- Search open + recently-closed GitHub issues (`gh issue list --search`) so you comment on an
  existing tracking issue instead of duplicating (reuse the `discovery_to_issue.py` /
  `/create-github-issue` dedup conventions).
- If `scan_web`/`discovery_to_issue` already filed a discovery for it, ENRICH that issue with
  the verdict rather than opening a new one.

## STEP 5: Report — and file issues only with `--apply`

1. Always print a verdict table: feature · version · status · verdict · one-line reason.
2. **`--dry-run` (default):** stop here — report only, file nothing.
3. **`--apply`:** for each **ADOPT** or **MEASURE-FIRST** verdict, file (or comment on) a
   migration issue linked to the platform-migration epic, with: the doc quote, the verdict +
   reason, a migration sketch, and an explicit `owner-decision` flag if it implies spend or a
   policy/default change. KEEP and REJECT verdicts are recorded in the report only (no issue) —
   unless a KEEP overturns a prior ADOPT, which warrants a tracking note.
4. Append a one-line entry to `plans/platform-migration-2026H2.md`'s log so the baseline
   advances and the next run does not re-audit the same release.

## CRITICAL RULES

- MUST run in-session only — MUST NOT create a scheduled cloud routine, invoke any billed/
  `ultra` feature, or spend money. The paid scheduled version is owner-gated (issue #153).
- MUST anchor every verdict to the hub doctrine (reactive-not-speculative · KISS/YAGNI ·
  measure-before-adopt · additive-for-downstream), never "adopt because new".
- MUST quote the official doc verbatim for any GA/availability/version claim — never
  paraphrase it (the conflation that caused a wrong deferral on 2026-06-20).
- MUST classify a spend- or policy- or default-changing feature as PROPOSE-only and file it
  for owner decision — never auto-enact.
- MUST dedupe against the plan ledger + existing issues before filing; enrich an existing
  discovery issue rather than duplicating it.
- MUST default to `--dry-run`; file issues only when `--apply` is explicitly passed.
- MUST advance the reviewed-baseline marker so successive runs don't re-audit settled releases.
