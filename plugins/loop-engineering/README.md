# loop-engineering

**The hub's proven autonomous meta-loop, packaged as a plugin.** Author a contract describing a
Definition of Done, hand it to `/loop-engineering`, and the loop runs DISCOVER → PLAN → EXECUTE →
VERIFY → (SHIP | FEEDBACK) unattended — dispatching a MAKER worker to do the work and a SEPARATE
CHECKER to grade it (so the author never grades its own output), self-healing through `/fix-loop`
or `/debugging-loop` when verification fails, and self-learning via `/learn-n-improve` every cycle.
Installing this plugin gives a downstream project the loop's **full dependency closure** in one
shot — no missing-worker preflight blocks, no hunting through the hub for the skills it calls.

## Install

```
/plugin install loop-engineering
```

(from this repo's marketplace — `plugins/.claude-plugin/marketplace.json`).

## Quickstart

1. Author a contract: `/goal-creator` — walks you through a Definition of Done the loop can verify
   against (terminal signals, gates, budgets).
2. Run the loop against it: `/loop-engineering <contract-path> --max-cycles N`.
3. Watch it work: each cycle plans, executes via a MAKER, verifies via an independent CHECKER, and
   either ships, self-heals, or escalates with a structured report — never silently stalling.

## What's included

| Type | Name | Role in the loop |
|---|---|---|
| Skill | `loop-engineering` | The orchestrator — runs at T0, drives the cycle, dispatches MAKER/CHECKER |
| Skill | `goal-creator` | Authors the Definition-of-Done contract the loop verifies against |
| Skill | `git-worktrees` | Isolates the MAKER's work so parallel/loop cycles never collide on disk |
| Skill | `auto-verify` | Independent verification pass (the CHECKER's strict gate) |
| Skill | `fix-loop` | Self-healing: analyze → fix → retest until green, under budget |
| Skill | `debugging-loop` | Self-healing for unclear-root-cause failures (routes to systematic-debugging) |
| Skill | `systematic-debugging` | Structured reproduce → isolate → hypothesize → evidence → fix → verify |
| Skill | `learn-n-improve` | Self-learning — captures error→fix→lesson patterns each cycle |
| Skill | `escalation-report` | Self-feedback — structured report when a budget is exhausted |
| Skill | `post-fix-pipeline` | Runs after a successful fix to close out the cycle |
| Skill | `status` | Reports current loop/cycle state |
| Skill | `writing-plans` | Produces the EXECUTE-phase plan the MAKER follows |
| Skill | `brainstorm` | Used when DISCOVER needs to widen the option space before planning |
| Agent | `plan-executor-agent` | Default MAKER — executes the plan in isolation (worktree) |
| Agent | `code-reviewer-agent` | Default CHECKER — independently reviews the MAKER's output |

## Provenance

Hardened through **5 eval rounds** (v1.2.0 → v1.2.3, PRs #260–#265): round-1 found 13 defects,
round-2 fixes surfaced 15 new, round-3 closed 2 MAJORs, round-5 verification passed with all 10
findings (V1–V10) closed and the finding trajectory converged (13 → 15 → 10 → 2-minor). Then
**live pilot-tested end-to-end in the noter-app project (2026-07-02)**: verdict **PASSED**, 1 cycle
of a 3-cycle budget, **0 heals needed**, 2 dispatches, 0/15 retries — the MAKER (`plan-executor-agent`,
isolated worktree) and CHECKER (`code-reviewer-agent`) were genuinely independent, and T0
reproduced every gate itself rather than trusting either worker's self-report.

## Version history

- **0.1.0** (2026-07-03) — Initial plugin scaffold: 13 skills + 2 agents, the loop's full
  dependency closure, registered in the hub marketplace. Pending: `/plugin install` validation in
  a second project (the open G6-graduation proof).
- **0.2.0–0.4.0** — G6 graduation (second-project install validated 2026-07-03) + incremental
  content syncs from the hub (PR trail: the hub's `registry/changelog.md`).
- **0.5.0** (2026-07-15) — Plugin QA review: bundle `tester-agent`,
  `test-failure-analyzer-agent`, `debugger-agent` so the closure claim is true on a fresh
  install (they were dispatched by `auto-verify`/`fix-loop`/`debugging-loop` but not shipped);
  PREFLIGHT gates added to `fix-loop` + `auto-verify` (missing worker now BLOCKS with an
  actionable message instead of crashing mid-dispatch); now 5 agents + 13 skills.
