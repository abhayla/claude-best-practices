# Loop Engineering — Canonical Spec

version: 1.0.0
status: active
owner: hub (Systems Architect)
created: 2026-06-16

## 1. Goal & anchor

Deliver a **repeatable, autonomous feedback loop** — DISCOVER → PLAN → EXECUTE →
VERIFY → (SHIP | FEEDBACK) — that any project can adopt to let an agent find work,
do it, check its own work with an *independent* checker, learn from the result, and
either ship or loop again, all under hard budgets.

**Goal anchor** (`goal-anchored-decisions.md`): this serves the hub's documented
goal — reusable patterns for downstream projects (`CLAUDE.md`). The concrete caller
exists (owner directive 2026-06-16) and the pattern is evidence-backed (Addy Osmani,
*Loop Engineering*; Anthropic agent-loop docs), so it clears `rule-curation.md`'s
reactive-not-speculative bar.

**Source of the concept:** Addy Osmani — *Loop Engineering* (canonical), Anthropic
*How the agent loop works* (`code.claude.com/docs/en/agent-sdk/agent-loop`).

## 2. The design decision (why this shape)

The hub already owns every primitive Loop Engineering needs. Therefore loop-engineering
is a **thin skill-at-T0 orchestrator that composes existing assets** — NOT a new engine.
This is the KISS/DRY/YAGNI-correct choice and avoids duplicating governance the rules
already own (`configuration-ssot.md`, `design-principles.md`).

Skill-at-T0 is mandatory, not stylistic: the maker→checker split needs `Agent()`, which
Claude Code exposes only in the T0 session, never inside a dispatched worker
(`agent-orchestration.md` §2). A loop-engineering *agent* that tried to dispatch
maker/checker workers would silently inline them — the 2026-04-24 failure mode.

### The six Loop-Engineering blocks → hub assets

| Block | Hub asset it maps to |
|---|---|
| Automations (trigger) | `/loop`, `/goal`, cron, GitHub Actions, lifecycle hooks |
| Worktrees (isolation) | `Agent(isolation:"worktree")`, `/git-worktrees` |
| Skills (project knowledge) | `core/.claude/skills/*` (the hub's product) |
| Plugins / connectors | MCP + `config/third-party-skills.yml` |
| Sub-agents (maker/checker) | `plan-executor-agent` (maker) vs `code-reviewer-agent` / blind tester (checker) |
| Memory (on-disk state) | `.workflows/loop-engineering/state.json` + `learnings.json` |

### The four "self-*" capabilities → composed-from (the spine)

| Capability | Composed from (no new pattern) |
|---|---|
| **self-healing** | `/fix-loop`, `/debugging-loop`, `/systematic-debugging` (FEEDBACK arm) |
| **self-verification** | maker ≠ checker: `supervisor-verification.md` + `independent-test-verification.md` |
| **self-learning** | `/learn-n-improve`, `/self-improve`, `auto-learn-trigger.sh` |
| **self-feedback** | `/escalation-report` + a triage inbox + `post-failure-capture.sh` |

Net new patterns: **1** — the `loop-engineering` skill. Maker/checker reuse existing
workers (distinct `subagent_type`s), so no new agents, rules, or hooks are created.

## 3. The loop (DAG)

```
        ┌──────────── automation trigger (/loop · /goal · cron · PR) ──────────┐
        ▼                                                                       │
  DISCOVER ──► PLAN ──► EXECUTE(maker) ──► VERIFY(checker, independent) ──► GATE │
                                                                            │    │
                                                       PASS ► SHIP ► LEARN ─┘    │
                                                       FAIL ► FEEDBACK ──────────┘
                                                              (heal, bounded)
```

| Step | Skill / dispatch | Gate / output |
|---|---|---|
| DISCOVER | `/status` or triage read (CI failures, open issues, the task) | `triage.json`; nothing actionable → exit clean |
| PLAN | `/brainstorm` (if novel) → `/writing-plans` | `plan.md` |
| EXECUTE (maker) | `Agent(plan-executor-agent, isolation:"worktree")` | `changed_files[]` |
| VERIFY (checker) | `/auto-verify` + `Agent(code-reviewer-agent)` (maker≠checker) + blind test verify | `result == PASSED` |
| GATE | pass → SHIP; fail → FEEDBACK | branch |
| SHIP | `/post-fix-pipeline` (commit) | `commit_sha` |
| FEEDBACK | `/fix-loop` (or `/debugging-loop` if root cause unclear), retry under budget | back to VERIFY |
| LEARN | `/learn-n-improve` | `learnings.json` |

## 4. Autonomy guarantees (the parts loops leak at)

- **Bounded** — inherits `global_retry_budget: 15` + `max_retries_per_step: 3`
  (`workflow-contracts.yaml` defaults); a `max_cycles` cap and an optional
  wall-clock cap. Budget exhaustion → `/escalation-report` to the triage inbox, never
  a silent stall (Osmani's "unattended mistakes" warning).
- **Terminating** — explicit termination conditions: DoD met, nothing actionable in
  DISCOVER, or any budget exhausted. No unbounded loop.
- **Maker ≠ Checker** — EXECUTE and VERIFY MUST use different `subagent_type`s; the
  author never grades its own homework (`independent-test-verification.md`). Enforced
  by `scripts/tests/test_workflow_closure_consistency.py`.
- **Supervised** — T0 reproduces the checker's gate before SHIP
  (`supervisor-verification.md`); a worker's "PASSED" is a claim, not proof.

## 5. Downstream correctness (the hard part)

A hub skill green locally can ship broken. Guarantees:

1. **Closure = provisioning contract.** Every dispatched worker is declared in the
   registry `dependencies`; the closure test makes shipping the skill without its
   workers un-mergeable.
2. **PREFLIGHT runtime probe.** STEP 1.5 BLOCKs with `WORKER_REGISTRY_NOT_LOADED`
   (listing the gap + the `/update-practices` + restart remediation) rather than
   inlining — because Claude Code pins the agent registry at session start
   (`pattern-structure.md`).
3. **Universal pattern.** No stack prefix → `bootstrap.py` copies it to every project.
4. **Contract ships.** The DAG lives in `core/.claude/config/workflow-contracts.yaml`
   (kept byte-identical to `config/` by `test_workflow_contracts_config_is_distributable_and_synced`).

## 6. Out of scope / escalation

- Running the loop against an **external downstream repo** (outward PR/push) is an
  escalation gate — the owner authorizes per-repo. The hub ships the mechanism; it does
  not auto-open PRs on others' repos.
- No new automation cron is wired in the hub by this spec — projects opt in via `/loop`
  or `/goal` on their own cadence.

## 7. References

- `core/.claude/skills/loop-engineering/SKILL.md` — the orchestrator
- `config/workflow-contracts.yaml` → `workflows.loop-engineering` — the DAG
- `agent-orchestration.md`, `supervisor-verification.md`,
  `independent-test-verification.md`, `goal-anchored-decisions.md`,
  `decision-authority.md`, `rule-curation.md`
