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

### Phase 0 — Audit / Migration Ledger · risk: none (analysis) · ⏳ IN PROGRESS (delegated 2026-06-19)
- Tag every registered pattern (registry total = 272) + each hand-rolled workaround: **KEEP**
  (durable domain/governance value), **MIGRATE** (re-home onto a native primitive), **RETIRE**
  (platform absorbed it). Output: ledger table appended to this file.
- **Test gate:** every pattern accounted for; KEEP+MIGRATE+RETIRE count == registry total.

### Phase 1 — Low-risk native adoption · risk: low
- [ ] **1.1** Adopt `/goal`+`/loop`; validate against loop-engineering. Test: tiny self-paced loop self-terminates.
- [ ] **1.2** Native `--worktree` / `isolation: worktree`; document + wire into worktree patterns. Test: 2 parallel worktree agents, no file collision.
- [ ] **1.3** Expanded hooks (`SubagentStop`,`TaskCompleted`,conditional `if`,`agent` hooks): re-home governance hooks onto deterministic events. Test: trigger event, hook fires. **Directly fixes Layer-3 enforcement gap.**

### Phase 2 — Deploy = finish line (calculator gap) · risk: med→high
- [ ] **2.1** `claude ultrareview` (CI-callable) into testing-pipeline. Test: buggy branch → findings returned.
- [ ] **2.2** `/autofix-pr` into fix-loop. Test: PR with failing test → auto-fix applied.
- [ ] **2.3** computer-use UI verify + `vps-deploy` (Unit 3 of idea-to-deploy-readiness). Test: throwaway deploy, live smoke + rollback. **Needs Abhay's VPS creds — escalate at deploy.**

### Phase 3 — Cloud autonomy · risk: med
- [ ] **3.1** Migrate crons (`scan-internet.yml` etc.) → Routines. Test: one routine fires in cloud.
- [ ] **3.2** Auto-mode hard-deny rules: encode irreversible-action escalation list deterministically. Test: denied op blocked.

### Phase 4 — Agent Teams replaces skill-at-T0 · risk: HIGH · gated
- [ ] **4.1** Verify Agent Teams GA status (research caveat: GA date unconfirmed).
- [ ] **4.2** Pilot ONE workflow A/B vs current skill-at-T0. Test: real parallelism observed.
- [ ] **4.3** Rewrite CLAUDE.md skill-at-T0 rationale **only after** 4.2 proves parallelism.

### Phase 5 — Self-updating layer (futuristic Layer 1) · risk: med
- [ ] **5.1** Routine polls `code.claude.com/docs/en/whats-new` weekly, diffs a tracked baseline, auto-opens an issue when a new feature can absorb a hub pattern. Test: detects current baseline on first run.

## Decisions / open items
- **Goal codification:** the 3-layer goal stays in THIS plan until Abhay ratifies wording; only then
  promote to README/CLAUDE.md as the official north-star.
- **Retirements are outward:** retiring a downstream-shipped pattern is consequential → each RETIRE
  needs Abhay sign-off before deletion (escalate per `decision-authority.md`).

## Log
- 2026-06-19 — Plan created; Fable dependency resolved (none); tracking triple set up; Phase 0 audit delegated.
