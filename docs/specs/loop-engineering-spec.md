# Loop Engineering — Canonical Spec

version: 1.4.0
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

## 3.7 Platform-native loop taxonomy (compose with, never reinvent, the native primitives)

The hub already names its own loop stages (§3) but did not, until this section, classify them
against the platform's OWN native loop primitives — so a new automation can accidentally
hand-roll what the harness already ships. Every fact below is cited to the hub's own cached docs
(`docs/claude-references/`, `Fetched:` dates as shown) or explicitly flagged **Unverified** where
no first-party citation exists in this repo's captures.

### The four native loop types

| # | Type | Trigger mechanism | Pacing owner | Persistence across sessions | Cost profile |
|---|---|---|---|---|---|
| 1 | **`/loop <interval> <prompt>`** (fixed interval) | user-given interval, converted to a `CronCreate` cron expression (`docs/claude-references/scheduled-tasks.md`, fetched 2026-06-23) | **harness** — deterministic cadence, no model judgment per tick | session-scoped; restored on `--resume`/`--continue` if the recurring task is <7 days old; **7-day hard expiry**, then self-deletes | fixed cadence regardless of need — halving the interval doubles the tick cost (§3.8 below) |
| 2 | **`/loop <prompt>`** (dynamic, self-paced) | Claude picks the next delay (1 min–1 h) each iteration based on what it observed, via the internal `ScheduleWakeup` tool — **first-party confirmed**: the tool's own schema reads "Schedule when to resume work in /loop dynamic mode — the user invoked /loop without an interval, asking you to self-pace iterations of a specific task" (live ScheduleWakeup tool schema, conductor session 2026-07-10 — snapshot: `docs/claude-references/schedule-wakeup-tool.md`); also **verified T0-only**: `docs/claude-references/sub-agents.md` lists `ScheduleWakeup` among tools "not available to subagents, even when listed in the `tools` field" | **model, at T0** — adaptive backoff replaces hand-rolled polling logic; MAY use the `Monitor` tool to stream a background script instead of polling at all | same session-scoped rules as #1 (7-day expiry, `--resume` restores if unexpired) | adapts to observed state (short waits on active work, long waits when quiet) — cheaper than fixed-interval polling on the same task; per the schema's delay guidance, wakeups under ~300 s land inside the prompt-cache window (cached prefix still warm — cheaper resume) while longer delays re-pay the full prompt cost (`schedule-wakeup-tool.md`) |
| 3 | **`CronCreate`/`CronList`/`CronDelete`** (the raw scheduled-task tools `/loop` and one-shot reminders sit on top of) — for DURABLE, session-independent cadence use **cloud Routines** (`/schedule`, `docs/claude-references/routines.md`, fetched 2026-06-27) instead, a *separate* first-party primitive (Anthropic-managed infra, ≥1-hour minimum interval, triggers: schedule/API/GitHub-event) — a separate primitive from the session-scoped `CronCreate` tools | calendar/cron expression (session-scoped tool) or a managed schedule (cloud Routines) | harness (cron scheduler checks every second; low-priority enqueue; jitter up to 30 min on recurring tasks) | session-scoped `CronCreate` tasks: die with the session / 7-day expiry, up to 50 per session. Cloud Routines: persist independent of any open session, draw a **daily run-count cap** on top of normal subscription usage | session-scoped tasks are near-free (one prompt re-run); cloud Routines bill as full cloud sessions per firing |
| 4 | **`/goal <condition>`** (one-shot autonomous contract) | a session-scoped, prompt-based Stop hook: after every turn the condition + transcript are sent to the configured small-fast model (default Haiku) for a yes/no (`docs/claude-references/goal.md`, fetched 2026-06-23) | **harness-orchestrated, model-evaluated** — the evaluator is a SEPARATE (cheaper) model from the one doing the work, but reads only the conversation transcript; it "does not call tools, so it can only judge what Claude has already surfaced" | one goal active per session; restored on `--resume`/`--continue` (turn count, timer, token baseline all reset); cleared by `/goal clear` or a fresh `/clear` | evaluator tokens run on the small-fast model and are "typically negligible compared to main-turn spend" (per the cached doc) — the real cost is the underlying work turns, identical to any other autonomous run |

**Routing table** — which loop-engineering entry point maps to which native type:

| Task shape | Native primitive | Why |
|---|---|---|
| Recurring check on EXTERNAL state at a known cadence (poll a deploy, babysit a PR, check a build) | **`/loop` fixed interval** | deterministic cadence matches a known-frequency external event; no adaptive judgment needed |
| Self-paced autonomous continuation (work until quiet, back off adaptively) | **`/loop` dynamic (self-paced)** | the harness's `ScheduleWakeup`-driven backoff replaces hand-rolled polling/backoff logic — cheaper and simpler than reimplementing it |
| Calendar cadence that must survive the session closing / the machine being off | **cloud Routines (`/schedule`)** — session-scoped `CronCreate` tasks 7-day-expire and die with the session, so they are NOT durable enough for this shape | Routines run on Anthropic-managed infra independent of any open session (per `routines.md`) |
| Run-to-Definition-of-Done, a SINGLE well-specified task with a transcript-verifiable end state, no fleet doctrine needed | **`/goal <condition>`** | the built-in evaluator-after-every-turn loop is a lighter-weight, near-free wrapper for exactly this shape (see `goal.md`'s own examples: migrate a module until all call sites compile, implement a design doc until acceptance criteria hold) |
| Unattended MULTI-UNIT work needing independent maker≠checker verification, bounded self-healing, and hub-ward telemetry | **`/loop-engineering`** | see the honest comparison below — this is the shape native `/goal` does not cover |

### Where hand-rolled loop-engineering DoD gating still beats native `/goal`

`/goal`'s evaluator is a genuine platform primitive, not a toy — but it solves a narrower problem
than §3's DAG. loop-engineering keeps its own gating for four reasons, each because `/goal` has no
equivalent:

1. **Maker≠checker enforcement.** `/goal`'s evaluator reads the SAME conversation transcript the
   implementer wrote — it never spawns an independent agent given the raw diff, so it cannot catch
   what `independent-test-verification.md` exists to catch (a plausible-sounding "done" that never
   happened). loop-engineering's STEP 5 dispatches a SEPARATE `Agent()` checker on the raw merged
   diff specifically because the doer is the worst judge of its own work.
2. **Healing budgets.** `/goal` has no `max_retries_per_step` / `global_retry_budget` / wall-clock
   cap — the docs describe only an optional turn/time CLAUSE inside the condition text itself
   (e.g. "or stop after 20 turns"), evaluated by the same non-tool-calling evaluator. loop-engineering
   enforces per-step AND global numeric budgets in `state.json`, independent of any prose clause.
3. **Strategy mutation (§3.6).** A stuck `/goal` loop just keeps re-attempting with the evaluator's
   "no, keep going, here's why" as its only steering signal — there is no equivalent to the §3.6
   strategy ledger + novelty gate that forces a DIFFERENT `{decomposition, diagnostic, model}` tuple
   on a repeat stall. `/goal` has no mechanism to detect "this is the same failed approach again."
4. **Telemetry round-trip.** loop-engineering emits hub-linked `.claude/learnings.json` entries on
   every terminal signal (§5.1) that the hub's weekly aggregator ingests. `/goal` has no equivalent
   hub-ward signal — a `/goal` run's outcome is visible only in that session's own transcript.

Where native `/goal` is SIMPLER and should be preferred: a single, well-specified task whose done
state is directly transcript-checkable (no multi-unit DISCOVER ranking needed, no independent
reviewer needed because the "check" IS the condition text itself), and where the overhead of
`state.json` + a worktree-merge dance + a strategy ledger is disproportionate to the task. Use
`/goal` directly for that shape; reserve `/loop-engineering` for the shape its extra machinery earns
its keep on (multi-unit, needs independent verification, needs bounded self-healing across repeats).

**Sentinel comments (`<<autonomous-loop>>` / `<<autonomous-loop-dynamic>>`):** **first-party
confirmed** (live ScheduleWakeup tool schema, conductor session 2026-07-10 — snapshot:
`docs/claude-references/schedule-wakeup-tool.md`). The schema states verbatim: "For an autonomous
/loop (no user prompt), pass the literal sentinel `<<autonomous-loop-dynamic>>` as `prompt` — the
runtime resolves it back to the autonomous-loop instructions at fire time. (There is a similar
`<<autonomous-loop>>` sentinel for CronCreate-based autonomous loops; do not confuse the two —
ScheduleWakeup always uses the `-dynamic` variant.)" So: `<<autonomous-loop-dynamic>>` belongs to
`ScheduleWakeup` (dynamic self-paced `/loop`, always the `-dynamic` variant), and
`<<autonomous-loop>>` belongs to `CronCreate`-based autonomous loops.

## 3.8 Budget introspection (loop-domain budgets compose with, never replace, token/turn budgets)

The hub's own doc cache does **not** document an official `budget.total()` / `budget.spent()` /
`budget.remaining()` API on the Dynamic Workflows tool (`docs/claude-references/workflows.md`,
fetched 2026-06-23, has no `budget` reference) — that claim traces only to a third-party capture
(`docs/process-improvement/sources/2026-07-06-claudedevs-getting-started-with-loops.md`, line 71:
"`/usage`, `/goal` (no args), `/workflows` token-introspection commands... they're the native
equivalent of the Workflow tool's `budget.spent()`"), which itself does not cite a first-party
source. **Unverified**: treat any specific `budget.*()` method signature as directional, not
confirmed platform fact, until a first-party doc is captured and cited here.

What IS first-party-verified as native token/turn introspection: `/goal` with no arguments prints
"how many turns have been evaluated" and "the current token spend" for the active/most-recent goal
(`docs/claude-references/goal.md`) — a real, citable per-goal budget readout.

**Guidance — wire a token/turn target into a loop contract, alongside the loop-domain budget, not
instead of it.** loop-engineering's own budgets (`max_heals` via `budget.step_retries[<step>]`,
`global_retry_budget`, `max_cycles`, an optional wall-clock cap — spec §4) are **loop-domain**
budgets: they bound how much WORK a stuck gate may retry. A token/turn budget is an orthogonal,
**spend-domain** concern that composes with, never substitutes for, the loop-domain one:

- When authoring a `/goal-creator` contract or a `/goal <condition>` invocation, append the
  documented turn/time clause (`goal.md`: "include a turn or time clause in the condition, such as
  `or stop after 20 turns`") so the SPEND has an explicit ceiling the evaluator judges each turn,
  independent of whether the WORK is bounded.
- For `/loop-engineering` runs, the existing `--max-cycles` / `global_retry_budget` /
  `max_retries_per_step` bound the WORK; they say nothing about token spend. Where a project also
  needs a spend ceiling, track it via the project's own cost ledger (the hub's own
  `scripts/collect_signals.py` / `trust-score/` ledgers are the hub's analog) rather than inventing
  a second in-skill budget field — spend tracking is a SEPARATE concern from `state.json`'s
  work-retry budgets, and conflating them would violate `configuration-ssot.md`'s one-canonical-layer
  rule.
- Neither budget substitutes for the other: a loop can be work-bounded (bounded cycles) yet still
  overspend tokens on an expensive model tier per cycle, and a token-bounded loop can still spin
  forever on cheap retries if `global_retry_budget` is unset. Author BOTH explicitly for any
  autonomous run with real cost exposure.

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
- `docs/loop-vocabulary.md` — shared loop-pattern vocabulary (§3.7 supersedes its
  "Table C §I" note that `/loop` + `/goal` map to the hub encoding only in passing —
  §3.7 is now the detailed taxonomy + routing table)
- Platform-native primitive docs (§3.7/§3.8 citations): `docs/claude-references/goal.md`
  (fetched 2026-06-23), `docs/claude-references/scheduled-tasks.md` (fetched 2026-06-23),
  `docs/claude-references/routines.md` (fetched 2026-06-27), `docs/claude-references/sub-agents.md`,
  `docs/claude-references/workflows.md` (fetched 2026-06-23),
  `docs/claude-references/schedule-wakeup-tool.md` (live tool-schema snapshot, 2026-07-10)
