---
name: loop-engineering
description: >
  Run a repeatable, autonomous feedback loop — DISCOVER → PLAN → EXECUTE →
  VERIFY → (SHIP | FEEDBACK) — as a skill-at-T0 orchestrator. The skill body IS
  the orchestrator: it runs in the user's T0 session, dispatches a MAKER worker
  (plan-executor-agent) and a SEPARATE CHECKER (code-reviewer-agent) via Agent()
  so the author never grades its own work, and self-heals on failure by looping
  through /fix-loop or /debugging-loop under hard budgets. Self-verifying
  (maker≠checker), self-healing (feedback arm), self-learning (/learn-n-improve
  each cycle), self-feedback (/escalation-report on budget exhaustion). Use to
  run unattended work to a Definition of Done — triggered by /loop, /goal, cron,
  or a PR. For a single feature use /development-loop; for one bug use
  /debugging-loop; this is the autonomous meta-loop that ROUTES into them.
type: workflow
triggers:
  - autonomous loop
  - loop engineering
  - run autonomously until done
  - self-healing loop
  - maker checker loop
  - discover plan execute verify loop
  - unattended feedback cycle
allowed-tools: "Agent Bash Read Write Edit Grep Glob Skill"
argument-hint: "<goal / Definition of Done, issue URL, or triage source> [--max-cycles N] [--no-ship]"
version: "1.1.0"
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
re-implement them. Canonical design: `docs/specs/loop-engineering-spec.md`.

**Self-\* spine (composed, not built):** healing = `/fix-loop` · `/debugging-loop`
· `/systematic-debugging`; verification = maker≠checker
(`supervisor-verification.md` + `independent-test-verification.md`); learning =
`/learn-n-improve`; feedback = `/escalation-report` + triage inbox.

**Input:** `$ARGUMENTS` — a Definition of Done, issue URL, or triage source. If
empty, ask the user for the DoD before proceeding (an autonomous loop with no DoD
cannot terminate — `dod-verbs.md`).

---

## CLI Signature

```
/loop-engineering <DoD | issue URL | triage source>
                  [--max-cycles N]   # default 5; hard cap on full loop iterations
                  [--no-ship]        # stop after VERIFY; never commit
                  [--discover-only]  # run DISCOVER + report, no execution
```

| Flag | Default | Meaning |
|------|---------|---------|
| `--max-cycles` | 5 | Hard cap on DISCOVER→…→GATE iterations before escalating |
| `--no-ship` | off | Stop after VERIFY passes; do not run SHIP (commit) |
| `--discover-only` | off | Triage only — surface actionable work, then stop |

---

## STEP 1: INIT

1. **Parse args + Definition of Done.** Restate the DoD as one load-bearing
   sentence with a precise verb + completeness bar (`dod-verbs.md`). If it is not
   stateable, STOP and ask — an autonomous loop satisfies the *weakest* reading of
   a vague goal.
2. **Read config.** `Read .claude/config/workflow-contracts.yaml` (hub repo:
   `config/workflow-contracts.yaml`; if absent, use the inline DAG below — this
   skill is self-contained) → `workflows.loop-engineering`. Pull the step DAG,
   gates, and budgets. `master_agent` should be null; `sub_orchestrators` empty.
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
     "budget": { "global_retry_budget": 15, "retries_used": 0, "dispatches_used": 0 },
     "step_status": { "INIT": "done" },
     "artifacts": {},
     "triage_inbox": ".workflows/loop-engineering/triage-inbox.md"
   }
   ```
5. **Append INIT event** to `events.jsonl`.

---

## STEP 1.5: PREFLIGHT (dependency-closure gate — BLOCK on missing workers)

Provisioning copies skills/agents by tier and does NOT always resolve a skill's
full dependency closure — a project can end up with `/loop-engineering` but
without its workers. Catch that here with an actionable BLOCK, never a silent
inline run (the 2026-04-24 failure mode).

1. **Required workers** (dispatched via `Agent()`): `plan-executor-agent` (MAKER),
   `code-reviewer-agent` (CHECKER). A file-existence check
   (`.claude/agents/<name>.md`) is necessary but NOT sufficient — Claude Code pins
   the agent registry at session start (`pattern-structure.md` → "registry
   session-pinning"). Probe runtime dispatchability early.
2. **Required sub-skills** (via `Skill()`): `auto-verify`, `fix-loop`,
   `learn-n-improve` (always); `brainstorm`, `writing-plans`, `debugging-loop`,
   `systematic-debugging`, `post-fix-pipeline`, `escalation-report` (conditionally).
   Check each exists in `.claude/skills/<name>/SKILL.md`.
3. **MAKER ≠ CHECKER invariant.** Assert the resolved maker `subagent_type` and
   checker `subagent_type` are DIFFERENT. If a project remapped them to the same
   agent, BLOCK — independent verification is the whole point.
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
   Write the BLOCKED verdict to `test-results/loop-engineering-verdict.json`,
   `emit_signal("preflight_blocked", ["loop-engineering","preflight_blocked",<missing-name>], "<gap>")`
   (see Monitoring — this is the #1 downstream defect and MUST reach the hub),
   and STOP. Do NOT proceed.

Only when the closure is present, dispatchable, and maker≠checker, continue.

---

## STEP 2: DISCOVER (the automation heartbeat)

Find the next actionable unit of work toward the DoD. Source order:

1. If `$ARGUMENTS` names a concrete task/issue → that is the unit; skip scanning.
2. Else triage: read CI failures, open issues (`/status`), and the DoD gap. Write
   findings to `state.triage_inbox`.

- **Nothing actionable** → terminate CLEAN (DoD already met or no work surfaced).
  Write `result: "PASSED"` verdict, REPORT, STOP. This is a valid, common exit.
- `--discover-only` → REPORT the triage and STOP.
- Otherwise select the highest-value item by `goal-anchored-decisions.md` (primary
  persona + documented priority order; correctness/safety errors rank high
  regardless of fix size) and continue.

Increment `cycle`. If `cycle > max_cycles` → ESCALATE (STEP 6 budget arm).

---

## STEP 3: PLAN

```
Skill("/brainstorm", args="<unit of work>")     # only if the unit is novel/unclear
Skill("/writing-plans", args="<spec or unit of work>")
```

`/writing-plans` writes `docs/plans/<unit>-plan.md`. Capture into
`state.artifacts.plan`. The plan MUST carry the root-cause + full consumer/surface
map (`plan-before-coding.md`) into the maker dispatch.

---

## STEP 4: EXECUTE — the MAKER (isolated)

Dispatch the maker as a flat worker from T0, in its own worktree so parallel
cycles cannot collide:

```
Agent(subagent_type="plan-executor-agent", isolation="worktree", prompt="""
## Workflow: loop-engineering
## Run ID: <run_id>   Cycle: <n>
## Plan file: <path from state.artifacts.plan>
## DoD: <one-sentence DoD>
## Upstream decisions: <key decisions so far>
## Original request: <input>

Execute every task in the plan. Produce a plan + full consumer/surface map BEFORE
editing; fix the ROOT cause across ALL affected surfaces, never a one-symptom
patch (plan-before-coding.md). Commit after each task for recovery checkpointing.
Return contract: {
  "gate": "PASSED|FAILED|BLOCKED",
  "tasks_completed": <int>, "tasks_total": <int>,
  "changed_files": [<paths>], "blockers": [...], "summary": "<line>"
}
""")
```

Capture the return; increment `dispatches_used`. If `gate` is `BLOCKED`/`FAILED`
→ go to STEP 6 FEEDBACK (do not VERIFY a non-result).

---

## STEP 5: VERIFY — the CHECKER (independent; maker ≠ checker)

Two independent gates, neither run by the maker:

1. **Mechanical gate.**
   ```
   Skill("/auto-verify", args="--strict-gates")
   ```
   Read `test-results/auto-verify.json`.
2. **Independent review gate** — dispatch a DIFFERENT agent than the maker, given
   the maker's RAW diff (not its self-assessment), prompted adversarially:
   ```
   Agent(subagent_type="code-reviewer-agent", prompt="""
   ## Adversarially review the maker's changed_files for run <run_id> cycle <n>.
   ## Inputs: changed_files=<paths>, DoD=<...>, plan=<path>
   Judge: is this the ROOT-cause fix across ALL surfaces (not a one-symptom patch)?
   Correctness, security-of-the-change, scope honored, no out-of-brief files?
   Return {gate: PASSED|FAILED, blocking_findings:[...], summary}.
   """)
   ```
3. **Supervisor reproduction.** T0 (this body) MUST reproduce the claimed gate —
   re-run the test/lint command itself, and apply an output-plausibility check to
   any user-facing value (`supervisor-verification.md`,
   `output-plausibility-verification.md`). A worker's "PASSED" is a claim, not
   proof. For UI changes, drive the running app (screenshot + interact).

GATE passes only when **both** the mechanical result is `PASSED` AND the
independent reviewer returns `PASSED` AND the supervisor reproduction agrees. Any
dissent → STEP 6 FEEDBACK.

---

## STEP 6: GATE → SHIP or FEEDBACK

**PASS** (and not `--no-ship`):
```
Skill("/post-fix-pipeline", args="<run_id>, test-results/auto-verify.json")
```
Captures docs update + commit. Record `state.artifacts.commit_sha`. → STEP 7 LEARN.

**FAIL — self-heal (bounded):** pick the healer by root-cause clarity, then
return to STEP 5 VERIFY and increment `retries_used`. When a heal subsequently
PASSES VERIFY, `emit_signal("healed", ["loop-engineering","healed",<failure-class>], "<what healed>")`:

```
# clear root cause:
Skill("/fix-loop", args="<failure context>")
# unclear root cause OR 2+ failed cycles on the same unit (does diagnose→fix→verify→learn):
Skill("/debugging-loop", args="<failure context>")
```

**Budget exhausted** (`retries_used >= global_retry_budget` OR
`cycle > max_cycles`):
```
Skill("/escalation-report", args="<run_id>")
```
Append the unresolved unit to `state.triage_inbox` with what was tried,
`emit_signal("escalated", ["loop-engineering","escalated",<unit-class>], "<unit + what was tried>")`,
then STOP with `result: "ESCALATED"`. NEVER loop unbounded — a loop running
unattended is a loop making mistakes unattended (Osmani).

---

## STEP 7: LEARN (self-learning, every shipped cycle)

```
Skill("/learn-n-improve", args="session")
```
Captures the discover→plan→make→check→ship pattern (and any heal) into
`.claude/learnings.json`, typed GENERIC vs PRODUCT-SPECIFIC (`learnings-routing.md`).
Ensure the shipped-cycle entry is tagged for hub monitoring —
`emit_signal("shipped", ["loop-engineering","shipped",<unit-class>], "<unit>")`
(or have `/learn-n-improve` write the entry WITH `hub_pattern_link:
"loop-engineering"`). Then loop back to STEP 2 DISCOVER for the next unit, until
DISCOVER finds nothing actionable or a budget caps the run.

---

## STEP 8: REPORT

1. **Finalize state + verdict.** Write `test-results/loop-engineering-verdict.json`:
   ```json
   {
     "schema_version": "1.0.0",
     "run_id": "<run_id>",
     "result": "PASSED | ESCALATED | BLOCKED | FAILED",
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
   Loop Engineering: <PASSED | ESCALATED | BLOCKED | FAILED>
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

## Monitoring & telemetry (hub-ward feedback signal)

The loop's runtime artifacts (`test-results/loop-engineering-verdict.json`, the
triage inbox) are gitignored and never leave the project. To make the loop
**observable from the hub** without a new pipeline, every terminal outcome ALSO
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
  "signal": "shipped | healed | escalated | preflight_blocked",
  "tags": ["loop-engineering", "<signal>", "<stable defect/unit class>"],
  "error": { "message": "<one-line what happened>" },
  "run_id": "<run_id>",
  "ts": "<iso>"
}
```

Use a STABLE `tags` signature per defect class (e.g. the failing test id or the
missing-closure name) — the aggregator counts a class that recurs across runs as
"recurring despite the pattern" (lower effectiveness), and a one-off as addressed.

Emit points (each writes exactly one entry):
- **STEP 1.5 BLOCK** → `emit_signal("preflight_blocked", ["loop-engineering","preflight_blocked",<missing-name>], "<closure gap or maker==checker>")`.
- **STEP 6 SHIP** → `emit_signal("shipped", ["loop-engineering","shipped",<unit-class>], "<unit>")` (in addition to STEP 7 LEARN).
- **STEP 6 FEEDBACK after a successful heal** → `emit_signal("healed", ["loop-engineering","healed",<failure-class>], "<what was healed>")`.
- **STEP 6 budget exhaustion / ESCALATE** → `emit_signal("escalated", ["loop-engineering","escalated",<unit-class>], "<unresolved unit + what was tried>")`.

`/learn-n-improve` at STEP 7 MAY satisfy the `shipped`/`healed` emission if it
writes the entry with `hub_pattern_link: "loop-engineering"`; the defect signals
(`preflight_blocked`, `escalated`) MUST be emitted directly here because they
occur on paths where STEP 7 never runs.

---

## CRITICAL RULES

- MUST emit a hub-linked `.claude/learnings.json` entry (`hub_pattern_link:
  "loop-engineering"`) on every terminal outcome — `preflight_blocked`,
  `escalated`, `healed`, `shipped` — so the hub's weekly aggregator can monitor
  this pattern's downstream defects/effectiveness. The defect signals
  (`preflight_blocked`, `escalated`) MUST NOT be skipped — they are the whole
  point of downstream monitoring.
- MUST run STEP 1.5 PREFLIGHT before any dispatch and BLOCK with
  `WORKER_REGISTRY_NOT_LOADED` if a worker/sub-skill is missing OR maker==checker.
  Provisioning does not resolve closures — a downstream project can have this skill
  without its workers; a silent inline run is the failure this prevents.
- MUST keep MAKER ≠ CHECKER — EXECUTE (`plan-executor-agent`) and the review gate
  (`code-reviewer-agent`) MUST be different `subagent_type`s. The author never
  grades its own homework (`independent-test-verification.md`).
- MUST reproduce the checker's gate at T0 before SHIP — a worker's "PASSED" is a
  claim, not proof (`supervisor-verification.md`); apply an output-plausibility
  check to user-facing values.
- MUST be BOUNDED + TERMINATING — honor `global_retry_budget` and `--max-cycles`;
  on exhaustion run `/escalation-report` and write the unit to the triage inbox.
  NEVER loop unbounded.
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
