---
name: loop-engineering
description: >
  Run a repeatable, autonomous feedback loop — DISCOVER → PLAN → EXECUTE →
  VERIFY → (SHIP | FEEDBACK) — as a skill-at-T0 orchestrator. The skill body IS
  the orchestrator: it runs in the user's T0 session, dispatches a MAKER worker
  (default plan-executor-agent) and a SEPARATE CHECKER (default
  code-reviewer-agent) via Agent()
  so the author never grades its own work, and self-heals on failure by looping
  through /fix-loop or /debugging-loop under hard budgets. Self-verifying
  (maker≠checker), self-healing (feedback arm), self-learning (/learn-n-improve
  each cycle), self-feedback (/escalation-report on budget exhaustion). Use to
  run unattended work to a Definition of Done — triggered by /loop, a
  /goal-creator contract, cron, or a PR. For a single feature use
  /development-loop; for one bug use /debugging-loop; this is the autonomous
  meta-loop that ROUTES into them.
type: workflow
triggers:
  - autonomous loop
  - loop engineering
  - run autonomously until done
  - self-healing loop
  - maker checker loop
  - discover plan execute verify loop
allowed-tools: "Agent Bash Read Write Edit Grep Glob Skill"
argument-hint: "<goal / Definition of Done, issue URL, or triage source> [--max-cycles N] [--no-ship]"
version: "1.5.0"
---

# /loop-engineering — Skill-at-T0 Autonomous Loop Orchestrator

This skill's body is injected into the user's T0 session and executed there. T0
is the only place `Agent()` is forwarded, so the MAKER→CHECKER dispatch happens
here, never inside a dispatched worker (`agent-orchestration.md` §2 — subagents
cannot spawn subagents; a loop-engineering *agent* would silently inline the
checker, defeating independent verification).

**What it is:** the autonomous *meta-loop* — it DISCOVERS work, PLANS it, EXECUTEs
with a maker, VERIFIEs with an INDEPENDENT checker, then SHIPs or FEEDBACK-loops
to self-heal, learning each cycle. It composes existing hub assets; it does not
re-implement them. Canonical design: `docs/specs/loop-engineering-spec.md` — including
§3.5 "The three rings": this loop is Ring 1 (machine, minutes); the owner's contract
revisions + gate approvals are Ring 2 (hours); user feedback entering DISCOVER is Ring 3
(days). Escalations exit to Ring 2 for a CONTRACT fix, never for babysitting the build.
§3.6 "Bilevel self-improvement" specifies the strategy-mutation + novelty gate that STEP 6
uses to change a stuck loop's search instead of re-running a proven-failed one. §3.7
"Platform-native loop taxonomy" classifies this skill against the platform's own `/loop`,
`/goal`, and cloud-Routines primitives, with a routing table for which one fits which task.

**Self-\* spine (composed, not built):** healing = `/fix-loop` · `/debugging-loop`
· `/systematic-debugging` (with **bilevel strategy mutation** on repeated stalls —
STEP 6's strategy ledger + novelty gate mutate the STUCK loop's SEARCH strategy,
not just its lessons; spec §3.6); verification = maker≠checker
(`supervisor-verification.md` + `independent-test-verification.md`); learning =
`/learn-n-improve`; feedback = `/escalation-report` + triage inbox.

**Input:** `$ARGUMENTS` — a Definition of Done, issue URL, or triage source. If
empty, ask the user for the DoD before proceeding (an autonomous loop with no DoD
cannot terminate — `dod-verbs.md`).

**Before starting a hand-rolled loop, check the platform-native routing table
first** (spec §3.7): a recurring check on external state fits native `/loop`
fixed interval; a self-paced autonomous continuation fits `/loop` dynamic
(self-paced via the `ScheduleWakeup` tool — first-party confirmed, live tool
schema 2026-07-10, `docs/claude-references/schedule-wakeup-tool.md`); a
calendar cadence that must survive the
session closing fits cloud Routines (`/schedule`); a single well-specified
task with a transcript-verifiable end state and no need for maker≠checker /
bounded healing / strategy mutation / hub telemetry fits native `/goal
<condition>` directly — SIMPLER than this skill for that shape. Reach for
`/loop-engineering` only when the task genuinely needs what native `/goal`
lacks: independent maker≠checker verification, bounded self-healing with
strategy mutation (§3.6), or hub-ward telemetry across a multi-unit DISCOVER
loop. Composing with the native primitive beats reinventing it.

---

## CLI Signature

```
/loop-engineering <DoD | issue URL | triage source>
                  [--max-cycles N]   # default 5; hard cap on full loop iterations
                  [--no-ship]        # stop after VERIFY; skip the SHIP commit
                                     # (the 4b integration merge still lands)
                  [--discover-only]  # run DISCOVER + report, no execution
```

| Flag | Default | Meaning |
|------|---------|---------|
| `--max-cycles` | 5 | Hard cap on DISCOVER→…→GATE iterations before escalating |
| `--no-ship` | off | Stop after VERIFY passes; skip the SHIP commit (the 4b integration merge still lands on the run branch) |
| `--discover-only` | off | Triage only — surface actionable work, then stop |

---

## STEP 1: INIT

1. **Parse args + Definition of Done.** Restate the DoD as one load-bearing
   sentence with a precise verb + completeness bar (`dod-verbs.md`). If it is not
   stateable, STOP and ask — an autonomous loop satisfies the *weakest* reading of
   a vague goal.
2. **Read config.** `Read .claude/config/workflow-contracts.yaml` (hub repo:
   `config/workflow-contracts.yaml`; if absent, execute the numbered STEPs 1–8
   of this skill as the DAG — this skill is self-contained) →
   `workflows.loop-engineering`. Pull the step DAG, gates, and budgets.
   `master_agent` should be null; `sub_orchestrators` empty.
3. **Generate `run_id`.** `{ISO-8601}_{7-char git sha}` with `:` → `-`.
4. **Initialize state + budgets.** `Write .workflows/loop-engineering/state.json`:
   ```json
   {
     "schema_version": "1.0.0",
     "run_id": "<run_id>",
     "started_at": "<iso>",
     "dod": "<one-sentence DoD>",
     "cycle": 0,
     "max_cycles": 5,
     "argument_unit_consumed": false,
     "merged_this_cycle": false,
     "pre_merge_sha": null,
     "units_shipped": 0,
     "heals": 0,
     "strategy_ledger": {},
     "workers": { "maker": "plan-executor-agent", "checker": "code-reviewer-agent" },
     "budget": { "global_retry_budget": 15, "max_retries_per_step": 3, "retries_used": 0, "step_retries": {}, "dispatches_used": 0 },
     "artifacts": { "plans": [], "commits": [] },
     "triage_inbox": ".workflows/loop-engineering/triage-inbox.md"
   }
   ```
   The template's budget values are DEFAULTS: `--max-cycles N` overrides
   `max_cycles`, and when the contracts config was read in 1.2 its `defaults`
   (`global_retry_budget: 15`, `max_retries_per_step: 3`, optional wall-clock
   cap) override the template values. These caps are ENFORCED, not advisory:
   every FEEDBACK re-entry increments `budget.step_retries[<failing step>]`,
   and a step exceeding `max_retries_per_step` triggers the STEP 6 ESCALATE
   arm even with global budget left; when a wall-clock cap is configured,
   check elapsed time against `started_at` at every STEP 2 entry and every
   FEEDBACK re-entry — exceeded → ESCALATE. `workers` holds the DEFAULT
   maker/checker names; STEP 1.5.3 overwrites them with the config-resolved
   values, and STEPs 4/5.2 dispatch from `state.workers`. `strategy_ledger`
   starts empty; STEP 6's bilevel self-improvement mechanism keys it by
   failing-gate signature to record each failed heal strategy so the next heal
   is mutated to a novel one (never a re-run of a proven-failed search).
5. **Append INIT event** to `events.jsonl`.

---

## STEP 1.5: PREFLIGHT (dependency-closure gate — BLOCK on missing workers)

Provisioning copies skills/agents by tier and does NOT always resolve a skill's
full dependency closure — a project can end up with `/loop-engineering` but
without its workers. Catch that here with an actionable BLOCK, never a silent
inline run (the 2026-04-24 failure mode).

1. **Required workers** (dispatched via `Agent()`): the RESOLVED maker and
   checker from item 3 below (`state.workers.maker` / `state.workers.checker`;
   the defaults are `plan-executor-agent` (MAKER) and `code-reviewer-agent`
   (CHECKER) when the config is absent) — probe the RESOLVED names, never the
   default literals. A file-existence check
   (`.claude/agents/<name>.md`) is necessary but NOT sufficient — Claude Code pins
   the agent registry at session start (`pattern-structure.md` → "registry
   session-pinning"). **Probe mechanism, in order:**
   - If the session surfaces an available-agent-types listing (the harness's
     agent list, e.g. in the Agent tool's system context), assert BOTH names
     appear in it — the authoritative zero-dispatch probe.
   - If no such listing is introspectable, fall back to the file-existence
     check and record the RESIDUAL RISK as an event in `events.jsonl` (the
     run log): an agent file added
     after session start passes the file check yet fails dispatch. To close
     that gap, treat a dispatch-time "agent type not found" error at STEP 4/5
     as a retroactive PREFLIGHT BLOCK — emit `preflight_blocked` with the same
     remediation below and STOP; NEVER fall back to inline execution.
   Probes and failed dispatches do NOT count against `dispatches_used`.
2. **Required sub-skills** (via `Skill()`): `auto-verify`, `fix-loop`,
   `learn-n-improve` (always); `status`, `brainstorm`, `writing-plans`,
   `debugging-loop`, `systematic-debugging`, `post-fix-pipeline`,
   `escalation-report` (conditionally).
   Check each exists in `.claude/skills/<name>/SKILL.md`.
3. **MAKER ≠ CHECKER invariant.** Resolve the maker and checker `subagent_type`s
   from the contracts DAG read in STEP 1.2 — the `dispatch:` fields of the
   `execute` and `verify_review` steps (fall back to the defaults named in
   item 1 only when the config is absent). Assert the two RESOLVED values are
   DIFFERENT — comparing the literals in STEPs 4/5 cannot detect a project
   remap. Store the resolved values into `state.workers.maker` /
   `state.workers.checker` (overwriting the template defaults) — STEPs 4 and
   5.2 dispatch THESE, never hardcoded literals, so a project remap actually
   takes effect and preflight validates the agents that run. If they resolve
   to the same agent, BLOCK — independent verification is the whole point.
4. **On any missing/undispatchable dependency OR maker==checker → BLOCK** with
   verdict `WORKER_REGISTRY_NOT_LOADED`, listing the gap, and emit verbatim:
   ```
   ============================================================
   Loop Engineering: BLOCKED — WORKER_REGISTRY_NOT_LOADED
     Missing closure: <names>   (or: maker == checker)
     Fix: run /update-practices to provision the loop-engineering
          closure, then RESTART the session (agent registry is
          pinned at session start), then re-run /loop-engineering.
   ============================================================
   ```
   Write the BLOCKED verdict to `test-results/loop-engineering-verdict.json`
   using the STEP 8 schema with `result: "BLOCKED"`, plus
   `reason: "WORKER_REGISTRY_NOT_LOADED"`, `missing: [<names>]`,
   `cycles_run: 0`, `units_shipped: 0`, and `finalized_at` (a RETROACTIVE
   block at STEP 4/5 writes the actual current `cycle` and `units_shipped`
   counts, not 0);
   `emit_signal("preflight_blocked", ["loop-engineering","preflight_blocked",<missing-name | "maker-equals-checker">], "<gap>")`
   (tag slot = the missing dependency's name, or the literal
   `"maker-equals-checker"` for the maker==checker block, where nothing is
   missing; see Monitoring — this is the #1 downstream defect and MUST reach
   the hub),
   and STOP. Do NOT proceed.

Only when the closure is present, dispatchable, and maker≠checker, continue.

---

## STEP 2: DISCOVER (the automation heartbeat)

Find the next actionable unit of work toward the DoD. Source order:

1. If `$ARGUMENTS` names a concrete task/issue AND `state.argument_unit_consumed`
   is false → that is the unit; skip scanning. Once that unit completes (STEP 7
   sets `argument_unit_consumed: true`), every later DISCOVER pass falls through
   to rule 2 — so a single-issue run terminates PASSED via the nothing-actionable
   exit instead of re-executing the same unit until budgets exhaust.
2. Else triage: read CI failures, open issues (`/status`), and the DoD gap. Write
   findings to `state.triage_inbox`.

- **Nothing actionable** → terminate CLEAN (DoD already met or no work surfaced).
  `emit_signal("clean_exit", ["loop-engineering","clean_exit","no-actionable-work"],
  "DoD met / nothing actionable")` so an always-clean project is still visible to
  the hub aggregator, write `result: "PASSED"` verdict, REPORT, STOP. This is a
  valid, common exit.
- `--discover-only` (work WAS found — the nothing-actionable exit above fires
  first when it wasn't) →
  `emit_signal("clean_exit", ["loop-engineering","clean_exit","discover-only"], "triage-only run")`,
  write a `result: "PASSED"` verdict (`cycles_run: 0`, `units_shipped: 0`),
  REPORT the triage, STOP. Never emit twice on one exit.
- Otherwise select the highest-value item by `goal-anchored-decisions.md` (primary
  persona + documented priority order; correctness/safety errors rank high
  regardless of fix size) and continue.

Increment `cycle` and reset `merged_this_cycle: false`. If `cycle > max_cycles`
→ ESCALATE (STEP 6 budget arm).

---

## STEP 3: PLAN

```
Skill("/brainstorm", args="<unit of work>")     # only if the unit is novel/unclear
Skill("/writing-plans", args="<spec or unit of work>")
```

`/writing-plans` writes `docs/plans/<unit>-plan.md`. APPEND the plan path to
`state.artifacts.plans` (one entry per cycle — the STEP 8 verdict's
`plans: [...]` is read straight from this array, so multi-unit runs keep every
plan). The plan MUST carry the root-cause + full consumer/surface
map (`plan-before-coding.md`) into the maker dispatch.

---

## STEP 4: EXECUTE — the MAKER (isolated)

First record `pre_merge_sha = git rev-parse HEAD` into state — captured BEFORE
dispatch so it is defined on EVERY exit from this step (merge success, merge
conflict, or maker failure); every later diff/recompute uses it. Then dispatch
the maker as a flat worker from T0, in its own worktree so parallel cycles
cannot collide:

```
Agent(subagent_type=<state.workers.maker>,   # RESOLVED at STEP 1.5.3 — the
      # default is subagent_type="plan-executor-agent" only when config is absent
      isolation="worktree", prompt="""
## Workflow: loop-engineering
## Run ID: <run_id>   Cycle: <n>
## Plan file: <latest entry of state.artifacts.plans>
## DoD: <one-sentence DoD>
## Upstream decisions: <key decisions so far>
## Original request: <input>

Execute every task in the plan. Produce a plan + full consumer/surface map BEFORE
editing; fix the ROOT cause across ALL affected surfaces, never a one-symptom
patch (plan-before-coding.md). Commit after each task for recovery checkpointing.
Return contract: {
  "gate": "PASSED|FAILED|BLOCKED",
  "tasks_completed": <int>, "tasks_total": <int>,
  "worktree_branch": "<the git branch your worktree commits live on>",
  "changed_files": [<paths>], "blockers": [...], "summary": "<line>"
}
""")
```

Capture the return; increment `dispatches_used`. If `gate` is `BLOCKED`/`FAILED`
→ STEP 4b is SKIPPED (no merge happens): discard the maker's self-reported
`changed_files` (an unmerged claim is never handed to a reviewer) and go to
STEP 6 FEEDBACK, **maker-failed entry** (do not VERIFY a non-result).

**4b. INTEGRATE the maker's worktree (mandatory before VERIFY).** The maker's
commits live on its worktree branch — NOT in this tree. Nothing downstream may
run against an unmerged tree (it would verify unchanged code: false green or
false red, and SHIP would commit nothing):

1. Merge the returned branch into the run's working tree:
   `git merge --no-ff <worktree_branch>` (`pre_merge_sha` was recorded at
   dispatch).
2. On merge CONFLICT: abort the merge (`git merge --abort`; HEAD is back at
   `pre_merge_sha`, the maker's commits remain only on the unmerged
   `worktree_branch`) → STEP 6 FEEDBACK, **merge-conflict entry**, with the
   conflict context.
3. On success set `merged_this_cycle: true`, then recompute the authoritative
   changed-file set from the merged tree:
   `git diff --name-only <pre_merge_sha>..HEAD` → overwrite `changed_files` in
   state (the maker's self-reported list is a claim; the merged diff is proof).
4. **Operative-tree rule:** from here on, STEP 5 VERIFY (mechanical gate,
   reviewer inputs, supervisor reproduction) and STEP 6 SHIP
   (`/post-fix-pipeline` commit) ALL operate on THIS tree — the T0 working
   tree post-merge — never on the maker's worktree. STEP 5 and SHIP are
   UNREACHABLE while `merged_this_cycle` is false: no path may enter VERIFY
   without a successful 4b merge for the current unit.

---

## STEP 5: VERIFY — the CHECKER (independent; maker ≠ checker)

Two independent gates, neither run by the maker:

1. **Mechanical gate.**
   ```
   Skill("/auto-verify", args="--strict-gates --range <pre_merge_sha>..HEAD")
   ```
   Read `test-results/auto-verify.json`. The `--range` is load-bearing: the
   merge (4b) and every heal checkpoint are COMMITTED, so the working tree is
   clean and a bare invocation would detect ZERO changed files and vacuously
   green the exact merged diff this gate exists to verify. With `--range`,
   auto-verify maps tests from `git diff <pre_merge_sha>..HEAD`, skips the
   git-stash pre-existing check (runs failing tests at `<pre_merge_sha>`
   instead), treats a MISSING `test-results/fix-loop.json` as the expected
   first-verify shape (WARN, not a strict-gate BLOCK — this loop runs VERIFY
   before any fix-loop), and still BLOCKs with `NO_TESTS_FOR_CHANGE` under
   `--strict-gates` if the range is empty or uncovered.
2. **Independent review gate** — dispatch a DIFFERENT agent than the maker, given
   the maker's RAW merged diff (not its self-assessment), prompted adversarially.
   Build the dispatch context from the merged tree: capture
   `git diff <pre_merge_sha>..HEAD` — complete on EVERY entry to this step,
   first-pass or heal re-entry, because every heal is COMMITTED (STEP 6 mode 1's
   heal checkpoint commit) before VERIFY re-entry, so no reviewed state is ever
   sitting uncommitted in the working tree — and include the diff text in the prompt (if
   it exceeds the prompt budget, write it to
   `.workflows/loop-engineering/cycle-<n>.diff` and pass that path instead):
   ```
   Agent(subagent_type=<state.workers.checker>,   # RESOLVED at STEP 1.5.3 — the
         # default is subagent_type="code-reviewer-agent" only when config is absent
         prompt="""
   ## Adversarially review the maker's merged diff for run <run_id> cycle <n>.
   ## Inputs: DoD=<...>, plan=<path>, changed_files=<paths>,
   ##         diff_range=<pre_merge_sha>..HEAD
   ## RAW MERGED DIFF (output of `git diff <pre_merge_sha>..HEAD`):
   <diff text — or the .diff file path when oversized>
   Judge: is this the ROOT-cause fix across ALL surfaces (not a one-symptom patch)?
   Correctness, security-of-the-change, scope honored, no out-of-brief files?
   Return {gate: PASSED|FAILED, blocking_findings:[...], summary}.
   """)
   ```
   Increment `dispatches_used` for the checker dispatch too — the STEP 8
   dashboard counts every completed worker dispatch (maker + checker);
   preflight probes and failed dispatches stay excluded (STEP 1.5).
   This reviewer — a fresh agent given only the RAW merged diff (never the
   maker's self-assessment) — plus the T0 supervisor reproduction below
   TOGETHER realize the spec §3 "blind test verify" layer
   (`independent-test-verification.md`): a deliberate KISS composition, not a
   fourth dispatched verifier.
3. **Supervisor reproduction.** T0 (this body) MUST reproduce the claimed gate —
   re-run the test/lint command itself, and apply an output-plausibility check to
   any user-facing value (`supervisor-verification.md`,
   `output-plausibility-verification.md`). A worker's "PASSED" is a claim, not
   proof. For UI changes, drive the running app (screenshot + interact).

GATE passes only when **all three** agree: the mechanical result is `PASSED`
AND the independent reviewer returns `PASSED` AND the supervisor reproduction
concurs. Any dissent → STEP 6 FEEDBACK.

---

## STEP 6: GATE → SHIP or FEEDBACK

**PASS** (and not `--no-ship`): if this passing VERIFY resolved a FEEDBACK
heal, FIRST increment `heals` and
`emit_signal("healed", ["loop-engineering","healed",<failure-class>], "<what healed>")`
— the FAIL arm's pending emit fires here, where the outcome is known. **If a §6a
MUTATED strategy is what unstuck it** (the ledger for this signature holds ≥1
recorded failed attempt), flag the STRATEGY DELTA (the winning tuple minus the
failed ones — which axis change broke the stall) so STEP 7's `/learn-n-improve`
records it as a success pattern (see STEP 7). The flag itself MUST CARRY the
winning tuple + the failed tuples inline — the ledger entry is cleared next, so
STEP 7 cannot re-read it. Then clear
`state.strategy_ledger[<signature>]` (the stall is resolved). Then:
```
Skill("/post-fix-pipeline", args="<run_id>, test-results/auto-verify.json")
```
Captures docs update + commit (on the T0 tree the maker's branch was merged
into at STEP 4b). APPEND the sha to `state.artifacts.commits`. → STEP 7 LEARN.

**PASS with `--no-ship` (TERMINAL branch):** skip `/post-fix-pipeline` entirely;
record `state.artifacts.commits = ["SKIPPED"]` and leave `units_shipped` at 0 —
the SHIP commit was skipped (the STEP 4b integration merge, and any heal
checkpoint commits, still sit on the run branch), and the `shipped` metric
must stay honest. Run the
learning capture inline HERE (`/learn-n-improve` with args `session`) — the
run does NOT enter STEP 7 (no `shipped` emit, no loop-back); emit
`clean_exit` (tags `["loop-engineering","clean_exit","no-ship-terminal"]`)
INSTEAD of `shipped` (a resolved heal still emits `healed` first, as above).
Then go directly to STEP 8 REPORT with `result: "PASSED"` and
`Commits: SKIPPED` (meaning: only the SHIP commit was skipped). The run STOPS
after its first verified unit — it does NOT loop back to DISCOVER
(verified-but-unshipped work must not pile up under later merges).

**FAIL — self-heal (bounded).** FEEDBACK has three entry modes. Every re-entry
to STEP 5 VERIFY requires `merged_this_cycle: true` (a successful 4b merge for
the current unit) — VERIFY is unreachable otherwise. Each heal/redo increments
`retries_used` AND `budget.step_retries[<failing step>]`.

### 6a. Bilevel self-improvement — mutate the STUCK loop's SEARCH strategy (not just its lessons)

A loop that heals-and-retries the SAME search strategy with more accumulated
notes is stuck by construction. So on a REPEAT heal for the same failing gate
(heal N≥2), the orchestrator MUST change the STRATEGY itself, tracked so an
already-failed strategy is never re-run. This governs which healer/worker/model
each mode below dispatches on a repeat; it composes with the STEP 7 learning
capture — it does not replace it.

- **Failing-gate signature** — the stable key that means "this same gate failed
  again": `<failing step>:<failure class>` (e.g. `verify_review:<failing_test_id>`,
  `mechanical:<gate>`, `execute:<blocker-class>`). It reuses the
  `budget.step_retries[<step>]` keying idea. Key `state.strategy_ledger[<signature>]`
  by it.
- **Three mutation axes — each enumerable, so exhaustion is DETECTABLE:**

  | Axis | Values (cheapest → most expensive) |
  |---|---|
  | **decomposition** | `whole` → `bisected` (split the failing range/tasks in half) → `single-surface` (isolate one file/test at a time) |
  | **diagnostic** | `fix-loop` (fast analyze→fix→retest) → `debugging-loop` (structured reproduce→isolate→root-cause) |
  | **model** | `sonnet` → `opus` — the worker/model tier the healer (or re-dispatched maker) runs on; escalate the tier only AFTER ≥2 supervised failures, so **model is the LAST axis to change** (cheapest-sufficient first) |

  A strategy is the tuple `{decomposition, diagnostic, model}`; the worker/agent
  identity rides the diagnostic (which healer skill/worker runs) + the model tier.
- **Strategy-attempt record** — APPEND to `state.strategy_ledger[<signature>]` the
  moment a heal attempt FAILS (write it on re-entry, before selecting the next
  strategy):
  ```json
  {
    "attempt": <n>,
    "failing_gate": "<signature>",
    "strategy": {"decomposition": "whole", "diagnostic": "fix-loop", "model": "sonnet"},
    "worker": "<healer / re-dispatched worker identity>",
    "failure_signature": "<one line: what STILL failed after this strategy>",
    "ts": "<iso>"
  }
  ```
- **Mutation rule** — the next strategy MUST differ on ≥1 axis from EVERY recorded
  attempt for this signature. (Two distinct tuples differ on ≥1 axis, so this is
  exactly: the proposed tuple is NOT already in the ledger.) Advance along the
  preference order to the first not-yet-recorded tuple. The first axis to flip is
  CONDITIONAL on the baseline diagnostic: baseline used `fix-loop` → flip
  `diagnostic` first (fix-loop→debugging-loop); baseline already used
  `debugging-loop` (the unclear-root-cause path) → flip `decomposition` first
  (whole→bisected→single-surface) and NEVER de-escalate the diagnostic back to
  fix-loop while the same failure-class persists. Then continue: change
  `decomposition`, then escalate `model` (sonnet→opus) LAST.
- **Novelty gate (before dispatching ANY heal on a repeat)** — compare the proposed
  strategy against the ledger: identical to a recorded attempt → REJECT and mutate
  again; if EVERY enumerable tuple is already recorded → **axes exhausted** → go to
  the Budget-exhausted arm below (`/escalation-report` with the strategy ledger
  attached). Never re-run a strategy the ledger already proved failed.

The three entry modes:

1. **VERIFY dissent** (merge succeeded). The heal runs inline at T0 and edits
   the SAME post-merge tree. Before re-entering STEP 5, COMMIT the heal's
   edits (a heal checkpoint commit: `git add -A && git commit -m "heal: <what>"`
   — `add -A` so files the heal CREATED are captured too, not just tracked edits) —
   an uncommitted heal edit is invisible to the commit-to-commit diff the
   checker receives — then recompute `changed_files` from
   `git diff --name-only <pre_merge_sha>..HEAD`, which is now complete.
   **Select the strategy via §6a.** First heal for this gate → the baseline
   `{whole, fix-loop-if-root-cause-clear-else-debugging-loop, sonnet}` (record it
   if it then fails). Repeat heal (N≥2) → the novelty-gated MUTATED strategy off
   `state.strategy_ledger[<signature>]`. Dispatch the chosen diagnostic, at the
   chosen model tier, over the chosen decomposition:
   ```
   # diagnostic == fix-loop  (add --range for a bisected decomposition, one file at a time for single-surface):
   Skill("/fix-loop", args="<failure context>")
   # diagnostic == debugging-loop  (structured reproduce→isolate→root-cause→fix→verify):
   Skill("/debugging-loop", args="<failure context>")
   ```
   When the mutated strategy escalates `model` to opus, run the healer's dispatched
   workers at opus (cheapest-sufficient — escalate the tier only after ≥2 failures).
   The old fixed "fix-loop→debugging-loop after 2 fails" heuristic is now just the
   FIRST mutation step of §6a for a fix-loop baseline (backward compatible); a
   debugging-loop baseline mutates decomposition first, never back to fix-loop.
2. **Merge-conflict entry** (4b aborted; HEAD == `pre_merge_sha`; the maker's
   commits sit only on the unmerged `worktree_branch`). The heal IS the
   integration: re-run `git merge --no-ff <worktree_branch>`, resolve the
   conflicts inline at T0, commit the resolution — that completes 4b (set
   `merged_this_cycle: true`; recompute `changed_files` from
   `git diff --name-only <pre_merge_sha>..HEAD`) — then enter STEP 5 VERIFY.
   If the conflicts are not resolvable, abort again, abandon the branch
   (record it in `events.jsonl`), and re-dispatch the maker (STEP 4) with the
   conflict context — NEVER VERIFY a tree that lacks the maker's work.
3. **Maker-failed entry** (`gate: FAILED|BLOCKED`; 4b was skipped; the tree is
   still at `pre_merge_sha`). Nothing is integrated, so there is nothing to
   heal in the T0 tree — do NOT run a healer against it. Re-dispatch the maker
   (STEP 4) with the failure/blocker context appended to the plan context; the
   failed attempt's worktree branch is abandoned (record it in `events.jsonl`).
   On a REPEAT maker-failure for the same blocker signature (heal N≥2), apply the
   §6a mutation to the RE-DISPATCH itself — record the failed attempt in
   `state.strategy_ledger`, then pick a novel strategy (e.g. escalate the maker's
   `model` sonnet→opus, or `bisect` the plan into a smaller sub-unit), never a
   verbatim re-dispatch of the same `{decomposition, model}`. VERIFY is reached
   only after the redo's 4b merge succeeds.

The `healed` emit for any of these fires at the PASS arm, when the heal's
re-VERIFY passes.

**Budget exhausted** (`retries_used >= global_retry_budget` OR
`cycle > max_cycles` OR any `step_retries[<step>] > max_retries_per_step` OR
the configured wall-clock cap exceeded OR **§6a strategy axes exhausted** —
every enumerable `{decomposition, diagnostic, model}` tuple for the failing
gate is already recorded in `state.strategy_ledger[<signature>]`, so no novel
strategy remains). Honesty note: under the shipped default
`max_retries_per_step: 3` the per-step budget veto normally fires long before
the 12 enumerable tuples are explored — the budget dominates and terminates
the search first; the axes-exhaustion terminal is the BACKSTOP for
configurations that raise `max_retries_per_step` (and the ledger is keyed by
`<step>:<failure-class>` while `step_retries` is keyed by `<step>` alone, so
multiple failure classes on one step share the same budget counter):
```
Skill("/escalation-report", args="<run_id>")   # attach state.strategy_ledger[<signature>] — the strategies already tried + their failure signatures
```
Append the unresolved unit to `state.triage_inbox` with what was tried
(including the full strategy ledger for the failing gate — every mutation
attempted and why each failed, so a human/Ring-2 fixes the CONTRACT rather than
re-trying an exhausted search),
`emit_signal("escalated", ["loop-engineering","escalated",<unit-class>], "<unit + what was tried>")`.
When the capped unit was never attempted (a clean run that hit `max_cycles`
with one more unit discovered), say so explicitly — message
`"<unit> — not attempted: max_cycles reached"`, what-was-tried = `"nothing —
cycle cap"`. Then go to STEP 8 REPORT with `result: "ESCALATED"` (write the
verdict + dashboard + handoff — ESCALATED terminates through STEP 8, same as
PASSED). NEVER loop unbounded — a loop running unattended is a loop making
mistakes unattended (Osmani).

---

## STEP 7: LEARN (self-learning, every shipped cycle)

```
Skill("/learn-n-improve", args="session")
```
Captures the discover→plan→make→check→ship pattern (and any heal) into
`.claude/learnings.json`, typed GENERIC vs PRODUCT-SPECIFIC (`learnings-routing.md`).
**If a §6a strategy mutation unstuck a stalled gate this cycle** (flagged at the
STEP 6 PASS arm), this `/learn-n-improve` call MUST also record the STRATEGY DELTA
as a `success_patterns` entry — its existing schema carries this with no change:
`attempted` = the stuck gate + the strategies that failed; `worked` = the winning
`{decomposition, diagnostic, model}` tuple; `mechanism` = which axis change broke
the stall (e.g. "fix-loop→debugging-loop surfaced the real root cause the fast
retry kept missing"); `reuse_trigger` = "when a heal stalls on <gate class>, mutate
<that axis> first"; `type` GENERIC (the bilevel-search craft) unless the delta is
this codebase's own quirk. This is the memory of what unstuck the loop, so the next
stall mutates the winning axis first instead of rediscovering it.
Then directly increment `units_shipped` and
`emit_signal("shipped", ["loop-engineering","shipped",<unit-class>], "<unit>")`
for hub monitoring — this is the SINGLE emit site for `shipped` (exactly one
entry per shipped unit; STEP 6 SHIP emits nothing, and do NOT rely on
`/learn-n-improve` to set the link — see Monitoring). Mark the unit consumed:
if it was the `$ARGUMENTS`-named unit, set `state.argument_unit_consumed: true`
so DISCOVER never re-selects it. Then loop back to STEP 2 DISCOVER for the next
unit, until DISCOVER finds nothing actionable or a budget caps the run.
(`--no-ship` runs never reach this step — their learning capture ran inline at
STEP 6 and `clean_exit` replaced `shipped`.)

---

## STEP 8: REPORT

1. **Finalize state + verdict.** Write `test-results/loop-engineering-verdict.json`:
   ```json
   {
     "schema_version": "1.0.0",
     "run_id": "<run_id>",
     "result": "PASSED | ESCALATED | BLOCKED",
     "dod": "<one-sentence DoD>",
     "cycles_run": <int>,
     "units_shipped": <int>,
     "artifacts": { "plans": [...], "commits": [...], "learnings": ".claude/learnings.json" },
     "budget_used": { "retries_used": <n>, "dispatches_used": <n> },
     "triage_inbox": "<path>",
     "finalized_at": "<iso>"
   }
   ```
2. **Dashboard:**
   ```
   ============================================================
   Loop Engineering: <PASSED | ESCALATED | BLOCKED>
     Run ID: <run_id>   Cycles: <n>/<max>
     Units shipped: <n>   Heals: <n>   Dispatches: <n>
     Commits: <shas or SKIPPED>
     Open (triage inbox): <count>  → <path>
     Evidence: test-results/loop-engineering-verdict.json
   ============================================================
   ```
3. **Handoff:** if ESCALATED, point at the triage inbox; if PASSED with commits,
   suggest `/code-review-workflow`.

---

## Fable-5 runtime notes (spec §3.9)

When the loop driver or a dispatched worker runs on `claude-fable-5`:

1. **Early-stopping guard** — include the official autonomous-pipeline reminder in the
   driver/worker prompt (verbatim text: spec §3.9(b)). It prevents the rare text-only
   "I'll now run X" turn-end deep into long runs. Environments that already inject an
   equivalent autonomy reminder per turn (hook-based governance) are covered; add it
   explicitly everywhere else — especially headless/cron/raw-API runs.
2. **Mid-run owner messaging** — don't go silent until STEP 8: at each cycle boundary and
   on every ESCALATE arm, send a one-line progress ping through the project's Notifier
   gateway if configured (fail-open no-op otherwise). Raw-API harnesses use a client-side
   `send_to_user` tool with system-prompt elicitation instead. Verbatim-worthy content
   only — never narration or reasoning.
3. **Raw-API loops only** — pass `output_config.task_budget` (beta `task-budgets-2026-03-13`,
   min 20k tokens, advisory) as the spend-domain budget alongside `state.json`'s
   work-retry budgets; the two compose and neither substitutes for the other. Not
   available inside Claude Code sessions. A too-small budget causes refusal-like early
   stops — raise it before debugging anything else.

---

## Monitoring & telemetry (hub-ward feedback signal)

The loop's runtime artifacts (`test-results/loop-engineering-verdict.json`, the
triage inbox) are gitignored and never leave the project. To make the loop
**observable from the hub** without a new pipeline, every signal-emitting
outcome — the terminal exits, plus the mid-run `shipped` (per unit, STEP 7)
and `healed` (PASS arm) marks — ALSO
appends one entry to the project's `.claude/learnings.json` — the same file the
hub's weekly `aggregate_telemetry.py` already scans. The hub aggregator keys on
`hub_pattern_link` and groups recurring defect classes by `tags`
(`compute_error_prevention_rate`), so escalations/blocks surface as per-pattern
effectiveness in `registry/patterns.json` automatically (Friday cron, enrolled
repos in `config/repos.yml`). No new uploader, no outward call from the project.

**emit_signal(signal, tags, message)** — read `.claude/learnings.json` (treat a
missing file as `{"learnings": []}`), APPEND (never overwrite) one entry, write back:

```json
{
  "hub_pattern_link": "loop-engineering",
  "signal": "shipped | healed | escalated | preflight_blocked | clean_exit",
  "tags": ["loop-engineering", "<signal>", "<stable defect/unit class>"],
  "error": { "message": "<one-line what happened>" },
  "run_id": "<run_id>",
  "ts": "<iso>"
}
```

Use a STABLE `tags` signature per defect class (e.g. the failing test id or the
missing-closure name) — the aggregator counts a class that recurs across runs as
"recurring despite the pattern" (lower effectiveness), and a one-off as addressed.

Emit points (exactly ONE entry per triggering outcome — a single outcome never
emits the same signal twice; where a signal lists more than one site, the
sites are mutually exclusive at runtime):
- **STEP 1.5 BLOCK (incl. retroactive at STEP 4/5)** → `emit_signal("preflight_blocked", ["loop-engineering","preflight_blocked",<missing-name | "maker-equals-checker">], "<closure gap or maker==checker>")`.
- **STEP 2 clean exit / STEP 2 `--discover-only` / STEP 6 `--no-ship` terminal** → `emit_signal("clean_exit", ["loop-engineering","clean_exit",<"no-actionable-work"|"discover-only"|"no-ship-terminal">], "<why>")`.
- **STEP 7 LEARN** → `emit_signal("shipped", ["loop-engineering","shipped",<unit-class>], "<unit>")` — the SINGLE `shipped` emit site; STEP 6 SHIP emits nothing (a second emit would double-count the spec §5.1 effectiveness metric).
- **STEP 6 PASS arm, when the passing VERIFY resolved a heal** → `emit_signal("healed", ["loop-engineering","healed",<failure-class>], "<what was healed>")`.
- **STEP 6 budget exhaustion / ESCALATE** → `emit_signal("escalated", ["loop-engineering","escalated",<unit-class>], "<unresolved unit + what was tried>")`.

The DIRECT `emit_signal` path above is **authoritative for all five signals**. Do
NOT rely on `/learn-n-improve` to set `hub_pattern_link` — in unattended mode it
defaults that field to `null`, so a delegated entry is never matched by the
aggregator. `/learn-n-improve` still runs for its own learning capture; it does
not replace the `shipped`/`healed` emit.

**Constraint — the project MUST commit `.claude/learnings.json`.** The hub reads
the COMMITTED file via the GitHub API; a gitignored learnings file emits no
hub-ward signal (same constraint as all error-prevention telemetry).

---

## CRITICAL RULES

- MUST emit a hub-linked `.claude/learnings.json` entry (`hub_pattern_link:
  "loop-engineering"`) for every signal — the terminal `preflight_blocked`,
  `escalated`, `clean_exit` plus the mid-run `healed` and `shipped` — from
  its defined emit
  point (one entry per triggering outcome, never two for the same outcome),
  so the hub's weekly aggregator can monitor this pattern's downstream
  defects/effectiveness without double counting. The defect signals
  (`preflight_blocked`, `escalated`) MUST NOT be skipped — they are the whole
  point of downstream monitoring.
- MUST integrate the maker's worktree branch into the run's working tree
  (STEP 4b merge) BEFORE VERIFY — verifying or shipping an unmerged tree is a
  false gate (false green/red, empty commit). STEP 5 VERIFY and SHIP are
  UNREACHABLE while `merged_this_cycle` is false: a merge CONFLICT or a maker
  `FAILED|BLOCKED` return enters FEEDBACK's merge-conflict / maker-failed
  modes (complete the integration or re-dispatch the maker) — never VERIFY.
  MUST recompute `changed_files` from the merged tree via `pre_merge_sha`
  (captured at STEP 4 dispatch, so it is always defined) — and again after
  every heal, whose edits MUST be COMMITTED (heal checkpoint commit) BEFORE
  re-entering VERIFY so `git diff <pre_merge_sha>..HEAD` is complete on every
  entry — so the reviewer never grades a stale or partial diff, and MUST hand
  the checker the RAW merged diff itself, not a path list.
- MUST run STEP 1.5 PREFLIGHT before any dispatch and BLOCK with
  `WORKER_REGISTRY_NOT_LOADED` if a worker/sub-skill is missing OR maker==checker.
  Provisioning does not resolve closures — a downstream project can have this skill
  without its workers; a silent inline run is the failure this prevents.
- MUST keep MAKER ≠ CHECKER — EXECUTE and the review gate MUST be different
  `subagent_type`s, and STEPs 4/5.2 MUST dispatch the STEP 1.5.3-RESOLVED
  `state.workers` values (defaults `plan-executor-agent` / `code-reviewer-agent`
  only when the config is absent) — never hardcoded literals a project's
  contract remap would bypass. The author never
  grades its own homework (`independent-test-verification.md`).
- MUST reproduce the checker's gate at T0 before SHIP — a worker's "PASSED" is a
  claim, not proof (`supervisor-verification.md`); apply an output-plausibility
  check to user-facing values.
- MUST be BOUNDED + TERMINATING — honor `global_retry_budget` and `--max-cycles`;
  on exhaustion run `/escalation-report` and write the unit to the triage inbox.
  NEVER loop unbounded.
- MUST mutate the SEARCH STRATEGY on a repeat heal (heal N≥2 for the same failing
  gate), not just accumulate lessons and retry (§6a). Record each failed heal
  attempt's strategy (`{decomposition, diagnostic, model}` + the failure signature)
  in `state.strategy_ledger[<signature>]`, and select a next strategy that differs
  on ≥1 axis from EVERY recorded attempt (novelty gate). Identical strategy →
  REJECT and mutate again; all enumerable tuples exhausted → `/escalation-report`
  with the strategy ledger attached. MUST capture the winning strategy delta as a
  `/learn-n-improve` success pattern when a mutation unstuck the loop (STEP 7).
- MUST run at T0 — if dispatched as a worker, `Agent` is stripped and the
  maker/checker dispatch silently inlines (the 2026-04-24 platform failure mode).
- MUST NOT SHIP if VERIFY failed or `--no-ship` is set — unverified code reaching
  commit destroys the loop's trust model.
- MUST capture a learning every shipped cycle (`/learn-n-improve`) — a loop that
  does not learn repeats its mistakes.
- MUST anchor unit selection to the documented goal + primary persona
  (`goal-anchored-decisions.md`) — never build to fill a matrix hole.
- MUST pass upstream artifacts + decisions + the DoD into every worker dispatch —
  no worker starts from scratch.
