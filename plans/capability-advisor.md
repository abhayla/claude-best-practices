# Capability Advisor — make every project use the right Claude Code features, with zero commands to remember

Status: v2 (2026-08-27) — reworked after an independent fresh-context Opus review (verdict on v1: REWORK). Owner: Abhay. Driver: Fable session.
Branch: `feature-utilization-meter` (worktree `D:/Abhay/GetWorkDone/wt-check/cbp-feature-meter`).
v1 → v2 change log at the bottom.

## 1. Problem (owner, 2026-08-27, verbatim intent)

"Whenever I work on a project I do not utilize Claude Code's features at their fullest — right skills, right agents, splitting work across them. I keep using the features I know. Many features exist that I don't know about. Fix this, fully autonomously, for new and existing projects. The user may forget commands — nothing should depend on remembering a command."

## 2. Evidence (scripts/feature_utilization.py, 30 days to 2026-08-27, 1,050 transcripts)

- Owner hands-on: 590 sessions. Coverage as first measured: 19/219 skills, 4/47 agents (8.6%). **This number is contaminated** (review B1): ~40 of the "never used" skills belong to plugins that are cached but NOT enabled (`cbp-*`), so they could not have been used. Corrected figure comes from T-395.
- Robust findings that survive the correction: plan mode 16 exits in 3 sessions; `Workflow` 2 calls; `EnterWorktree` 0; ~190 of 241 agent dispatches are `general-purpose`; specialist review/test/security agents ~5 total; browser is the top feature (Chrome MCP 1,351 + Playwright 793 calls).
- **The biggest single cause found (review B3, verified against code.claude.com/docs/en/memory + CHANGELOG):** Claude Code only honours `paths:` for path-scoped rules; the hub invented `globs:` and its validator ENFORCES it. So every "path-scoped" rule loads unconditionally: IPODhan 81 rule files / ~48k words (~64k tokens) per session, incl. android/flutter/vue in a Next.js repo; KKB 52/56, firekaro-planner 52/75, algochanakya 44/70, RealFuelPrices 11/35, calculator 9/35. The docs say >200 lines per file already "reduces adherence". Any new instruction competes with that pile.
- **The core v1 mechanism already exists and already failed (review B2):** IPODhan has `.claude/rules/engineering-roles.md` — a 191-line task→role→skill/agent table, auto-loaded — and specialist agents still ran ~2% of dispatches.
- Hub telemetry on what Claude follows: the one-line `*Enhanced:*` banner is missed 93×/30d; the multi-part card 380×. Short self-attested markers get followed; ceremony does not. `lint_rule_compliance.py`: all 23 global directives have zero measurable signal.

## 3. Approach (Musk order: requirement → delete → simplify → accelerate → automate)

**Requirement (fixed):** every task gets the *cheapest feature set that measurably improves outcome*, chosen without the owner doing anything. NOT "use everything".

### Step 0 — Fix the floor first (no new machinery)
- **T-394 (hub):** `globs:` → `paths:` in `core/.claude/rules/`; validator inverted to reject `globs:` (red-then-green test); registry hashes; all prose that teaches `globs:`.
- **T-396 (6 app repos):** same rename, one PR per repo, with an `InstructionsLoaded`-hook proof in IPODhan: rule files loaded at launch BEFORE vs AFTER.
- **T-395 (meter):** installed = settings-resolved `enabledPlugins`; cached-but-disabled → `not-enabled` bucket, out of the denominator.
- Exit criterion: IPODhan launch loads only its `# Scope: global` rules; corrected coverage number published.

### Step 1 — Rules diet in saturated projects, then MEASURE with zero new machinery
- After step 0, the always-on rule set per project is what remains unscoped. For IPODhan/algochanakya/firekaro/KKB: cut to the docs' bar (each file < 200 lines; only rules that need to be in every session stay unscoped). Owner-visible PR per repo.
- Then run the meter for 2 weeks. If specialist-agent share and plan-mode use move materially with no advisor at all, step 3 shrinks or dies. This is the reviewer's point and it is right: don't build the advisor on top of a pile that may itself be the cause.

### Step 2 — Adherence telemetry (cheap, honest, first thing that tells us if anything works)
- **Stop hook, telemetry only, never blocks** — `capability-plan-adherence.py` (user-level, Python, `D:\Abhay\GetWorkDone\hooks\`). The model self-reports the row it applied as ONE line, `capability-row: <id>` (same shape as the `*Enhanced:*` banner, which telemetry says gets followed). The hook reads `last_assistant_message` from hook stdin (docs: the transcript file lags the turn; never read the tail), greps the marker, compares the row's expected skill/agent/primitive names against the turn's tool calls, appends `{project, session, bucket, row, expected[], used[], adhered}` to `~/.claude/.capability-adherence.jsonl`. Unmarked turns log as `unclassified` — never guessed. Bucketed with the meter's `FLEET_SLUG_MARKERS` so fleet workers never mix with owner sessions.
- No keyword classifier (review S7): a classifier owns the denominator and makes the % unfalsifiable.

### Step 3 — The Capability Plan (only if step 1's numbers say it is still needed)
- Artifact: `<project>/.claude/rules/capability-plan.md`, ≤ 40 lines, a decision table `row-id | task shape → steps (skill/agent/primitive) → gate`. It **replaces** `engineering-roles.md` in that project (two routers = "conflicting instructions, Claude picks arbitrarily" per docs), never sits beside it.
- Two regimes (review S9): saturated project (IPODhan: 157 skills) → rows PLUS an explicit **hide-list** ("not for this project: …"); bare project (gorefer: 0 rules, 1 skill) → rows PLUS a **provision-list** fed to `recommend.py --local`.
- Generator `scripts/capability_advisor.py`: **deterministic v1** — stack detection (`dependency_detection.py`), enabled inventory (meter `--json`), a static row template per stack, project facts. No Sonnet call in v1 (review cut). Emits the rule file + `capability-plan.json` (row ids for the Stop hook) + a content hash; if the owner hand-edits the file, regeneration writes `capability-plan.generated.md` and leaves the owner's file alone (N1).
- **Missing skill → list-and-wait, with an auto-build trigger at 3 recorded firings of that missing row** (review Q6; build-immediately's failure mode is an estate of 240 auto-generated, never-invoked skills each needing evals + registry rows). Build = contract in that repo's worktree via `/synthesize-project --local` / `skill-author-agent`, branch + CI.
- **SessionStart hook (user-level, `async: true` — native, no hand-rolled detachment; default timeout 600 s):** skip on GWD fleet marker; cache keyed by the MAIN worktree (`git worktree list` head) so N worktrees share one plan; fingerprint = manifests + `.claude/` tree + enabled-plugin list (NOT the cache dir — ~240 `temp_git_*` dirs churn it); regenerate when missing / > 7 days / fingerprint changed. First contact: deterministic rows synchronously in < 2 s (N2). Banner: the rows + last week's adherence.
- Gates by data only: a row < 50% adherence for 2 weeks AND rework unchanged → the row is dead, delete it; a row < 50% AND the owner keeps hitting the failure it prevents → PreToolUse gate proposed as a contract.

### Part A — Delete (reversible; after T-395's recount)
- Uninstall plugins with zero usage in 30 days AND no matching stack in the repo registry (candidates: vercel, postman, cloudflare, supabase, desktop-commander, pydantic-ai, telegram — verify each against `repo_registry` first). Reconcile `config/plugin-recommendations.yml` in the same PR.
- **Duplicate-home collapse (fix-loop / writing-plans / brainstorm / code-reviewer-agent in 3–4 namespaces) is a SEPARATE contract** — it touches registry hashes, the dual-home gate, `plugin-recommendations.yml`, and copy-provisioned downstream files (review B4). Not in this plan.
- Cache hygiene: remove the ~240 `temp_git_*` / `temp_subdir_*` dirs under `~/.claude/plugins/cache/` (N3).

### Part D — Measure (the only success criterion)
- **Outcome gate** (review S8): `scripts/measure_outcomes.py` terms — 30-day rework rate, checker/CI first-pass rate — must improve or hold. Adherence % is a **diagnostic, not a target**: "a row at 100% adherence with rework unchanged is a dead row".
- Diagnostics printed weekly in the SessionStart banner: rules loaded at launch (from `InstructionsLoaded` log), specialist-agent share, plan-mode sessions, adherence per row, corrected coverage of the plan's rows.
- `InstructionsLoaded` logging stays wired in one project permanently: it is the only proof that any of these files reach the model.

## 4. Non-goals
- No new always-on prose rule beyond the ≤ 40-line plan. No blocking hook until data demands it. No "use everything".
- Never touches get-work-done fleet-core (frozen); fleet workers skip all of this.
- Calls `recommend.py` / `/synthesize-project` / `/review-new-claude-features`; replaces `engineering-roles.md` per project.

## 5. Build order
0. T-394 + T-396 + T-395 (in flight 2026-08-27 20:40 IST). Land the meter + catalogue with T-395.
1. Rules diet PRs for the 4 saturated repos; `InstructionsLoaded` logging in IPODhan; 2-week measurement.
2. Stop-hook marker telemetry + `capability-row:` convention (user-level hook + one line in the user CLAUDE.md).
3. Part A uninstall + cache hygiene (after the recount).
4. Advisor v1 (deterministic) — only if step 1's readout says the gap persists; pilot on gorefer (bare) and IPODhan (saturated).
5. Week-1 adherence readout → first row deletions / gate contracts.

## 6. Risks (honest)
- Step 1 may fix most of it, making step 4 unnecessary — that is a good outcome, not a risk.
- The `capability-row:` marker is prose-driven too; its edge over the v1 design is that it is one line (telemetry says one-liners get followed) and that unmarked turns are counted honestly as unclassified.
- Owner/fleet split in the meter is a floor; a fleet session marker would fix it — out of scope (fleet-core frozen).
- Windows: all hooks are Python, as the existing user-level hooks are.

## v1 → v2 change log (from the independent review)
- B1 fixed: coverage denominator = enabled plugins (T-395); headline 8.6% withdrawn pending recount.
- B2 fixed: plan now names `engineering-roles.md` as the failed predecessor and REPLACES it; advisor demoted to step 4, conditional on step 1's data.
- B3 fixed: new step 0 — `globs:` → `paths:` across hub + 6 repos with validator inversion and an `InstructionsLoaded` proof (T-394/T-396).
- B4 fixed: duplicate-home collapse split out; uninstall gated on the recount; `plugin-recommendations.yml` reconciliation added.
- S5: native `async: true` hooks; Stop hook reads `last_assistant_message`, never the transcript tail.
- S6: `InstructionsLoaded` logging as a permanent proof, wired before anything is built on rule files.
- S7: keyword classifier dropped; `capability-row:` self-report marker; unmarked = unclassified.
- S8: outcome metrics from `measure_outcomes.py` are the gate; adherence is diagnostic; gameable targets removed.
- S9: hide-list (saturated) / provision-list (bare) regimes.
- S10: cache keyed by main worktree; fingerprint excludes the plugin cache dir; JSONL bucketed by fleet markers.
- Q6: build-missing-immediately → list-and-wait with a 3-firings auto-build trigger.
- N1–N3: hand-edit guard, sync cold-start rows, cache hygiene.
- Cut: Sonnet row-synthesis call in v1.

## Status log
- **2026-08-27 22:10 IST — step 0 DONE, step 1 mechanical part DONE.** #603 meter+catalogue+plan; #604 validator inverted; `globs:`→`paths:` in 5 app repos (KKB archived, local-only). Path-scoping merged: IPODhan 25→20, algochanakya 21→17, firekaro 24→16 rule files at launch (InstructionsLoaded proofs; permanent logging in IPODhan via `D:\Abhay\GetWorkDone\hooks\instructions-loaded-log.py`). `workflow.md` 5-vs-3 retry contradiction resynced from hub in 5 repos (T-402). New mechanism `scripts/check_provisioned_rule_drift.py` (T-401): first run = **86 stale hub-rule copies across 6 repos**, `prompt-auto-enhance-rule.md` RETIRED-but-enforced in all 6. Plugin cache: 188 stale `temp_*` clones removed.
- **OPEN (owner, rule 5):** rules-diet items 1–7 (deletes/trims/merges, 2 policy contradictions, retired-rule deletion) — hub-first, then resync. Queued: T-397. Next after owner reply: 2-week meter readout (no new machinery), then step 2 marker telemetry, then Part A uninstall.
