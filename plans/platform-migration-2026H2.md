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
| weekly GH-Action crons | Routines (cloud agents, W16) | MIGRATE (Phase 3.1) |
| no-overask-guard forced autonomy | Auto mode + hard-deny rules (W13/19/21) | MIGRATE (Phase 3.2) |

## Phases (each chunk: implement → TEST → proceed only if green)

### Phase 0 — Audit / Migration Ledger · risk: none (analysis) · ✅ DONE (2026-06-19)
- **Test gate PASSED:** reconciles to 276 = 242 KEEP + 28 MIGRATE + 6 RETIRE
  (272 registry [skill 166 + rule 51 + agent 39 + hook 13 + config 3] + 4 non-registry hand-rolled).
- Full ledger in "Phase 0 Ledger (result)" section at the bottom of this file.

### Phase 1 — Low-risk native adoption · risk: low
- [ ] **1.1** Adopt `/goal`+`/loop`; validate against loop-engineering. Test: tiny self-paced loop self-terminates.
- [ ] **1.2** Native `--worktree` / `isolation: worktree`; document + wire into worktree patterns. Test: 2 parallel worktree agents, no file collision.
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
- [ ] **2.1** `claude ultrareview` (CI-callable) into testing-pipeline. Test: buggy branch → findings returned.
- [ ] **2.2** `/autofix-pr` into fix-loop. Test: PR with failing test → auto-fix applied.
- [ ] **2.3** computer-use UI verify + `vps-deploy` (Unit 3 of idea-to-deploy-readiness). Test: throwaway deploy, live smoke + rollback. **Needs Abhay's VPS creds — escalate at deploy.**

### Phase 3 — Cloud autonomy · risk: med
- [ ] **3.1** Migrate crons (`scan-internet.yml` etc.) → Routines. Test: one routine fires in cloud.
- [ ] **3.2** Auto-mode hard-deny rules: encode irreversible-action escalation list deterministically. Test: denied op blocked.

### Phase 4 — Agent Teams replaces skill-at-T0 · risk: HIGH · **PROMOTED to next real chunk (2026-06-19)**
- [ ] **4.1** ⏳ IN PROGRESS — Verify GA status of Agent Teams + recursive subagents. CRITICAL: if
  recursive subagents are GA, `agent-orchestration.md` ("subagents cannot spawn subagents, verified
  2026-04-24") is STALE and the entire skill-at-T0 doctrine needs revisiting. This gates the bulk of
  the high-value migrations. Verify against official `code.claude.com` docs (sub-agents + whats-new).
- [ ] **4.2** Pilot ONE workflow A/B vs current skill-at-T0. Test: real parallelism observed.
- [ ] **4.3** Rewrite CLAUDE.md skill-at-T0 rationale **only after** 4.2 proves parallelism.

### Phase 5 — Self-updating layer (futuristic Layer 1) · risk: med
- [x] **5.1a** ✅ DONE (2026-06-19) — Wired the 5 official Claude Code release-tracking URLs
  (`whats-new`, `sub-agents`, `hooks`, `worktrees`, `scheduled-tasks`) into the EXISTING
  `config/urls.yml` → the existing `scan-internet.yml` weekly cron + `scan_web.py` now surface new
  native features automatically. KISS/DRY: reused the internet→hub scan pipeline instead of building
  a new poller (YAGNI). Tested: YAML parses, 19 URLs, 0 malformed. `whats-new` set to 14d expiry
  (weekly cadence); others 30d.
- [ ] **5.1b** (enhancement, deferred — YAGNI until 5.1a proves insufficient) auto-open a GitHub
  issue when a discovery maps to a migratable hub pattern. The scan pipeline currently emits
  discovery reports (`config/discoveries.json` + `/scan-discovery-report`); wiring discovery→issue
  is a further step, only if the reports alone don't surface migrations reliably.

## Decisions / open items
- **Goal codification:** the 3-layer goal stays in THIS plan until Abhay ratifies wording; only then
  promote to README/CLAUDE.md as the official north-star.
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

## Phase 0 Ledger (result — 2026-06-19)

### RETIRE (6 — all already deprecated; safe, but each is downstream-shipped → Abhay sign-off before deletion)
e2e-conductor-agent · failure-triage-agent · fix-issue (alias→fix-github-issue) ·
test-pipeline-agent · testing-pipeline-master-agent · testing-pipeline-workflow.
All carry `category=deprecated` / `DEPRECATED 2026-04-24`; platform direction + ultrareview absorb them.

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
| weekly GH-Action crons (non-reg) | Routines (cloud agents) | 3.1 |
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
