# Loop Engineering — Canonical Spec

version: 1.3.0
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
| Automations (trigger) | `/loop`, `/goal-creator` contracts, cron, GitHub Actions, lifecycle hooks |
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
  automation trigger (/loop · /goal · cron · PR)
        ▼
    DISCOVER ◄──────────────────────────────────────────────────┐
        ▼                                                       │
      PLAN                                                      │
        ▼                                                       │
    EXECUTE (maker) ◄────────────────────────────┐              │
        ▼                                        │              │
    VERIFY (checker, independent) ◄───────┐      │              │
        ▼                                 │      │              │
      GATE ── PASS ► SHIP ► LEARN ────────┼──────┼──────────────┘  (next unit)
        │                                 │      │
       FAIL ► FEEDBACK (heal, bounded)    │      │
                │                         │      │
                ├─ VERIFY dissent or a ───┘      │
                │  resolvable conflict:          │
                │  heal, complete the 4b         │
                │  merge ► re-enter VERIFY       │
                └─ maker FAILED|BLOCKED or ──────┘
                   unresolvable conflict:
                   re-dispatch the maker ► EXECUTE
```

(FEEDBACK never returns to DISCOVER — only LEARN advances to the next unit.)

| Step | Skill / dispatch | Gate / output |
|---|---|---|
| DISCOVER | `/status` or triage read (CI failures, open issues, the task) | `triage-inbox.md`; nothing actionable → exit clean (`clean_exit` signal) |
| PLAN | `/brainstorm` (if novel) → `/writing-plans` | `plan.md` |
| EXECUTE (maker) | `pre_merge_sha` recorded at dispatch; `Agent(<config-resolved maker — SKILL STEP 1.5.3; default plan-executor-agent>, isolation:"worktree")`; the orchestrator then MERGES the maker's returned `worktree_branch` into the run's working tree (SKILL STEP 4b) — VERIFY/SHIP operate on the post-merge T0 tree, never the worktree, and are unreachable until that merge succeeds | `worktree_branch` + `changed_files[]` (recomputed from the merged diff) |
| VERIFY (checker) | `/auto-verify --strict-gates --range pre_merge_sha..HEAD` (the range makes the mechanical gate verify the COMMITTED merged diff — a bare invocation would see a clean working tree and vacuously green) + `Agent(<config-resolved checker — SKILL STEP 1.5.3; default code-reviewer-agent>)` (maker≠checker) + T0 supervisor reproduction — the "blind test verify" layer is realized by the context-blind reviewer given the RAW merged diff itself (`git diff pre_merge_sha..HEAD`, passed in the dispatch context — not a path list; complete on every entry because each heal is COMMITTED — a heal checkpoint commit — before VERIFY re-entry) plus the T0 reproduction (`independent-test-verification.md`), not a fourth dispatch | `result == PASSED` |
| GATE | pass → SHIP; fail → FEEDBACK | branch |
| SHIP | `/post-fix-pipeline` (commit) | `commit_sha` |
| FEEDBACK | three entry modes (SKILL STEP 6): VERIFY dissent → `/fix-loop` (or `/debugging-loop` if root cause unclear) on the post-merge tree, the heal COMMITTED (heal checkpoint commit) before re-entering VERIFY; merge CONFLICT → resolve-and-complete the 4b merge (or re-dispatch the maker); maker `FAILED\|BLOCKED` → re-dispatch the maker. On a REPEAT heal for the same failing gate (§3.6) the STRATEGY is mutated + novelty-gated, not re-run. Retry under budget | back to VERIFY only after a successful 4b merge |
| LEARN | `/learn-n-improve` | `learnings.json` |

## 3.5 The three rings (nested feedback loops at three timescales)

The §3 DAG is only the INNERMOST of three nested loops (Andrew Ng's 3-loops model —
captured 2026-06-30, `docs/process-improvement/sources/2026-06-30-andrew-ng-3-product-development-loops.md`).
Each outer ring steers the ring inside it; a loop run is never "the whole system":

| Ring | Owner | Timescale | What cycles | Existing hub implementation |
|---|---|---|---|---|
| **1 — Machine** | the agents | minutes | the §3 DAG (DISCOVER→…→LEARN) | this spec |
| **2 — Developer** | the project owner | hours | goal/contract revision, escalation review, gate approvals | `/goal-creator` contracts, `/escalation-report` + triage inbox, `human-approval-gates.md` G1/G2/G3 |
| **3 — External** | real users | days–weeks | shipped work → usage/feedback → next goals | dogfood flywheel (`/synthesize-hub`), `aggregate_telemetry.py`, downstream `learnings.json` |

Placement rule for human gates (Ng's context-advantage criterion): a Ring-2 pause belongs
ONLY where the human knows something the machine does not (taste, strategy, spend,
irreversibility) — never as routine babysitting of Ring 1. Escalations exit Ring 1 to
Ring 2 with the human fixing the CONTRACT, not the build; Ring-3 signals enter as new
DISCOVER inputs, never mid-cycle. This section names the model; the gate mechanics stay
owned by their SSOTs (`decision-authority.md`, `human-approval-gates.md`) — no duplication.

Shared loop-pattern vocabulary (the 20 loop design patterns, Karpathy's 9 harness rules, the
Ralph loop, Willison's brakes → the hub asset owning each): `docs/loop-vocabulary.md`.

## 3.6 Bilevel self-improvement (strategy mutation + novelty gate in the FEEDBACK arm)

The FEEDBACK arm's default reflex is a lower-level loop: heal → re-verify → heal again. If it
keeps failing on the SAME gate, retrying accumulates only more LESSONS while re-running the SAME
search strategy — the loop is stuck by construction. The **outer** (bilevel) loop fixes that: on a
repeat heal it mutates the stuck loop's SEARCH STRATEGY itself, with a novelty ledger so a
proven-failed strategy is never re-run and exhaustion is detectable. It composes with the STEP 7
learning capture (which remembers WHAT unstuck it) — it does not replace it. Full mechanics live in
SKILL STEP 6 §6a; this section is the design record.

- **Strategy ledger** — when the loop enters heal N≥2 for the same failing gate, the orchestrator
  writes a strategy-attempt record to the working state file (`state.strategy_ledger`, keyed by a
  stable failing-gate signature: `<step>:<failure-class>`). Record shape:
  `{attempt, failing_gate, strategy:{decomposition, diagnostic, model}, worker, failure_signature, ts}`.
- **Three mutation axes (enumerable → exhaustion detectable):** `decomposition`
  (whole → bisected → single-surface), `diagnostic` (`/fix-loop` → `/debugging-loop`), `model`
  (sonnet → opus, escalated LAST — cheapest-sufficient first). A strategy is the tuple
  `{decomposition, diagnostic, model}`.
- **Mutation rule** — the next heal MUST select a strategy that differs on ≥1 axis from EVERY
  recorded failed attempt (equivalently: a tuple not already in the ledger), advancing along the
  cheapest-axis-first preference order. The first flip is conditional on the baseline diagnostic:
  fix-loop baseline → flip diagnostic first; debugging-loop baseline → flip decomposition first,
  never de-escalating the diagnostic while the same failure-class persists. Then decomposition,
  then model LAST.
- **Novelty gate** — before dispatching a heal, compare the proposed strategy against the ledger:
  identical → REJECT and mutate again; all enumerable tuples recorded → **axes exhausted** →
  `/escalation-report` (the existing terminal) with the strategy ledger attached, so a human/Ring-2
  fixes the CONTRACT rather than re-trying an exhausted search. Honesty note: under the shipped
  default `max_retries_per_step: 3` the per-step budget veto normally terminates the search long
  before the 12 enumerable tuples are explored — the budget dominates; the axes-exhaustion terminal
  is the BACKSTOP for configurations that raise `max_retries_per_step` (and the ledger is keyed by
  `<step>:<failure-class>` while `step_retries` is keyed by `<step>` alone, so multiple failure
  classes on one step share the same budget counter).
- **Success capture** — when a mutated strategy SUCCEEDS, the STEP 7 `/learn-n-improve` call records
  the strategy delta (which axis change unstuck it) as a `success_patterns` entry. The existing
  success-pattern schema (attempted/worked/mechanism/reuse_trigger) carries the delta with **no
  extension** — so the next stall mutates the winning axis first instead of rediscovering it.

Net new mechanism: **0 new patterns** — this is FEEDBACK-arm state + selection logic inside the
existing `loop-engineering` skill, reusing `/fix-loop`/`/debugging-loop` (healers), the strategy
ledger in the existing state file, `/escalation-report` (exhaustion terminal), and
`/learn-n-improve`'s existing success-pattern capture. Consistent with §2's "composes existing
assets, creates no new engine".

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

## 5.1 Monitoring (hub-ward feedback — automatic, no new pipeline)

The loop's runtime artifacts (`test-results/loop-engineering-verdict.json`, triage
inbox) are gitignored and stay local. To make downstream behaviour observable from
the hub WITHOUT a new uploader or outward call, every signal-emitting outcome —
the terminal exits, plus the mid-run `shipped` (per unit) and `healed` marks —
appends one hub-linked entry to `.claude/learnings.json` — the file the hub's weekly
`aggregate_telemetry.py` already scans on the Friday cron against enrolled repos
(`config/repos.yml`).

| Signal | Emitted at | What it tells the hub |
|---|---|---|
| `preflight_blocked` | STEP 1.5 (incl. the retroactive block at STEP 4/5 on a dispatch-time "agent type not found") | provisioning shipped the skill without its worker closure (the #1 downstream defect) |
| `escalated` | STEP 6 budget exhaustion | a unit the loop could not resolve under budget |
| `healed` | STEP 6 PASS arm (mid-run, when the passing VERIFY resolved a heal) | self-healing worked — positive effectiveness |
| `shipped` | STEP 7 (mid-run, per shipped unit — the single emit site, never STEP 6) | a unit completed cleanly |
| `clean_exit` | STEP 2 nothing-actionable exit / STEP 2 `--discover-only` / STEP 6 `--no-ship` terminal | the loop ran and found nothing to do (or triaged/verified without shipping) — an always-clean project stays visible |

Each entry sets `hub_pattern_link: "loop-engineering"` and a STABLE `tags`
signature per defect class. The aggregator's `compute_error_prevention_rate` keys
on exactly those fields: a defect class that recurs across runs lowers the pattern's
effectiveness rate; a one-off counts as addressed. Result lands in
`registry/patterns.json` automatically — closing the monitor-downstream loop on the
existing flywheel rather than a bespoke telemetry channel (KISS/DRY).

`aggregate_telemetry` was hardened (v1.1.0) so a pattern that appears ONLY via a
learning's `hub_pattern_link` — with no sync-manifest adoption row — is still
aggregated (`_linked_pattern_names`): otherwise the `escalated` / `preflight_blocked`
signals would be silently dropped in copy-all / synthesis adoptions that don't write
a manifest. Guarded by `test_learnings_only_pattern_is_aggregated` (aggregator-level,
end-to-end) plus `test_loop_engineering_emits_hub_linked_telemetry` (skill-level).

**Constraint:** a downstream project must commit `.claude/learnings.json` for the
signal to travel (same constraint as all error-prevention telemetry — not new).

## 6. Out of scope / escalation

- Running the loop against an **external downstream repo** (outward PR/push) is an
  escalation gate — the owner authorizes per-repo. The hub ships the mechanism; it does
  not auto-open PRs on others' repos.
- No new automation cron is wired in the hub by this spec — projects opt in via `/loop`
  or a `/goal-creator` contract on their own cadence.

## 7. References

- `core/.claude/skills/loop-engineering/SKILL.md` — the orchestrator
- `config/workflow-contracts.yaml` → `workflows.loop-engineering` — the DAG
- `agent-orchestration.md`, `supervisor-verification.md`,
  `independent-test-verification.md`, `goal-anchored-decisions.md`,
  `decision-authority.md`, `rule-curation.md`
