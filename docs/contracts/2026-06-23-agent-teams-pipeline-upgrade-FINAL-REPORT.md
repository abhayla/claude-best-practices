# Final Report — Agent-Teams Pipeline Upgrade

**Contract:** `docs/contracts/2026-06-23-agent-teams-pipeline-upgrade.md`
**Run:** supervised → authorized-autonomous, branch `auto/agent-teams-pipeline-upgrade` (worktree-isolated)
**Date:** 2026-06-23
**Verdict:** **Upgrade COMPLETE** (all A3 workflows team-ready, best-practices baked in, CI green) with an
**honest reliability caveat** on the risky Execute (parallel-edit) tier — see §Reliability.

---

## 1. What shipped, per stage (commit SHAs)

| Stage | Commit | What shipped |
|---|---|---|
| A — harness + provisioning | `40440ba` | 4 team patterns flipped `nice-to-have → must-have` (dormant; §3a env-var master switch); rule `EXPERIMENTAL_AGENT_TEAMS` self-gate; 3 `team-*` hooks wired pre-but-inert in `core/.claude/settings.json`; best-practice acceptance standard recorded in §12 |
| B — Verify (review team) | `ae3cbaa` | `code-review-workflow` `--team` (STEP 2-TEAM); 3 review agents teammate-ready (security-auditor teammate note). LIVE-VALIDATED |
| C+D — Execute + remaining | `4e6b57f` | `development-loop` STEP 4-TEAM (canonical parallel-build); `executing-plans`/`implement` pointers; `brainstorm` advisor-panel, `research-mode` parallel-research; `writing-plans` team-compatible; 2 verification rules self-gated. Execute LIVE-VALIDATED |
| Verify remainder | `1e23579` | `review-gate` + `auto-verify` `--team`; `output-plausibility-verification` teammate clause; final §12 ticks |

## 2. Skipped (already covered — §0.2 preflight)

- All 4 team scaffolding patterns (`agent-team-selection` rule + 3 `team-*` hooks) already existed (built in the prior session) — Stage A only flipped their tier + wired the hooks; the calibrated hooks were NOT regressed.
- `code-reviewer-agent`, `tester-agent`, `plan-executor-agent`, `planner-researcher-agent`, `web-research-specialist-agent`: teammate-readiness audit PASSED with **no edit needed** (no `skills`/`mcpServers` frontmatter reliance; sufficient `tools`).
- `code-quality-gate` / `architecture-fitness` / `security-audit`: covered as teammates under `review-gate` `--team` (no per-skill edit).

## 3. Best-practice compliance checklist (items 1–8 × each team-mode workflow)

Source: `docs/claude-references/multi-agent-best-practices.md` §A–§H. ✓ = satisfied; N/A = not applicable to that tier; ☐doc = documented in the skill but not separately live-exercised.

| Workflow (mode) | 1 Task-shape | 2 File-partition | 3 Anti-conflict | 4 Doer≠checker | 5 Hooks | 6 Context | 7 Sizing/cost | 8 Teammate-audit |
|---|---|---|---|---|---|---|---|---|
| `code-review-workflow --team` (B, LIVE) | ✓ (TaskCreated payloads shaped) | N/A (read-only) | ✓ (lead synthesizes) | ✓ (cross-challenge + separate verifier documented) | ✓ (12 events, honest audit) | ✓ (all ctx in spawn) | ✓ (2–4 reviewers) | ✓ (3 agents) |
| `development-loop --team` (C, LIVE) | ✓ | ✓ (disjoint claim sets + worktree isolation, **zero collisions** verified) | ✓ (lead waits) | ✓ (read-only `verify` teammate ran tests) | ✓ (hooks fired) | ✓ | ✓ (3–4 members) | ✓ (2 agents) |
| `review-gate --team` (doc) | ✓ | N/A | ✓ | ✓ | ☐doc | ✓ | ✓ | ✓ |
| `auto-verify --team` (doc) | ✓ | N/A | ✓ | ✓ (independent-test-verification at boundary) | ☐doc | ✓ | ✓ | ✓ |
| `brainstorm --team` advisor-panel (doc) | ✓ | N/A | ✓ | ✓ (panel cross-dispute) | ☐doc | ✓ | ✓ | N/A |
| `research-mode --team` (doc) | ✓ | N/A | ✓ | ✓ | ☐doc | ✓ | ✓ | ✓ |

Two workflows (review-team B, build-team C) were **live-validated**; the read-only Clarify/Verify variants are documented against the same proven discipline and self-gated (lower risk, no parallel edits).

## 4. Reliability (live `claude --bg` validation runs)

| Team | Runs | Real team (members>1 + hooks) | Build/output correctness | Zero same-file collision | Autonomous end-to-end completion |
|---|---|---|---|---|---|
| Review (B) | 1 | ✓ members=3, 12 hooks | usable review, real cross-challenge | N/A (read-only) | **1/1 clean** |
| Execute (C) | 3 | ✓ all 3 (members=4) | **3/3** (10 tests pass each) | **3/3** (disjoint claims; `claimed==src`) | **1/3 clean** (run-1 clean; run-2 lead self-recovered an *environmental* commit-less-repo worktree blocker = rescue; run-3 build validated but lead **paused for a merge decision** instead of auto-completing) |

**Honest finding:** the team MECHANISM is reliable — every run formed a real team and produced a
**correct, collision-free** result. What is NOT yet reliable is **fully-autonomous end-to-end completion**
of the risky parallel-edit tier (1/3 clean) — the variance lives in the **integration/decision step**
(merge worktree → main, or pause), not in the partitioned build. This is **below the contract's A2
≥2/3-no-rescue bar** for the Execute tier. The review/research read-only teams carry no such risk.

**Recommendation (matches the contract's open owner-decision):** ship all `--team` modes **documented,
self-gated, default-OFF** (already the case) and flag the **Execute `--team` tier as supervised-recommended**
(a human confirms the integration step) until the merge/complete step is hardened — rather than trusting it
for unattended end-to-end runs. Read-only review/research teams are safe to use unsupervised once ground-truth-verified.

## 5. Token cost vs flat-subagent baseline

Not precisely instrumented this run (the `--bg` sessions were not launched with `--output-format json`, so
per-run `total_cost_usd` was not captured — a **measurement gap**, recorded honestly). Per the bake-in
standard (§F/§H6), an agent team costs **~4–7× tokens** vs a single session (≈4× at init alone, each teammate
reloads project context), scaling ~linearly with active teammates. The review/build teams ran 3–4 members each,
so ≈4–7× a flat subagent for the same task. **Implication:** teams pay off only for genuinely team-shaped work
(parallel review that cross-challenges, independent parallel modules) — the `agent-team-selection` rule + every
`--team` self-gate enforce "flat subagent is the default; team only when workers must challenge each other."

## 6. Learnings to fold back (PROPOSE-only — route per `learnings-routing.md`)

1. **GENERIC (process) — check dual-home class before editing a `core/` resource.** Editing only the `core/`
   copy of a `synced` dual-home resource (`executing-plans`) silently drifts the `test_dual_home_sync` gate.
   *Proposed home:* a one-line note in `docs/HUB-CORE-SYNC.md` / the editing checklist: "before editing a
   `core/.claude/` pattern, grep `config/dual-home-resources.yml` — if `synced`, edit BOTH copies (or
   `sync_dual_home.py`)." (Gate already exists; this is the human-facing reminder.)
2. **GENERIC (capability) — `claude --bg` forms real teams reliably; headless `-p` does not.** Confirmed again
   (4 launches, 4 real teams). The reliability gap is end-to-end *completion* of parallel-edit teams, not formation.
3. **PRODUCT (this contract) — parallel-edit team integration step needs hardening.** The merge-worktree-to-main /
   "am I done?" decision is where autonomous runs stall or ask. A future hardening: give the build-team lead an
   explicit "merge + report, do not pause" completion contract, or a Stop-hook that auto-finalizes a validated build.
4. **GENERIC (harness) — instrument `--bg` team cost.** Launch validation teams with cost capture so reliability/cost
   is measured, not estimated. (Closes the §5 measurement gap.)

These are PROPOSE-only — not auto-applied. Owner approves routing.

## 7. Run-end SUMMARY

- **DONE:** All A3 required workflows upgraded to team-ready (Clarify: brainstorm, research-mode; Execute:
  development-loop, executing-plans, implement + 2 agents; Verify: code-review-workflow, review-gate, auto-verify
  + 4 agents; 2 of the 4 live-validated). Multi-agent best-practices baked in + verified per the §3 checklist.
  4 team patterns must-have-dormant + hooks pre-wired-but-inert + rule self-gated. Full local CI green every stage
  (3 validators + pytest 1591 passed). §12 tracker all ✅. Defect found+fixed (dual-home drift) with sibling audit.
- **PENDING:** none blocking the upgrade. Optional follow-ups: live-validate the read-only Clarify/Verify `--team`
  variants (currently documented); wire a trust-score ledger entry; instrument team token cost.
- **BLOCKED / BELOW-BAR:** Execute (parallel-edit) team **autonomous end-to-end completion = 1/3** (below the A2
  ≥2/3 bar) — mechanism proven, completion/integration step needs hardening; recommend supervised use of that tier.
- **NEXT (handoff to the monitoring session):** build the TODO tracker USING these upgraded workflows as a
  real-world validation harness (out of THIS contract's scope; tracked in
  `docs/specs/agent-teams-measure-first-experiment-spec.md`) — and when that build surfaces a workflow defect,
  fix the workflow and continue. Start with a read-only `--team` review on the TODO build's first PR (the
  reliable tier), and keep the Execute `--team` tier supervised until its integration step is hardened.

**Goal declaration:** the upgrade-and-bake-in goal is **COMPLETE**; the honest reliability measurement
(Execute autonomous-completion below bar) is recorded above and carried into the owner's keep-supervised decision.
