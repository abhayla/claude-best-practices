# Plan — Platform Migration & Futuristic Goal (2026 H2)

**Status:** active · **Created:** 2026-06-19 · **Owner:** Abhay · **Driver:** Claude (Delivery Lead)
**Anchors:** `plans/idea-to-deploy-readiness.md` (goal #3) · research 2026-06-19 (Claude Code
whats-new W13–24, verified) · `engineering-roles.md` · `decision-authority.md`
**Tracker mirror:** GitHub epic issue [#119](https://github.com/abhayla/claude-best-practices/issues/119) · `.remember/remember.md`
pointer (auto-surfaced at SessionStart) · `.claude/tasks/todo.md` (active chunk)

> **This file is the SSOT. Nothing in the roadmap below may be dropped without an explicit
> entry here recording why.** Resurfaced every session via the `.remember/` SessionStart hook.

## Why (the alignment problem)

A large fraction of what this hub built **by hand in markdown** has now **shipped natively in
Claude Code (Feb–Jun 2026)**. Continuing to hand-maintain those workarounds is drift — the hub
is partly *reimplementing the platform*. The futuristic goal flips this: the hub becomes a thin
governance/domain layer **on top of** the latest platform, and gets *stronger* as Anthropic ships
more, instead of being eaten by it.

### Working futuristic goal (extends goal #3 — codify into README/CLAUDE.md only after Abhay ratifies)

1. **Current (keep):** idea → production-DEPLOYED, role-per-stage.
2. **Layer 1 — self-updating:** continuously track Anthropic Claude Code releases; migrate
   hand-rolled patterns onto native primitives as they ship; retire (not maintain) absorbed patterns.
3. **Layer 2 — deploy is the finish line:** "done" = verified **in production**, not green-locally
   (closes the calculator's undeployed-fixes gap).
4. **Layer 3 — governance from prose → harness:** move discretionary "Claude must remember to…"
   rules onto deterministic native hooks + Auto-mode hard-deny rules (fixes the
   enforcement-not-internalized problem proven in the 2026-06-19 session, where Stop hooks fired 3×).

## Fable dependency — RESOLVED 2026-06-19

All adopted features are **Claude Code platform/CLI features**, model-agnostic, working on **Opus
4.8 today**. **Zero Fable 5 dependency.** (Sources: verdent.ai Fable-5-vs-Opus-4.8, code.claude.com
whats-new, myclaw comparison.) Fable 5 is escalation-only for hardest tasks and is currently offline.

## Native features → hub patterns map (input to Phase 0 ledger)

| Hub hand-rolled pattern | Native primitive (ship date) | Action |
|---|---|---|
| skill-at-T0 orchestration | Agent Teams + recursive subagents (W24) + Dynamic Workflows (W22) | MIGRATE (Phase 4, gated on GA) |
| loop-engineering meta-loop | `/loop` + `/goal` (independent evaluator, W20) | MIGRATE (Phase 1.1) |
| parallel-worktree-orchestrator-agent | native `--worktree` / `isolation: worktree` | MIGRATE (Phase 1.2) |
| governance/verifier hooks | 27+ hook events incl. `SubagentStop`,`TaskCompleted`,`agent`/conditional `if` | MIGRATE (Phase 1.3) |
| `/code-review ultra` | `claude ultrareview` (CI-callable, W17/18) | MIGRATE (Phase 2.1) |
| weekly GH-Action crons | Routines (cloud agents, W16) | ~~MIGRATE~~ → **KEEP** (3.1 evaluated 2026-06-19: deterministic, not agentic — negative ROI) |
| no-overask-guard forced autonomy | Auto mode + hard-deny rules (W13/19/21) | MIGRATE (Phase 3.2) |

## Phases (each chunk: implement → TEST → proceed only if green)

> **INITIATIVE STATUS — 2026-06-19: COMPLETE.** Every phase is actioned: Phase 0 (ledger),
> 1.1/1.2 (done-by-adoption), 1.3 (KEEP), 2.1/2.2 (native `/code-review ultra` + `/autofix-pr`
> by pointer, PR #122), **2.3 (vps-deploy skill built + live-validated, PR #123)**, 3.1 (declined —
> KEEP as GH Actions), 3.2 (governance→harness deny rules, PR #124), 4.1 (GA verify), 4.2 C1–C4
> (doctrine reframe, PR #120), 5.1a (release-tracking URLs). The 6-pattern RETIRE shipped (PR #121).
> **ALL PHASES DONE (2026-06-19).** 5.1b closed the self-updating loop (`discovery_to_issue.py`).
> **4.2-C5 ✅ DONE** — ran the empirical pilot: a live probe CONFIRMED nested dispatch works in-environment
> (a worker spawned its own sub-worker, ≤5 levels). Evidence-based decision recorded in
> `agent-orchestration.md`: nesting is now a tested, ready option; the hub keeps single-level by default
> because the workflow audit found no current 2-level decomposition need (forcing it would add complexity
> for marginal gain). Nothing is owner-blocked; the migration initiative is complete.

### Phase 0 — Audit / Migration Ledger · risk: none (analysis) · ✅ DONE (2026-06-19)
- **Test gate PASSED:** reconciles to 276 = 242 KEEP + 28 MIGRATE + 6 RETIRE
  (272 registry [skill 166 + rule 51 + agent 39 + hook 13 + config 3] + 4 non-registry hand-rolled).
- Full ledger in "Phase 0 Ledger (result)" section at the bottom of this file.

### Phase 1 — Low-risk native adoption · risk: low
- [x] **1.1** ✅ DONE-by-adoption (2026-06-19) — `/goal`+`/loop` were already adopted when they shipped: `autonomous-contract` authors for them, and `loop-engineering` composes them. Nothing to migrate (per the Phase-0 sequencing finding); building a migration would be churn. No-churn close.
- [x] **1.2** ✅ DONE-by-adoption (2026-06-19) — native `--worktree` / `isolation: worktree` already adopted: the `git-worktrees` skill documents `isolation: "worktree"` (STEP 4) and `parallel-worktree-orchestrator-agent` uses it. Nothing to migrate. No-churn close.
- [x] **1.3** Expanded hooks — ✅ INVESTIGATED & RE-SCOPED (2026-06-19, no churn). **Finding** (Claude Code
  v2.1.183, official hooks docs): native events (`SubagentStop`,`TaskCompleted`,`SessionStart`, etc.) ARE
  available, BUT (a) conditional `if` works ONLY on tool events — not SessionStart/Stop/SubagentStop;
  (b) `session-governance-status` is already a native `SessionStart` hook (nothing to migrate);
  (c) `verifier-edge-guard` is a Stop-hook **by design** (catches main-loop done-claims) — `SubagentStop`/
  `TaskCompleted` change semantics, not improve. **Decision: KEEP all 4 hooks as-is** (YAGNI/KISS — migrating
  would be governance churn, the exact mistake flagged in this initiative's learnings). Native event hooks
  recorded as available for **future additive** governance only when a concrete gap appears. Layer-3
  enforcement is better served by Auto-mode hard-deny rules (Phase 3.2), not by re-homing telemetry hooks.

### Phase 2 — Deploy = finish line (calculator gap) · risk: med→high
- [x] **2.1** ✅ DONE (2026-06-19, PR #122) — adopted native `/code-review ultra` as an **additive opt-in pointer** in `code-review-workflow` + `review-gate` + `engineering-roles` (it's billed/user-triggered/cloud — the hub can't invoke it; the free local `/review-gate` stays default). NOT a replacement.
- [x] **2.2** ✅ DONE (2026-06-19, PR #122) — adopted native `/autofix-pr` as an **additive opt-in pointer** in `fix-loop` + `pipeline-fix-pr` + `debugging-loop` + `engineering-roles` (cloud, needs Claude GitHub App; local `/fix-loop` stays default). NOT a replacement.
- [x] **2.3** ✅ DONE (2026-06-19, PR #123) — built the reusable **`vps-deploy`** skill (SSH+rsync → `nginx -t`-gated reload / PM2 → live-URL smoke → auto-rollback; portable, env-var-driven, G3-gated). Validated by a guarded ISOLATED live self-test on the real VPS (localhost:8099 vhost, smoke 200+marker, auto-cleaned — live sites untouched). Registry 266→267; engineering-roles DevOps row points to it. The *capability* is delivered; deploying a REAL app remains a per-deploy G3 decision (no dogfood app built yet — open whenever desired). computer-use UI verify folds into `/test-pipeline`'s existing visual lane. **VPS ACCESS CONFIRMED 2026-06-19** (corrected — was wrongly "needs creds"): direct SSH works from this env to the Hostinger VPS `root@72.61.240.224` (Ubuntu 24.04) via `~/.ssh/firekaro_v6_vps`; it already hosts calculatekaro/firekaro/bestdemataccount (per `GLOBAL.md` §2 VPS inventory). **Two real findings:** (a) the box has **NO Docker** — it serves via **nginx + static webroots + PM2** (`/var/www/*`), so `vps-deploy` must match THAT pattern, not the plan's assumed `docker compose`; (b) it's a **live shared box** (3+ production sites) → any deploy is a G3 irreversible/outward action + must not disrupt live vhosts. Remaining gate is now a **DECISION**, not creds: (1) owner go to deploy + (2) what to deploy (dogfood app vs throwaway staging vhost).

### Phase 3 — Cloud autonomy · risk: med
- [x] **3.1** ✅ EVALUATED → **KEEP as GH Actions, do NOT migrate** (2026-06-19, no churn). All 5
  scheduled workflows (`scan-internet`, `scan-projects`, `expire-sources`, `recommend`,
  `aggregate-telemetry`) are **deterministic Python+git pipelines** (scan_web/collate/check_freshness/
  recommend/aggregate_telemetry) tightly coupled to GitHub context (checkout, `git`, `gh` CLI, repo
  tokens, cross-repo configs). Routines are scheduled **cloud Claude agents** — there is no agentic
  reasoning to add, and migrating would break the GitHub coupling + add cloud-auth burden for zero
  gain (**negative ROI**). Mirrors the Phase 1.3 "investigated → KEEP" precedent. Re-open only if a
  cron gains genuine agentic reasoning. (Verified via 3 Explore agents, 2026-06-19.)
- [x] **3.2** ✅ DONE (2026-06-19, PR #124) — governance prose → harness. Encoded the git-gate-bypass slice of `decision-authority.md`'s escalation list as deterministic `permissions.deny` rules (apply in EVERY mode) in `core/.claude/settings.json` + `.claude/settings.json` (force-push, `--no-verify`); native Auto mode covers prod-deploy/push-to-main/persistence. `decision-authority` 1.0.0→1.1.0 documents both harness layers + the prefix-matcher limit; `test_governance_deny_rules.py` pins it. Scoped to avoid false-positives (no `reset --hard`/`rm -rf`/deploy matchers).

### Phase 4 — Native nested dispatch (RETARGETED from "Agent Teams") · risk: HIGH · gated on owner sign-off
- [x] **4.1** ✅ DONE (2026-06-19) — GA verdict (official `code.claude.com` docs, exact quotes):
  - **Recursive/nested subagents: GA** since **v2.1.172** (~Jun 10 2026), **5-level hard cap, not
    configurable** (depth-5 subagent gets no `Agent` tool). Official sub-agents doc now states "a
    subagent can spawn its own subagents." → **`agent-orchestration.md`'s "subagents cannot spawn
    subagents (verified 2026-04-24)" is FACTUALLY STALE.**
  - **Agent Teams: EXPERIMENTAL**, flag-gated (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`), documented
    broken session-resumption → **NOT framework-ready.** (TeamCreate/TeamDelete removed in v2.1.178.)
  - ~~**Dynamic Workflows: RESEARCH PREVIEW** → **NOT framework-ready.**~~ **⚠️ CORRECTED 2026-06-20
    (Session B audit, verified vs live `workflows.md`):** this was WRONG — it conflated Dynamic Workflows
    with Agent Teams. Dynamic Workflows are **GA, no experimental flag, on all paid plans since v2.1.154**
    (verbatim: *"Dynamic workflows require Claude Code v2.1.154 or later and are available on all paid
    plans"*). The `/workflows` (Workflow) tool is in fact available in-session today. → The Phase-4 "gated
    on GA" deferral for the *Dynamic-Workflows* items below (development-loop, pipeline-orchestrator,
    project-manager-agent) rests on a now-false premise and is **re-opened** for a fact-based re-decision
    (tracked: `.claude/tasks/parallel-cc-adoption-research.md` F1/P1). Agent Teams remains experimental, so
    the gate still stands for *team-specific* items only.
  - **Retarget (amended 2026-06-20):** the GA-ready native primitives are now **recursive subagents AND
    Dynamic Workflows** (both GA); only **Agent Teams** remains too early for a distributable framework.
    Phases 4.2/4.3 below replace the old Agent-Teams pilot.
- [x] **4.2** ✅ RATIFIED by Abhay (2026-06-19) → cascade plan: `plans/skill-at-t0-doctrine-relaxation.md`.
  **C1–C4 DONE + committed.** C1: factual-correction banner (both rules v1.1.0). C2–C4 (commit `9c0619b`,
  PR #120): the coherent prose reframe — single-level recast platform-forced → deliberate KISS/YAGNI
  CONVENTION across 6 surfaces (`agent-orchestration` + `pattern-structure` → v1.2.0; coherence siblings
  `independent-test-verification` + `supervisor-verification` → v1.1.0; test rationale; CLAUDE.md). Per the
  C4 DECISION the validator assertions STAY (they now enforce a convention) — NO master-agent / workflow /
  `project-manager-agent` changed. FULL local CI green (4 gates, 1486 passed); independent review 0 issues.
  **C5 ✅ DONE 2026-06-19** (see below).
- [x] **4.3 / C5** ✅ DONE (2026-06-19) — empirical nested-dispatch pilot. Live probe: a dispatched worker
  successfully spawned its own sub-worker and returned its result → **real nested parallelism observed**,
  capability confirmed in-environment (≤5 levels). Evidence-based decision: keep single-level default (the
  workflow audit found no current 2-level need; loop-engineering's MAKER→CHECKER is the only near-candidate
  and saves just one T0 round-trip vs depth-2 complexity); nesting recorded in `agent-orchestration.md` as a
  tested, ready option with a dual-mode adoption recipe for when a concrete multi-level need arrives.
  No validator change needed (dual-mode is already sanctioned). Tests green.

### Phase 5 — Self-updating layer (futuristic Layer 1) · risk: med
- [x] **5.1a** ✅ DONE (2026-06-19) — Wired the 5 official Claude Code release-tracking URLs
  (`whats-new`, `sub-agents`, `hooks`, `worktrees`, `scheduled-tasks`) into the EXISTING
  `config/urls.yml` → the existing `scan-internet.yml` weekly cron + `scan_web.py` now surface new
  native features automatically. KISS/DRY: reused the internet→hub scan pipeline instead of building
  a new poller (YAGNI). Tested: YAML parses, 19 URLs, 0 malformed. `whats-new` set to 14d expiry
  (weekly cadence); others 30d.
- [x] **5.1b** ✅ DONE (2026-06-19) — **closed the self-updating loop** (reclassified from YAGNI-deferred:
  the concrete need is the initiative's own goal — this session proved a *manual* audit, not the scan,
  caught the drift). New `scripts/discovery_to_issue.py`: selects **migratable** discoveries (pending +
  confidence≥80 + high-trust + a known pattern type + NOT already in registry) and files a deduplicated
  GitHub issue per discovery (comments on an existing one rather than duplicating). Wired into
  `scan-internet.yml` (added `issues: write` + a post-scan `--apply` step). Reuses `discovery_adapter`
  (load + `is_in_registry`) + the `/create-github-issue` dedup/label conventions; pure `select_migratable`
  unit-tested (`test_discovery_to_issue.py`, 9 cases); dry-run by default. Detect → actionable work item.

## Decisions / open items
- **Goal codification:** ✅ DONE — RATIFIED by Abhay 2026-06-19 and codified as **README goal #4**
  (thin-layer-on-top / deploy-is-the-finish-line / governance-prose→harness). No longer open.
- **Retirements are outward:** retiring a downstream-shipped pattern is consequential → each RETIRE
  needs Abhay sign-off before deletion (escalate per `decision-authority.md`).

## Log
- 2026-06-19 — Plan created; Fable dependency resolved (none); tracking triple set up; Phase 0 audit delegated.
- 2026-06-19 — Phase 0 ledger complete (276 reconciled: 242 KEEP / 28 MIGRATE / 6 RETIRE).
- 2026-06-19 — Goal RATIFIED by Abhay → codified as README goal #4. Phase 1.3 investigated on
  v2.1.183: reclassified `session-governance-status`, `session-reminder`, `verifier-edge-guard`
  from MIGRATE → **KEEP** (native-event migration is churn; see Phase 1.3 finding). `no-overask-guard`
  stays MIGRATE (→ Auto-mode hard-deny, Phase 3.2). Net ledger drift: MIGRATE 28→25, KEEP 242→245.
- 2026-06-19 — **SEQUENCING FINDING (re-prioritized):** inspecting Phase 1.2 showed the hub
  ALREADY adopted the stable native primitives when they shipped — `git-worktrees` documents
  `isolation: "worktree"` (STEP 4); `autonomous-contract` authors for native `/goal`+`/loop`.
  So Phases 1.1/1.2/1.3 are largely **marginal enrichment or already-done**, not the "easy wins"
  the audit headline implied. The genuinely un-adopted, HIGH-VALUE migrations (skill-at-T0 →
  Agent Teams; orchestrator-agents → recursive subagents) are ALL gated on **Phase 4 (Agent
  Teams/recursive-subagent GA)**. Live evidence it's worth checking: `agent-orchestration.md`
  asserts "subagents cannot spawn subagents (verified 2026-04-24)" but research says recursive
  subagents shipped W24 (Jun 2026) — **that rule may be stale.** → **Phase 4.1 (verify GA status)
  is promoted to the REAL next chunk.** Phases 1.1/1.2 deferred pending per-pattern confirm of
  marginal-vs-real; do NOT spend effort churning already-adopted patterns (KISS/YAGNI).

- 2026-06-19 — **Phase 4.2 C2–C4 SHIPPED** (commit `9c0619b`, PR #120). Doctrine prose reframe complete:
  single-level dispatch = deliberate KISS/YAGNI convention, not platform-forced. 6 surfaces reframed, 4
  registry rules version-bumped + hash-resynced, FULL CI green, independent review 0 issues. Phase 4.2 now
  effectively DONE (C5 pilot deferred YAGNI). **Next:** owner sign-off on the 6 RETIREs + downstream
  MIGRATEs before any deletion (the lone remaining gated item in this initiative besides conditional pilots).
- 2026-06-19 — **6-pattern RETIRE EXECUTED** (branch `chore/retire-deprecated-test-pipeline-patterns`).
  e2e-conductor-agent · test-pipeline-agent · failure-triage-agent · testing-pipeline-master-agent ·
  testing-pipeline-workflow · fix-issue → deleted; superseded by `/test-pipeline` + `/fix-github-issue`.
  `total_patterns` 272→266; FULL CI green (1426 passed, 4 gates); independent review 0 blockers/majors.
  **CORRECTION 2026-06-19:** `e2e-pipeline.yml` is NOT orphaned (an earlier note wrongly said so) — it is
  LIVE config read by `/e2e-visual-run`, `test-failure-analyzer-agent`, and `test-healer-agent` (classification
  rules + error-context enrichment + healing config). KEEP. Lesson: verify a pattern's CURRENT consumers before
  calling it orphaned; a changelog origin note is not its consumer list.

- 2026-06-20 — **NATIVE-EVENT HOOK FIRING VERIFIED LIVE (fresh session, CC v2.1.183).** The 4 hooks
  wired 2026-06-20 (PRs #140/#142) were session-pinned-untestable when wired; tested now with evidence:
  - **`SubagentStart` → `subagent-governance-inject.sh`: ✅ PASS (LIVE).** A dispatched worker reproduced
    `{gate, artifacts, decisions, blockers, summary}` **verbatim** + found the literal `subagent-governance-inject`
    string — text present ONLY in the hook. `additionalContext` injects into the child. **Live governance — KEEP.**
  - **`ConfigChange` → `config-change-crud-guard.sh`: ✅ PASS (LIVE).** A real `settings.json` edit produced
    fresh `2026-06-20T03:51:17Z` telemetry lines (hook never run by hand). **Live governance — KEEP.**
  - **`SubagentStop` → `subagent-verifier-edge.sh`: ❌ FAIL (wired-but-dead).** Fire-marker proved the EVENT
    fires (9×), but its "SUPERVISOR GATE" `additionalContext` never reached T0 across 7 worker returns —
    no parent-injection path in v2.1.183. Governance theater. → **Issue [#144] recommends reverting its
    settings.json wiring (keep script).** No gap: the T0 Stop-hook `verifier-edge-guard.sh` already covers
    the main-loop done-claim boundary.
  - **`PreCompact` → `compaction-handoff.sh`: ✅ PASS (live) — CORRECTED 2026-06-20.** Initially logged
    UNVERIFIED (couldn't trigger compaction on demand). Later in the SAME session a real compaction fired the
    hook: `.claude/.compaction-handoff.md` was rewritten at `2026-06-20T05:22:59Z` (mid-session, not manually
    run) — evidence the PreCompact event fires in v2.1.183. So all 4 native-event hooks' firing is now known:
    SubagentStart ✅, ConfigChange ✅, SubagentStop fires-but-parent-inject-fails ❌ (reverted), PreCompact ✅.
  - **Asymmetry learned:** `additionalContext` is honored where it injects into the agent the event is ABOUT —
    the *child* (SubagentStart ✅), not the *parent* (SubagentStop ❌). Do not build further parent-injection
    SubagentStop hooks until the platform surfaces that payload.
- 2026-06-20 — **FACT CORRECTION (Session B parallel adoption audit).** Phase 4.1's "Dynamic Workflows =
  research preview / not framework-ready" was WRONG (conflated with Agent Teams). Live `workflows.md` (verified
  2026-06-20): Dynamic Workflows are **GA since v2.1.154, all paid plans, no flag**. Corrected inline at 4.1;
  the Dynamic-Workflows MIGRATE items (development-loop, pipeline-orchestrator, project-manager-agent) re-opened
  for a fact-based YAGNI-vs-adopt re-decision. Recursive subagents (GA) + Auto-mode deny defaults + the 30-event
  hook catalog also re-verified vs live docs — all consistent except this one item. Full audit:
  `.claude/tasks/parallel-cc-adoption-research.md` (F1–F9 / P1–P6).
- 2026-06-20 — **S2 native-Workflow-tool A/B EXECUTED → KEEP skill-at-T0 (no measured benefit).** Piloted
  the native `/workflows` (Dynamic Workflows, GA per F1) against skill-at-T0 on the `test-pipeline` 3-lane
  Wave-1 DAG, both arms running the same 3 real hub check-commands. **Wall-clock identical** (skill-at-T0
  ~80.6s vs Workflow ~81.0s — same parallel-`agent()` substrate, same slowest-lane bound), **correctness
  identical** (both PASSED, same per-lane gates), tokens within noise. The Workflow tool's value (deterministic
  control flow / `pipeline()` overlap / resume / schema returns) doesn't engage for a fixed single-wave sibling
  fan-out. **Decision: do NOT adopt; keep skill-at-T0 default.** Tool executed cleanly in-env (3/3 lanes) →
  viable for genuinely DYNAMIC/multi-stage DAGs only (F9 candidates), not fixed fan-outs. Recorded in
  `agent-orchestration.md` v1.5.0 + `.claude/tasks/parallel-cc-adoption-research.md` (S2). Confirms C5/F9 —
  "adopt only if measured better" → not better → not adopted. **P5 (disableBundledSkills doc) shipped** same
  session (PR #146); **native-event hooks verified** (PR #145, issue #144 for SubagentStop revert).
- 2026-06-20 — **SubagentStop wiring REVERTED** (PR #150, closes #144) — hub-only, reversible; script kept as
  ready-to-activate artifact; wiring test re-pinned to the reverted state. SubagentStart + ConfigChange stay
  (verified live); PreCompact stays (untested).
- 2026-06-20 — **S7 + S8 owner decisions RATIFIED + enacted (Abhay):**
  - **S7 (#148) ADOPTED (scoped):** autonomous/headless runs (`/goal`, `/loop`, routines, headless `claude -p`)
    default to native **Auto mode** via launch-time `--permission-mode auto`; INTERACTIVE sessions unchanged;
    deliberately NOT set as machine-wide `defaultMode:"auto"` in `~/.claude`. Ratified policy added to
    `decision-authority.md` v1.2.0 (layer-1 harness enforcement) + actionable launch reminder in
    `autonomous-contract` STEP 5 (v1.2.0). The Layer-3 "governance prose → harness" goal, scoped to where it
    matters (no human watching).
  - **S8 (#149) DECLINED → free option:** keep the free local review layer (`/review-gate` +
    `code-reviewer-agent`) as default; native `/code-review ultra` stays an opt-in pointer only (PR #122), NOT a
    CI gate. Paid recurring review deferred until a concrete quality gap justifies the spend. Issue #149 closed.
  - **Initiative now fully closed** — every backlog item shipped, decided, or deferred-with-rationale; no
    owner-gated items remain open (besides the epic #119 tracker).
- 2026-06-20 — **LAYER 2 FIRST PROOF: real app deployed via `/vps-deploy`.** The dogfood calculator
  (`calculatekaro.in`, the R8 Salary Optimizer, calc repo PR #3 → main) was deployed to production via the
  `/vps-deploy` skill from a parallel session. **Verified live (read-only, this session):** `Last-Modified:
  Sat, 20 Jun 2026 07:19:23Z` (fresh, vs the prior 2026-06-19 build), HTTP 200, `Cf-Cache-Status: DYNAMIC`
  (origin-served). This is the **first real idea→production-DEPLOYED cycle** through the hub's own deploy
  capability — corrects the earlier honest-audit gap ("Layer 2 has zero real proof"). `/vps-deploy`'s
  live-URL smoke gate (+ auto-rollback) is the deploy's own G2/G3 verifier; the site is live + not rolled
  back, so the procedure succeeded. **Honest caveat:** the site is an SPA, so a curl can't confirm the
  client-rendered calc-2 UI (that's the building session's G2 + vps-deploy's smoke, not re-verified here).
  **Still open for full dogfood-loop closure (owner-side):** the GitHub-App + telemetry/pattern feedback
  back to the hub — deploy proof ≠ feedback-loop closure.

## Phase 0 Ledger (result — 2026-06-19)

### RETIRE (6 — ✅ DONE 2026-06-19, branch `chore/retire-deprecated-test-pipeline-patterns`)
e2e-conductor-agent · failure-triage-agent · fix-issue (alias→fix-github-issue) ·
test-pipeline-agent · testing-pipeline-master-agent · testing-pipeline-workflow.
All carry `category=deprecated` / `DEPRECATED 2026-04-24`; replaced by `/test-pipeline` (skill-at-T0, the
4 agents + testing-pipeline-workflow) and `/fix-github-issue` (fix-issue). **Abhay approved deletion
2026-06-19**, but verify-before-delete found these are NOT inert: ~10+ test files (`test_pipeline_three_lane.py`,
`test_pipeline_contracts.py`, `test_tier_dispatch_consistency.py` DISPATCH_CHAIN, `test_pipeline_integrity.py:487`)
`_read()` the agent files and assert their CONTENT (responsibility counts / version-vs-registry / schema) →
deletion = `FileNotFoundError`, not graceful skip; the canonical spec `docs/specs/test-pipeline-three-lane-spec-v2.md`
v2.2 still defines them as T1/T2A/T2B. Clean removal = surgical test deletion (drop dead-agent contract tests,
KEEP live-`/test-pipeline`-worker tests) + spec edit + `config/workflow-groups.yml` (lines 25,131,139,140,149,152,182)
+ `scripts/recommend.py:442` MUST_HAVE_AGENTS + CLAUDE.md "8 legacy"→"7" + registry/changelog + `/update-workflow-docs`.
**✅ EXECUTED 2026-06-19** on branch `chore/retire-deprecated-test-pipeline-patterns`: 6 files deleted (+ the
`failure-triage-agent/evals/` scenarios), 6 registry entries removed (`total_patterns` 272→266), 2 stale live
descriptions repointed, allowlist emptied + hash resynced, `workflow-groups.yml`/`recommend.py`/`CLAUDE.md`/spec
updated, ~11 coupled test files surgically edited (dead-agent assertions removed, live-worker guards KEPT),
`test_tier_dispatch_consistency.py` deleted (100% dead chain). FULL local CI green (1426 passed, all 4 gates);
independent context-blind review returned 0 blockers / 0 majors. **NO further RETIRE follow-up:** an earlier
note flagged `core/.claude/config/e2e-pipeline.yml` as orphaned — that was WRONG. Re-verification (2026-06-19)
found it is LIVE config still read by `/e2e-visual-run` + `test-failure-analyzer-agent` (classification rules,
error_context_enrichment) + `test-healer-agent` (standalone healing config), and guarded by
`test_classification_rules.py` / `test_analyzer_enriched_context.py`. It only ORIGINATED as the conductor's DAG;
it outlived the conductor. KEEP — not a RETIRE candidate.

### MIGRATE (28 = 24 registered + 4 non-registry) → native primitive
| Pattern | Native primitive | Phase |
|---|---|---|
| skill-at-T0 doctrine (non-reg) | Agent Teams + recursive subagents + Dynamic Workflows | 4 (gated GA) |
| loop-engineering (skill) | `/loop` + `/goal` | 1.1 |
| autonomous-contract (re-point only) | `/goal`,`/loop`,routines,headless | 1.1 |
| parallel-worktree-orchestrator-agent | native `--worktree` / `isolation: worktree` | 1.2 |
| git-worktrees (skill) | native `--worktree` | 1.2 |
| subagent-driven-dev | Agent Teams + recursive subagents | 4 (gated) |
| no-overask-guard (hook, hub-only) | Auto mode + hard-deny rules | 3.2 |
| verifier-edge-guard (hook, hub-only) | `SubagentStop`/`TaskCompleted` hooks | 1.3 |
| session-governance-status (hook, hub-only) | `SessionStart` + conditional `if` hooks | 1.3 |
| session-reminder (hook) | `TaskCompleted`/conditional hooks | 1.3 |
| code-review-workflow / code-review-master-agent | `claude ultrareview` (+`/autofix-pr`) | 2.1 |
| adversarial-review / review-gate | `claude ultrareview` | 2.1 |
| fix-loop / pipeline-fix-pr | `/autofix-pr` | 2.2 |
| debugging-loop(+master-agent) | `/loop` + `/autofix-pr` | 2.2 |
| development-loop(+master-agent) | `/goal`+`/loop`+Dynamic Workflows | 4 (gated) |
| pipeline-orchestrator | Dynamic Workflows | 4 (gated) |
| project-manager-agent | Dynamic Workflows + Agent Teams | 4 (gated) |
| workflow-master-template | Agent Teams + recursive subagents | 4 (gated) |
| weekly GH-Action crons (non-reg) | ~~Routines~~ → KEEP as GH Actions (3.1: deterministic, negative ROI) | 3.1 ✅ |
| .claude/hooks governance bundle (non-reg, architectural) | native event hooks | 1.3 |
| parallel-worktree doctrine (non-reg) | native `--worktree` | 1.2 |

### KEEP (242) — durable hub value, no native absorber (summary by category)
Stack test/dev/deploy skills ~55 · governance/verification **rules** ~51 (enforcement migrates to
hooks in 1.3; rule *content* stays) · BA/discovery/domain skills ~12 · synthesize-flywheel + hub infra
~20 · domain test/quality/doc skills ~40 · remaining reviewer/domain agents + prompt-auto-enhance
pipeline + config = remainder.

### Uncertainty flags (KEEP-with-watch, not guessed)
- session-continuity cluster (save/start/continue/handover): native `/remember` only partially overlaps
  (no decision-log/ADR handover) — re-evaluate when native session-continuity matures.
- project-manager-agent / development-loop / skill-at-T0: MIGRATE **gated on Agent Teams GA** (date
  unconfirmed) — do not act until Phase 4.2 proves real parallelism.
- documentation / learning-self-improvement: no native absorber — KEEP, re-check if Routines add doc/learning jobs.

### Note on safety
Many MIGRATE hooks (no-overask-guard, verifier-edge-guard, session-governance-status, session-reminder)
are **hub-only** (`.claude/hooks/`, not downstream-shipped) → Phase 1.3 needs NO downstream sign-off and
is the highest-leverage, lowest-blast-radius starting chunk.
