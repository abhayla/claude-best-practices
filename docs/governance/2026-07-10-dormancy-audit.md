# Governance dormancy audit — 2026-07-10 (fable-window item 5, Part C)

**Purpose:** the delete-the-harness pass. For every wired governance hook and every auto-loaded
governance rule-block, a verdict: **KEEP** / **SILENCE-ON-MACHINE-TURNS** / **DEAD-DELETE-CANDIDATE**
/ **DUPLICATE-OF-PLUGIN**, each with its evidence.

**This report deletes nothing.** Deletions and rule-text edits are a follow-up needing owner approval
(the proposed rule diff is `docs/governance/2026-07-10-proposed-rule-diffs.md`). Part A of this same PR
already implements the SILENCE-ON-MACHINE-TURNS verdicts via the shared `turn-origin.sh` predicate.

## Evidence base (live telemetry, 30-day window ending 2026-07-10)

Read live from the operational `.claude/*.log` files (gitignored; sampled from the main checkout,
not this worktree) via `scripts/lint_rule_compliance.py --telemetry-dir <main>/.claude`:

| Log | Recent count | Breakdown |
|---|---|---|
| `.enhance-misses.log` | **416** | 258 enhance-block-miss, 85 role-miss, 73 enhance-banner-miss |
| `.overask-violations.log` | **556** | 340 reviewer-card-miss, 82 narrate-and-stop, 60 diagnosis-substance-miss, 52 over-ask, 19 session-boundary (exempt), 3 card-block-EXHAUSTED |
| `.verifier-misses.log` | **36** | 36 verifier-edge-miss (all code-edit) |
| `.config-changes.log` | **317** | 317 config-change **all `kind=unknown`** |
| `.enhance-plugin-misses.log` | 9 | 9 review-table-miss (pre-stand-down / non-hub) |

**Key reading:** the 416 enhance-misses + the 340 reviewer-card-miss + 60 diagnosis-substance-miss
(400 of the 556 overask entries) are the SAME enhance-ceremony enforcement firing — and the bulk are
autonomous/continuation turns being graded like human prompts. That is the noise the fire-where-it-pays
predicate removes. The genuinely-useful governance (82 narrate-and-stop + 52 over-ask = 134) is a small,
healthy fraction and STAYS active on machine turns.

## Hook verdicts

| Hook (event) | Verdict | Evidence / rationale |
|---|---|---|
| `prompt-enhance-reminder.sh` (UserPromptSubmit) | **SILENCE-ON-MACHINE-TURNS** (KEEP for humans) | Injects the full-enhance reminder. 416 enhance-misses, largely autonomous turns. Part A: machine turns now get only the governance tail. |
| `no-overask-guard.sh` — enhance-card block (Stop) | **SILENCE-ON-MACHINE-TURNS** | 340 reviewer-card-miss + 60 diagnosis-substance-miss. These enforce the enhance card; on machine turns they were pure noise. Part A exempts machine turns (reuses the `is_slash` plumbing). |
| `no-overask-guard.sh` — over-ask + narrate-and-stop block (Stop) | **KEEP (stays active on machine turns)** | 82 narrate-and-stop + 52 over-ask are real, actionable governance on autonomous work. Deliberately NOT gated by origin. |
| `enhance-process-guard.sh` (plugin Stop, present in-hub) | **DUPLICATE-OF-PLUGIN (already dormant in-hub)** | Coexistence stand-down (v0.3.1): exits 0 when `no-overask-guard.sh` is wired — the hub's superset enforcer already covers its card/Overall block. In-hub it is correctly inert; it enforces only downstream. Part A additionally teaches it `full_process_scope` for downstream parity. |
| `verifier-edge-guard.sh` (Stop) | **KEEP** | 36 real verifier-edge-miss, telemetry-first (never blocks). Active, low-noise signal on the builder→verifier boundary. |
| `config-change-crud-guard.sh` (ConfigChange) | **DEAD-DELETE-CANDIDATE (or REWRITE)** | 317 hits, **100% `kind=unknown`** — the CRUD classifier never classifies, so the log is 317 unactionable rows. Either fix the `kind` derivation (REWRITE) or retire the hook (DELETE). Zero decisions have ever keyed off it. Owner call. |
| `session-governance-status.sh` (SessionStart) | **KEEP** | Informational session banner; fires once per session, negligible cost, orients the operator. |
| `subagent-governance-inject.sh` (SubagentStart) | **KEEP** | Verified firing live (CC v2.1.183); injects plan-first/root-cause/structured-return into workers. |
| `compaction-handoff.sh` (PreCompact) | **KEEP (unverified)** | Wired but can't be triggered on demand; writes a breadcrumb before compaction. No noise. Leave until the platform lets us verify. |
| `ba-usecase-discovery-reminder.sh` (UserPromptSubmit) | **KEEP** (candidate for SILENCE-ON-MACHINE-TURNS follow-up) | Offer gate for BA/deep-research. No dedicated miss-log sampled here; it also fires on every prompt, so a future pass should give it the same machine-turn exemption. Out of scope for this PR (no measured noise yet). |
| `stale-branch-reaper.sh` / `auto-pr-reconcile.sh` / `session-concurrency-guard.sh` (SessionStart) | **KEEP** | Lifecycle automation, not enhance/governance ceremony. Out of scope. |

## Rule-block verdicts (auto-loaded `# Scope: global` rules)

From `scripts/lint_rule_compliance.py` (18 directives across 7 global rules). Full machine-readable
output: `python scripts/lint_rule_compliance.py --json`.

| Rule block | Verdict | Evidence |
|---|---|---|
| `prompt-auto-enhance.md` — "MANDATORY OUTPUT" / "indicator is unconditional on substantive OUTPUT" | **REWRITE** | 416 enhance-misses map here; the "unconditional on OUTPUT" wording is exactly what graded machine turns. Rewrite to human-typed scope + point at `turn-origin.sh`. Proposed diff in Part D. |
| `prompt-auto-enhance.md` — "Slash commands are NEVER enhanced" | KEEP (already machine-checked by the hook) | The lint flags it REWRITE only because it keyword-associates to the enhance log; the hook already enforces it deterministically. No change — the association is a lint false-positive noted here for honesty. |
| 15 directives in `claude-behavior.md`, `claude-docs-cache.md`, `context-management.md`, `model-routing.md`, `product-incubation.md`, `workflow.md` | **DEMOTE (candidates)** | Zero measurable telemetry AND no wired hook measures them — unenforceable prose in an always-loaded rule. Candidates to move to skill docs / on-demand references. NOT actioned here (owner approval + case-by-case; several are load-bearing doctrine worth keeping even unmeasured). |

## What Part A already changed (the SILENCE verdicts, implemented)

- New SSOT predicate `.claude/hooks/turn-origin.sh` (+ core + plugin copies): `classify_turn()` →
  `human`|`machine` for task-notification / scheduled-wakeup / skill-execution / system-reminder-only.
- `prompt-enhance-reminder.sh`: machine turn → governance tail only, no enhance block.
- `no-overask-guard.sh` (hub + core, synced): machine turn → exempt from the enhance-card/banner/role
  enforcement (over-ask + narrate-and-stop stay active).
- Plugin: `full_process_scope` setting (`human-prompts` default) honored by both plugin hooks.

## Recommended follow-ups (owner-gated, NOT in this PR)

1. **`config-change-crud-guard.sh`**: fix the `kind` derivation or retire it (317 unactionable rows).
2. **Rule text**: ~~apply the Part-D diff to `prompt-auto-enhance.md`~~ — DONE (owner approved 2026-07-10, applied on this branch).
3. **`ba-usecase-discovery-reminder.sh`**: extend the machine-turn exemption to it if its telemetry
   shows the same autonomous-turn noise.
4. **DEMOTE pass**: review the 15 zero-signal directives one at a time; move genuinely-unenforceable
   ones to skill docs (keep load-bearing doctrine).
