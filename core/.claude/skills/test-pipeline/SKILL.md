---
name: test-pipeline
description: >
  Run the full three-lane test verification pipeline as a skill-at-T0
  orchestrator. The skill body IS the orchestrator — it runs in the user's T0
  session and dispatches worker subagents (scout, functional/API testers,
  visual-inspector, analyzer, issue-manager, fixers) via Agent() at T0 where
  subagent dispatch actually works. Enforces the JOIN gate, triage subgraph,
  verify-affected loop, and final commit per spec v2.2. Use for the full
  fix→verify→commit chain; for verification only, use /auto-verify.
type: workflow
allowed-tools: "Agent Bash Read Write Edit Grep Glob Skill"
argument-hint: "[failure_output] [--capture-proof | --no-capture-proof] [--skip-fix] [--only-issues N,M] [--fix-pr-mode] [--full-suite-before-success] [--update-baselines]"
triggers:
  - test pipeline
  - fix verify commit
  - verify and commit
  - full test pipeline
  - test verification pipeline
  - run test pipeline
version: "2.0.0"
---

# /test-pipeline — Skill-at-T0 Orchestrator

This skill's body is injected into the user's T0 session and executed there.
The T0 session owns the full pipeline lifecycle (STEPS 1–9 below) and dispatches
worker subagents via `Agent()` at T0 — the only reliably-parallel dispatch
point in Claude Code (see `core/.claude/rules/agent-orchestration.md` §2 and
spec `docs/specs/test-pipeline-three-lane-spec-v2.md` §3.0).

**Why this is a skill-at-T0 and not a thin wrapper:** v1's `testing-pipeline-master-agent`
→ `test-pipeline-agent` → lane workers → `failure-triage-agent` → fan-out workers
chain depended on nested `Agent()` dispatch. Anthropic's platform does not forward
`Agent` to dispatched subagents ([docs](https://code.claude.com/docs/en/sub-agents),
[GH #19077](https://github.com/anthropics/claude-code/issues/19077),
[GH #4182](https://github.com/anthropics/claude-code/issues/4182)). v2 dissolves
the intermediate orchestrators and runs the orchestration logic at T0.

**Arguments:** `$ARGUMENTS`

---

## CLI Signature

```
/test-pipeline [failure_output]
               [--capture-proof | --no-capture-proof]
               [--skip-fix]
               [--only-issues N,M]
               [--fix-pr-mode]
               [--full-suite-before-success]
               [--update-baselines]
```

| Flag | Default | Meaning |
|------|---------|---------|
| `failure_output` | — | Test failure text to feed into triage (enters Fix mode directly) |
| `--capture-proof` / `--no-capture-proof` | on (config) | Capture screenshots on every test for visual review |
| `--skip-fix` | off | Start at STEP 5 JOIN (assume tests already ran); skip triage+fix |
| `--only-issues N,M` | — | Restrict triage to listed GitHub Issue numbers |
| `--fix-pr-mode` | off | Open fixes as a single PR (via `/pipeline-fix-pr`) instead of N serial commits |
| `--full-suite-before-success` | off | Force STEP 8 final full-suite pass before commit |
| `--update-baselines` | off | Visual baselines regenerate mode — STEPS 6–7 skip, STEP 4 writes baselines instead of comparing (REQ-S002) |

Mutually exclusive: `--skip-fix` and `--update-baselines` MUST NOT both be set.

---

## STEP 1: INIT

1. **Validate args + resolve mode.** Parse `$ARGUMENTS`. If `failure_output` is
   non-empty OR `--skip-fix` is absent, the pipeline runs all 9 steps (Full
   mode). If `--skip-fix` is set, skip to STEP 5 (Verify mode). If
   `--update-baselines` is set, skip STEPS 6–7 entirely (Baseline-update mode).
2. **Read config.** `Read .claude/config/test-pipeline.yml`. Required keys
   (schema 2.0.0): `capture_proof.enabled`, `lanes.ui.use_checkpoint`,
   `lanes.parallel_classifier.enabled`, `lanes.parallel_classifier.min_test_count`,
   `budgets.max_total_dispatches` (default 100), `budgets.max_wall_clock_minutes`
   (default 90), `budgets.global_retries_remaining` (default 15),
   `concurrency.max_concurrent_analyzers` (default 5),
   `concurrency.max_concurrent_issue_managers` (default 5),
   `concurrency.max_concurrent_fixers` (default 5), `auto_heal.*`.
3. **Generate `run_id`.** Format: `{UTC ISO-8601}_{7-char git sha}` with `:`
   replaced by `-`. Bash: `run_id="$(date -u +%Y-%m-%dT%H-%M-%SZ)_$(git rev-parse --short=7 HEAD)"`.
4. **Clean prior artifacts.** Remove `test-results/`, `test-evidence/`, and
   `.workflows/testing-pipeline/` from any prior run. Keep the 3 most recent
   `test-evidence/{run_id}/` directories; delete older ones.
5. **Initialize state.** `Write .workflows/testing-pipeline/state.json`:
   ```json
   {
     "schema_version": "2.0.0",
     "run_id": "<run_id>",
     "started_at": "<iso-8601>",
     "mode": "Full | Verify | BaselineUpdate",
     "flags": { "capture_proof": true, ... },
     "queues": { "functional": [], "api": [], "ui": [] },
     "tracks_required_per_test": {},
     "step_status": { "INIT": "done", "SCOUT": "pending", ... },
     "dispatches_used": 0,
     "wall_clock_started_at": "<iso-8601>",
     "global_retries_remaining": 15
   }
   ```
6. **Append INIT event** to `.workflows/testing-pipeline/events.jsonl`:
   `{"ts": "<iso>", "event": "INIT", "run_id": "<run_id>", "mode": "<mode>"}`.

---

## STEP 2: SCOUT

Dispatch the scout at T0 (one `Agent()` call):

```
Agent(subagent_type="test-scout-agent", prompt="""
## Mode: classify
## Run ID: <run_id>
## State: .workflows/testing-pipeline/state.json
## Config: .claude/config/test-pipeline.yml

Walk every test file in the project. For each test, determine which tracks
(functional, api, ui) it belongs to. Populate the queues + tracks_required_per_test
map in the state file. For queues larger than 1000 entries, emit a sidecar
(.workflows/testing-pipeline/queue-{lane}.jsonl) and record the sidecar path
in state.json instead.

Return a contract: {
  "gate": "PASSED|FAILED",
  "test_count": <int>,
  "queues": { "functional": <count>, "api": <count>, "ui": <count> },
  "sidecars": [<paths>],
  "summary": "<one line>"
}
""")
```

After the contract returns:

1. Merge the returned counts into `state.json`.
2. Increment `dispatches_used` by 1.
3. If `gate: FAILED`, abort pipeline with `BLOCKED` verdict; skip to STEP 9 with
   failure reason `SCOUT_FAILED`.
4. Decide Wave 1 topology using the classifier flag (Q4 decision):
   - If `lanes.parallel_classifier.enabled: true` AND
     `test_count >= lanes.parallel_classifier.min_test_count`: **parallel Wave 1**.
   - Otherwise: **serial Wave 1** (functional fully, then api).

Record `wave1_topology` in `state.json` for resume/debug.

---

## STEP 3: WAVE 1 — Functional + API

**Lane skip rule (REQ-M001 / v1 §3.3 NN-4):** If a lane's queue is empty,
record a synthetic `SKIP` result in `test-results/{lane}.json` with
`{"result": "SKIP", "reason": "EMPTY_QUEUE"}` and do NOT dispatch. This
is checked per-lane BEFORE any dispatch.

### Parallel topology (default for >= min_test_count tests)

Emit both `Agent()` calls in **one T0 assistant message** (this is how
parallel dispatch actually works — see agent-orchestration.md §2 final rule):

```
Agent(subagent_type="tester-agent", prompt="""
## Lane: functional
## Capture proof: <bool>
## Run ID: <run_id>
## Queue: <queues.functional or sidecar path>
## Output: test-results/functional.json + functional.jsonl
## Screenshots: test-evidence/<run_id>/screenshots/
## Stack runner: <detected — pytest-dev | jest-dev | vitest-dev | fastapi-run-backend-tests | etc.>

Run every test in the queue with --capture-proof=<bool>. Return lane contract:
{"gate": "PASSED|FAILED", "summary": "<line>", "artifacts": {...}, "failures": [...]}
""")

Agent(subagent_type="fastapi-api-tester-agent", prompt="""
## Lane: api
## Run ID: <run_id>
## Queue: <queues.api>
## Output: test-results/api.json + api.jsonl

Run API tests in the queue. If contract files are present, invoke
Skill(\"/contract-test\", ...). Combined verdict per spec §3.2.
Return lane contract.
""")
```

For non-FastAPI projects, the api-lane owner is `tester-agent` + stack-
appropriate runner skill (`/contract-test` + `/integration-test`).

### Serial topology (for small suites or classifier disabled)

Dispatch functional first; wait for contract; then dispatch api. Same prompts.

### After both lane contracts return

1. Read `test-results/functional.json` and `test-results/api.json`.
2. Merge lane gates into `state.json` → `step_status.WAVE1 = done`.
3. Increment `dispatches_used` by the number of `Agent()` calls issued.

---

## STEP 4: WAVE 2 — UI/Visual Lane

**Lane skip rule:** If `queues.ui` is empty, record a synthetic `SKIP` in
`test-results/ui.json` and proceed to STEP 5 without dispatching.

### Checkpoint early-start (REQ-S006)

If `lanes.ui.use_checkpoint: true` in `test-pipeline.yml`:

1. While the functional lane is still running (STEP 3 in parallel topology),
   T0 polls `test-results/functional.ui-tests-complete.flag` every 3 seconds
   (max 30s wait).
2. If the flag appears before Wave 1 fully returns: dispatch `visual-inspector-agent`
   immediately (in parallel with the still-running functional lane's non-UI tests).
3. Else: wait for Wave 1 to fully return, then dispatch.

If `lanes.ui.use_checkpoint: false` (default): always wait for Wave 1 full return.

### Dispatch

```
Agent(subagent_type="visual-inspector-agent", prompt="""
## Lane: ui
## Run ID: <run_id>
## Queue: <queues.ui>
## Screenshots: test-evidence/<run_id>/screenshots/
## Mode: <verify | update-baselines>
## Baselines: <path from test-pipeline.yml>

Read screenshots from Wave 1 for the UI test subset. Dual-signal verdict
per spec §3.2 (ARIA snapshot + screenshot AI diff). If mode=update-baselines,
overwrite baselines without comparison. Return lane contract with
{verdict_per_test: {...}, expected_changes: [...], first_run_artifacts: [...]}.
""")
```

If `--update-baselines` is set, the entire STEP is a baseline-write-only
operation; STEPS 6 and 7 are unconditionally skipped after this step.

After contract returns:

1. Read `test-results/ui.json` and update state.
2. Increment `dispatches_used`.
3. If any `expected_changes` or `first_run_artifacts`, hold them for STEP 9.

---

## STEP 5: JOIN + Per-Test Report

1. **Compute per-test verdict.** For each test `t` in `tracks_required_per_test`:
   `verdict(t) = AND(result(t) for each track in tracks_required[t])`.
   A test required in functional AND ui must pass BOTH to be green.
2. **Write `test-results/per-test-report.md`** with one section per failing test:
   test id, lanes that ran, per-lane verdict, screenshot paths.
3. **Write `test-results/pipeline-verdict.json`** skeleton:
   ```json
   { "schema_version": "2.0.0", "run_id": "<id>", "result": "PENDING",
     "lanes": { ... }, "failures": [...], "triage": null, "commit": null }
   ```
4. Update state: `step_status.JOIN = done`. Compute `failures[]` list.
5. If `failures[]` is empty AND `--update-baselines` is NOT set:
   jump to STEP 8 (or STEP 9 if `--full-suite-before-success` is off).
6. If `--skip-fix` is set: jump to STEP 9 (report only, no triage).
7. If `--update-baselines` is set: jump to STEP 9 (baseline-update complete).
8. Otherwise: proceed to STEP 6 triage.

---

## STEP 6: TRIAGE (Inline at T0)

Triage fans out three worker waves. All dispatches originate at T0; workers
never chain-dispatch. Each fan-out chunk is **one T0 assistant message with
up-to-N parallel `Agent()` calls** (N = `concurrency.max_concurrent_*` for
that wave).

### Budget guard (REQ-M015, v2 §3.3 end)

Before every chunk dispatch:

```
if state.dispatches_used >= config.budgets.max_total_dispatches:
    emit BLOCKED verdict "BUDGET_EXHAUSTED_DISPATCHES", go to STEP 9
if wall_clock_elapsed_minutes(state) >= config.budgets.max_wall_clock_minutes:
    emit BLOCKED verdict "BUDGET_EXHAUSTED_WALL_CLOCK", go to STEP 9
```

Track `wall_clock_elapsed_minutes` as `(now - state.wall_clock_started_at).total_seconds() / 60`.

### Fan-out 1: Analyzers

Chunk the failure list into groups of `max_concurrent_analyzers` (default 5).
Per chunk, one T0 message with up-to-5 calls:

```
Agent(subagent_type="test-failure-analyzer-agent", prompt="""
## Failure: <failure_id>
## Test log: <path>
## Screenshot: <path or null>
## Config: .claude/config/test-pipeline.yml

Classify the failure by category (SELECTOR, TIMEOUT, ASSERTION_FAILURE, ...).
Return: {"gate": "PASSED", "category": "<cat>", "confidence": "<HIGH|MEDIUM|LOW>",
         "recommended_action": "<AUTO_HEAL|ISSUE_ONLY|ESCALATE>", "fix_hints": [...]}
""")
```
*(... repeat up to 5 ...)*

Wait for all chunk contracts. Aggregate into `state.triage.analyses[]`.
Increment `dispatches_used` by chunk size.

### Fan-out 2: Issue managers

Only for failures with `recommended_action: ISSUE_ONLY` or `AUTO_HEAL`.
Chunks of `max_concurrent_issue_managers`. Per chunk, one T0 message:

```
Agent(subagent_type="github-issue-manager-agent", prompt="""
## Failure: <failure_id>
## Analysis: <analyzer contract>
## Dedup signature: <computed from failure>

Create or dedup an Issue via `gh`. Hard-fail with "GITHUB_NOT_CONNECTED" if
gh is not authenticated or the repo has no origin — per REQ-M015 and
partial_failure_policy: abort_on_first_blocked (v1 §3.7.1).
Return: {"gate": "PASSED|FAILED", "issue_number": <n>, "deduped_from": <n|null>}
""")
```

**Abort-on-first-blocked:** if ANY issue-manager returns `GITHUB_NOT_CONNECTED`,
abort triage immediately with BLOCKED verdict, skip Fan-out 3, go to STEP 9.

### Fan-out 3: Fixers

Only for `recommended_action: AUTO_HEAL`. Chunks of `max_concurrent_fixers`.
Each chunk dispatches stack-specific fixer agents (detected from the project
stack: `fastapi-fixer-agent`, `android-fixer-agent`, `react-fixer-agent`, etc.
— the analyzer's `fix_hints` names the fixer).

Per chunk, one T0 message with up-to-5 calls; each returns a unified diff.
Workers MUST NOT apply diffs directly — they return diff text for T0 to apply.

### Apply fixes

If `--fix-pr-mode` is set:

```
Skill("/pipeline-fix-pr", args="<collected diffs>, <issue numbers>, <run_id>")
```

Otherwise:

```
Skill("/serialize-fixes", args="<collected diffs>, <run_id>")
```

### Escalate on budget exhaustion

If any `state.global_retries_remaining <= 0` OR budget guards tripped:

```
Skill("/escalation-report", args="<run_id>, <unresolved failures>")
```

Update state: `step_status.TRIAGE = done`. Record `triage.analyses`,
`triage.issues`, `triage.fixes_applied` in `pipeline-verdict.json`.

---

## STEP 7: VERIFY-AFFECTED

If no fixes applied in STEP 6, skip to STEP 8. Otherwise:

1. **Derive affected test subset.** Union of tests touched by applied fixes
   (from diff file paths + import graph). Keep the subset small — ideally
   only the originally-failing tests plus their direct importers.
2. **Re-dispatch Wave 1 + Wave 2 for the subset.** Same `Agent()` call
   shape as STEPS 3–4, but with `queues.*` narrowed to the affected subset.
3. **Loop.** Up to `global_retries_remaining` retries per failure. Decrement
   `global_retries_remaining` per retry.
4. **Termination:**
   - All affected tests green → proceed to STEP 8
   - Budget exhausted → BLOCKED, go to STEP 9 with reason `VERIFY_BUDGET_EXHAUSTED`
   - Specific test flaps (passes/fails alternately) 3+ times → mark as `flaky_detected: true`
     in the failure entry; treat as FAILED for verdict (per `testing.md` "FLAKY
     tests are reported as FAILED with flaky_detected: true").

---

## STEP 8: FINAL FULL-SUITE PASS

Run only when `--full-suite-before-success` is set OR configured. One more
Wave 1 + Wave 2 over the complete suite to catch collateral regressions
from applied fixes (REQ-S006 equivalent).

Same dispatch pattern as STEPS 3–4. If final full-suite is green, proceed;
if it regresses, re-enter STEP 6 triage for the new failures (subject to
remaining budget).

Skip entirely if `--update-baselines` or `--skip-fix` mode.

---

## STEP 9: COMMIT + REPORT

1. **Invoke post-fix skill:**
   ```
   Skill("/post-fix-pipeline", args="<run_id>, <pipeline-verdict.json path>")
   ```
   This skill handles final documentation updates, commit message, and git
   commit (unless `--fix-pr-mode` already opened a PR in STEP 6).
2. **Finalize `pipeline-verdict.json`:** set `result` to `PASSED | FAILED | BLOCKED`;
   fill `triage`, `commit`, `artifacts`.
3. **Print user-facing dashboard:**
   ```
   ============================================================
   Test Pipeline: <PASSED | FAILED | BLOCKED>
     Run ID: <run_id>
     Mode: <Full | Verify | BaselineUpdate>
     Wave topology: <parallel | serial>
     Tests: <total> | <passed> | <failed> | <flaky>
     Budget: <dispatches_used>/<max> dispatches, <minutes>/<max> min
     Evidence: test-evidence/<run_id>/
     Verdict: test-results/pipeline-verdict.json
   ============================================================
   ```
4. **If BLOCKED:** print the blocker reason prominently + path to
   `test-results/escalation-report.md` if produced.
5. **Handoff suggestions** (only if PASSED):
   - `Next: push branch and open PR` (if commit was made)
   - `Next: run /review-gate before PR` (if team gates enabled)

---

## Budget semantics quick reference

| Budget | Default | Owner | Enforced at |
|--------|---------|-------|-------------|
| `max_total_dispatches` | 100 | T0 (this skill) | Before every fan-out chunk (STEP 6) and every verify-affected iteration (STEP 7) |
| `max_wall_clock_minutes` | 90 | T0 | Same as above |
| `global_retries_remaining` | 15 | T0 | Decremented per verify-affected retry |
| `max_concurrent_analyzers` | 5 | T0 | STEP 6 Fan-out 1 chunk size |
| `max_concurrent_issue_managers` | 5 | T0 | STEP 6 Fan-out 2 chunk size |
| `max_concurrent_fixers` | 5 | T0 | STEP 6 Fan-out 3 chunk size |

Exit code semantics: T0 is the user's interactive session — there is no
process exit code. The `result` field in `pipeline-verdict.json` IS the
signal; downstream aggregators read this exact field name (see `testing.md`
Structured Test Output).

---

## CRITICAL RULES

- MUST run at T0 — this skill's body is injected into the user's session; it
  MUST NOT be invoked by another agent via `Agent()`. If dispatched as a
  worker, `Agent` is stripped at runtime and every `Agent()` call below
  becomes silent inline work (the exact failure mode of v1's nested dispatch).
- MUST emit all parallel `Agent()` calls within a single T0 assistant message.
  Splitting them across messages serializes the dispatch — `Agent()` parallelism
  is per-message, not per-session.
- MUST NOT dispatch `testing-pipeline-master-agent`, `test-pipeline-agent`,
  or `failure-triage-agent` — all three are deprecated (2026-04-24). Their
  orchestration is now inline in this body.
- MUST update `.workflows/testing-pipeline/state.json` and `events.jsonl`
  after every step transition — this is the ONLY canonical state file;
  workers read paths from their dispatch context, never read the state file.
- MUST enforce the budget guard before every chunk dispatch (STEP 6 Fan-outs
  and STEP 7 retries). BLOCKED verdict on exhaustion, not silent overage.
- MUST treat the first `GITHUB_NOT_CONNECTED` from any issue-manager as a
  triage-wide abort (partial_failure_policy: abort_on_first_blocked).
- MUST set `flaky_detected: true` on a failing test that passes and fails
  across retries — do NOT report as PASSED even if a later retry passed.
- MUST NOT modify baselines outside `--update-baselines` mode. The visual
  inspector compares; it does not overwrite, unless the mode flag says so.
- MUST NOT proceed past STEP 5 if `--update-baselines` is set — STEPS 6 and 7
  are unconditionally skipped in baseline-update mode per REQ-S002.
