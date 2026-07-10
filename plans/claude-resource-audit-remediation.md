# Claude-Resource Audit Remediation Program

**Status:** ✅ COMPLETE (2026-07-03) — all 12 issues CLOSED + merged; #187 intentionally OPEN (spike done, pilot owner-gated).
- **P0** #279 ✅ PR #292 · **P1** #281/#286/#289/#284 ✅ PR #294 · **P2** #285/#287 ✅ PR #295, #282 ✅ PR #296, #288 ✅ closed (not-a-bug), #196 ✅ PR #297+#300 (firewall test + honest auto-accrual, shadow-mode)
- **P3** (owner-approved "do your recommended option on all four"): #290 ✅ PR #301 (ceremony downgrade mandatory→sampled), #283 ✅ closed (reactive-defer), #187 ✅ spike PR #299 (GO-WITH-CAVEATS → pilot cbp-workflows; build is the owner-gated next step)
- **Restart needed:** #290's plugin change (0.3.0) needs `/plugin update prompt-auto-enhance` + one restart to take effect (like #279).
**Created:** 2026-07-03  ·  **Owner:** Abhay (gates) + Claude (execution)
**Source:** 7-way parallel read-only audit of every Claude resource (170 skills, 36 agents, 55 rules, 21 hooks, 285 registry keys). Findings filed as issues **#281–#290** + evidence added to open **#279** (enhance-guard) and **#196** (trust-score).

## Guiding principles (decided with owner 2026-07-03)
1. **Fix a CLASS with a shared GATE, not a per-resource auto-rewriter.** A checker *catches*; it does not silently rewrite a resource. Add/wire a shared gate (test/hook/CI) where the issue IS "the gate is missing" — do NOT staple a bespoke validator onto every skill (170-validator maintenance tax = YAGNI).
2. **The loop + a human PR do the actual fixing.** Every fix runs via `/loop-engineering` (headless, **sonnet** per `.claude/rules/model-routing.md`) in an isolated worktree → CI-gated PR → **T0 supervisor reproduces the gate + inspects the diff** → owner-visible land. No silent auto-edits to governance.
3. **Measure before adding a heavy always-on checker.** The enhance-card guard (#290/#279) is the live cautionary example — an over-firing checker is negative value. Instrument, then decide.
4. **Discovery is done; this is execution.** Each phase item = one tracked issue with a machine-checkable DoD; land CI-gated; nothing merges red.

## Phased sequence (value × risk × dependency)

### P0 — Unblock ourselves (do FIRST; it taxes every turn)
- **#279** — enhance/overask guard *card-detection* false-positives. Fix: detect a markdown table-row (`^\|.*reviewer.*\|`) instead of brittle prose tokens; port the plugin's Overall-row check into the hub guard (H2); handle client-expanded slash commands (H4); add a hub↔plugin dual-home consistency gate (H6). TDD: the #278 discriminating test must still pass. Plugin edit ⇒ version bump + `/plugin-lifecycle` + reinstall + restart to actually take effect.
  *Why first:* stops the false STOP-blocks disrupting every subsequent fix.

### P1 — Clean quick-wins (small, low-risk, high signal)
- **#281** — Update-Docs CI fails 100% (pushes to protected `main`). Fix: final step `git push` → `gh pr create` gated by `validate`. Self-contained.
- **#286** — `workflow.md` Step 5 contradicts `claude-behavior.md` rule 15. Fix: rewrite Step 5 as a one-line pointer to rule 15 / `/fix-loop`.
- **#289** — delete 7 deprecated `*-master-agent` files (2 mo past window) + registry entries + docs regen.
- **#284** — onboarding "Option B" contradiction (README vs GETTING-STARTED); consolidate to one SSOT, drop the deprecated bootstrap path.

### P2 — Wire the dormant gates (the strategic core: "designed but not wired")
- **#196** — wire `collect_signals.py` into the Stop hook / branch-finish so trust-score (G5 north-star) accrues passively; reconcile the inconsistent ledgers. *(This is a GATE-wiring fix — matches principle 1.)*
- **#282** — add the eval-coverage touch-trigger gate (PreToolUse/CI: SKILL.md changed but evals/ absent/older ⇒ warn/block) so coverage ratchets; then start covering highest-centrality skills.
- **#285** — add explicit least-privilege `tools:` + `dispatched_from:` to the 4 tool-less agents; change `test_orchestrator_tool_grants.py` skip→fail so it can't recur.
- **#287** — extend `workflow_quality_gate` glob to the hub-only `.claude/skills/` tree; add an aggregate global-rule line-budget CI check.
- **#288** — verify `scan-internet.yml` isn't a silent no-op; investigate why telemetry sync-manifests aren't populating adoption signal.

### P3 — Strategic / judgment (owner-gated decisions, not mechanical)
- **#290** — instrument blind-reviewer Overall-vs-self divergence across N turns; if rare, **downgrade the per-turn enhance ceremony from mandatory → sampled** (needs owner sign-off — changes a standing behavior).
- **#283** — stack-coverage gap (Go/Rust/Rails/Django). Reactive per `rule-curation.md`: build when a real downstream project on that stack appears; do NOT speculatively build now.
- **#187** — (open) migrate distribution copy-provision → native plugin model, workflow by workflow (loop-engineering already proved it). Strategic, incremental.

## Execution method (per item)
1. `/goal-creator`-style contract (or reuse the issue body) with a machine-checkable DoD.
2. `/loop-engineering <contract> --max-cycles N` headless on **sonnet** in a dedicated worktree.
3. Loop: maker builds → **separate** checker reviews raw diff → loop reproduces gate → self-heals under budget.
4. **T0 supervision:** reproduce the new test + full suite (baseline 1631+) + validators; inspect diff for scope creep.
5. Land CI-gated PR (auto-merge on green); re-provision/plugin-bump where dual-home; close the issue with evidence.
6. Batch P1 items may share one loop-run; P2/P3 one issue per run.

## Definition of done (program)
- Each issue closed via a merged CI-green PR whose diff a T0 supervisor reproduced.
- Every "add a gate" fix ships the gate + a failing-then-passing test proving it fires.
- No governance resource auto-rewritten unsupervised; every change landed through a human-visible PR.
- P3 items carry an explicit owner decision recorded here before execution.

## Session note
Recommended to run in a FRESH session (this one is long + context-polluted + the enhance-guard is looping). The kickoff prompt lives with the owner; this file + `.remember/remember.md` are the resume anchors. After P0 (#279) lands + the plugin is reinstalled, restart once so the fixed guard takes effect for the remaining phases.
