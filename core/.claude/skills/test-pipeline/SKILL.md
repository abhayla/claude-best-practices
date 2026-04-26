---
name: test-pipeline
description: >
  Run your full test suite end-to-end: find broken tests, diagnose root causes,
  open GitHub issues, apply targeted auto-fixes, re-verify, and commit. The
  three-lane pipeline runs functional + API + UI tests with dual-signal visual
  verification, then fans out failure triage (analyze → file issues → fix →
  serialize). Use when you want the complete test→fix→verify→commit chain.
  For verification without fixes, use /auto-verify. For a single fix iteration,
  use /fix-loop. For unclear root cause, use /systematic-debugging. For the
  bug-resolution full cycle with mandatory learning capture, use /debugging-loop.
  Under the hood: this skill's body runs at T0 as a skill-at-T0 orchestrator
  (spec v2.2) and dispatches flat worker subagents via Agent() at T0 —
  required because Anthropic's platform does not forward Agent to dispatched
  subagents.
type: workflow
allowed-tools: "Agent Bash Read Write Edit Grep Glob Skill"
argument-hint: "[failure_output] [--capture-proof | --no-capture-proof] [--skip-fix] [--allow-gaps] [--only-issues N,M] [--fix-pr-mode] [--full-suite-before-success] [--update-baselines]"
triggers:
  - test pipeline
  - fix verify commit
  - verify and commit
  - full test pipeline
  - test verification pipeline
  - run test pipeline
  - run my tests
  - run all tests end to end
  - run the test suite
  - fix failing tests
  - fix broken tests
  - fix the tests
  - test and fix
  - test everything
  - verify my changes
  - verify the fix
  - verify and ship
  - debug test failures
  - find broken tests
  - check if tests pass
  - make the tests pass
  - test fix commit cycle
version: "3.0.0"
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
               [--allow-gaps]
               [--only-issues N,M]
               [--fix-pr-mode]
               [--full-suite-before-success]
               [--update-baselines]
```

| Flag | Default | Meaning |
|------|---------|---------|
| `failure_output` | — | Test failure text to feed into triage (enters Fix mode directly) |
| `--capture-proof` / `--no-capture-proof` | on (config) | Capture screenshots on every test for visual review |
| `--skip-fix` | off | Skip STEPS 6–8 (triage + fixers + final-suite); STEPS 1–5 + 9 still run |
| `--allow-gaps` | off | Treat `PASSED_WITH_GAPS` (some manifest tests not executed) as `ci_gate: PASSED` instead of `FAILED`. Strict default per v3.0.0 contract — only set when subsetting is intentional (e.g., user-explicit filter, sharded CI) |
| `--only-issues N,M` | — | Restrict triage to listed GitHub Issue numbers |
| `--fix-pr-mode` | off | Open fixes as a single PR (via `/pipeline-fix-pr`) instead of N serial commits |
| `--full-suite-before-success` | off | Force STEP 8 final full-suite pass before commit |
| `--update-baselines` | off | Visual baselines regenerate mode — STEPS 6–7 skip, STEP 4 writes baselines instead of comparing (REQ-S002) |

Mutually exclusive: `--skip-fix` and `--update-baselines` MUST NOT both be set.

---

## STEP 1: INIT

1. **Validate args + resolve mode.** Parse `$ARGUMENTS`. Mutually-exclusive
   flag combos MUST be rejected with an actionable error before any state is
   touched:
   - `--skip-fix` + `--update-baselines` → BLOCKED with `blocker: INVALID_FLAG_COMBO`
   - `--fix-pr-mode` + `--update-baselines` → BLOCKED (baselines mode skips triage)
   If valid: `failure_output` non-empty OR `--skip-fix` absent → Full mode
   (all 9 steps). `--skip-fix` set → Verify mode (skip to STEP 5).
   `--update-baselines` set → Baseline-update mode (skip STEPS 6–7).
1a. **Cutover guard: PIPELINE_IN_PROGRESS.** Check
    `.workflows/testing-pipeline/.lock`. If file exists AND its timestamp is
    less than `budget.max_wall_clock_minutes` old → another pipeline is
    in flight. Refuse to proceed unless `--force` was passed. Write BLOCKED
    verdict `{"blocker": "PIPELINE_IN_PROGRESS", "existing_run_id": "<from lock>",
    "remediation": "wait for existing run OR pass --force to override"}` and
    exit. If lock is older than the budget window (stale crash recovery) or
    `--force` set → proceed. Always write a fresh lock file containing
    `{"pid": <current>, "run_id": "<new>", "started_at": "<iso>"}` at this point.
2. **Read config.** `Read .claude/config/test-pipeline.yml`. If the file does
    not exist at all → BLOCKED with `{"blocker": "CONFIG_MISSING",
    "expected_path": ".claude/config/test-pipeline.yml",
    "remediation": "Run /update-practices to sync the hub config template,
    or copy core/.claude/config/test-pipeline.yml from the hub"}`.
    Required keys (schema 2.0.0): `capture_proof.enabled`,
    `lanes.ui.use_checkpoint`, `lanes.parallel_classifier.enabled`,
    `lanes.parallel_classifier.min_test_count`,
    `budget.max_total_dispatches` (default 100),
    `budget.max_wall_clock_minutes` (default 90),
    `retry.global_budget` (default 15),
    `concurrency.max_concurrent_analyzers` (default 5),
    `concurrency.max_concurrent_issue_managers` (default 5),
    `concurrency.max_concurrent_fixers` (default 5), `auto_heal.*`.
2a. **Config schema gate.** If `schema_version != "2.0.0"` OR any of
    `lanes.parallel_classifier`, `budget.max_total_dispatches`,
    `budget.max_wall_clock_minutes`, `retry.global_budget` is missing →
    fail-fast: write BLOCKED verdict `{"result": "BLOCKED", "blocker":
    "CONFIG_SCHEMA_INCOMPATIBLE", "observed_schema": <or null>,
    "missing_keys": [...], "remediation": "Run /update-practices"}` to
    `test-results/pipeline-verdict.json`, emit event, print remediation,
    exit. Prevents silent key-shape mismatches (the 2026-04-24 downstream
    gap).
2b. **Worker registry probe (WORKER_REGISTRY_PROBE).** Before any heavy
    work, probe the runtime registry for each worker the pipeline will
    dispatch in STEPs 2–6. Claude Code pins its agent registry at session
    start; file existence on disk does NOT equal runtime dispatchability.
    The worker list is derived (NOT hardcoded) from config + flags, so
    this gate is generic across stacks:
    - Always probe: `test-scout-agent`, `tester-agent`
    - If `lanes.api.enabled` AND project has FastAPI markers (Bash detect
      `pyproject.toml` containing `fastapi`): probe `fastapi-api-tester-agent`.
      Otherwise the api lane reuses `tester-agent` and no extra probe.
    - If `lanes.ui.enabled`: probe `visual-inspector-agent`
    - If `--skip-fix` is NOT set (triage path active): probe
      `test-failure-analyzer-agent`, `github-issue-manager-agent`,
      and any project-specific fixer matching `<stack>-fixer-agent` if
      detectable from config

    For each probed worker emit one minimal dispatch:
    ```
    Agent(subagent_type="<name>", description="probe",
          prompt="probe — return {ack: true} immediately")
    ```
    These count toward `dispatches_used`.

    If ANY probe returns "Agent type not found" / "unknown subagent_type"
    / similar runtime registry-miss → fail-fast: write BLOCKED verdict
    `{"result": "BLOCKED", "blocker": "WORKER_REGISTRY_NOT_LOADED",
    "missing_agents": [<list>], "agents_on_disk": <count of matching
    .claude/agents/*.md files that exist>, "remediation": "Newly synced
    agents require Claude Code session restart. Exit this session
    (Ctrl+D or /exit), run claude again from the project root, then
    re-run /test-pipeline. The agent .md files are on disk but Claude
    Code's runtime registry was loaded at session start and does not
    pick them up live."}` to `test-results/pipeline-verdict.json`, emit
    `WORKER_REGISTRY_PROBE_FAILED` event with the missing list, print
    remediation banner prominently, release the lock file (per STEP 9
    sub-step 2a), exit.

    Cache successful probe results in state.json under
    `registry_probe: {"ts": "<iso>", "verified": [<agent names>]}` so a
    resume of the same `run_id` within the same session skips re-probing
    on retry. `--force` invalidates the cache.
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

Walk every test file in the project. For each individual test (file::name)
in the project, classify the lanes it belongs to (functional, api, ui).

**v3.0.0 — emit a manifest.** Write `test-results/manifest.json` per the
schema below. The manifest is the SINGLE SOURCE OF TRUTH for "what should
run" — every downstream lane verdict and the JOIN reconciliation step
read from this file.

Manifest schema:
{
  "schema_version": "3.0.0",
  "run_id": "<run_id>",
  "scout_completed_at": "<iso>",
  "tests": [
    {
      "test_id": "<file>::<name>",
      "test_file": "<relative path>",
      "test_name": "<test name>",
      "lanes_required": ["functional"|"api"|"ui", ...],
      "framework": "playwright|vitest|jest|pytest|...",
      "classification_signals": ["imports:<lib>", "path:<dir>", ...],
      "estimated_duration_ms": <int|null>
    }
  ],
  "queue_counts_by_lane": {"functional": <n>, "api": <n>, "ui": <n>},
  "overlap": {"functional_and_ui": <n>, "functional_and_api": <n>, "all_three": <n>}
}

Each unique test appears ONCE in `tests[]` regardless of lanes_required
length. `queue_counts_by_lane` sums tests where lane is in lanes_required.

Also populate `queues` + `tracks_required_per_test` in state.json (legacy
fields kept for STEP 7 verify-affected logic). For queues > 1000 entries,
emit a sidecar at .workflows/testing-pipeline/queue-{lane}.jsonl.

Return a contract: {
  "gate": "PASSED|FAILED",
  "test_count": <int — unique test_ids in manifest>,
  "queues": { "functional": <count>, "api": <count>, "ui": <count> },
  "manifest_path": "test-results/manifest.json",
  "sidecars": [<paths>],
  "summary": "<one line>"
}
""")
```

After the contract returns:

1. Merge the returned counts into `state.json`.
2. Increment `dispatches_used` by 1.
3. **Verify manifest exists.** If `test-results/manifest.json` is missing or
   malformed → BLOCKED with `{"blocker": "MANIFEST_MISSING_OR_MALFORMED",
   "remediation": "scout failed to emit a valid manifest — re-run /test-pipeline"}`.
4. If `gate: FAILED`, abort pipeline with `BLOCKED` verdict; skip to STEP 9 with
   failure reason `SCOUT_FAILED`.
5. **Empty-suite early exit:** If `test_count == 0` (all queues empty) →
   write `pipeline-verdict.json` with `{"result": "PASSED",
   "reason": "NO_TESTS_IN_SUITE", "test_count": 0}`, emit PIPELINE_DONE event,
   release the lock file, and exit cleanly. No Wave 1, Wave 2, or triage
   fires. (A project with zero tests trivially passes the pipeline.)
6. Decide Wave 1 topology using the classifier flag:
   - If `lanes.parallel_classifier.enabled: true` AND
     `test_count >= lanes.parallel_classifier.min_test_count`: **parallel Wave 1**.
   - Otherwise: **serial Wave 1** (functional fully, then api).

Record `wave1_topology` in `state.json` for resume/debug.

**Stack runner resolution (for STEP 3 Wave 1 functional lane).** Scout reports
the detected stack. If absent, the orchestrator falls back in this order:
`pyproject.toml` → `package.json` → `go.mod` → `Cargo.toml` → `Gemfile` →
`pom.xml`/`build.gradle`. Maps to stack-runner skill:
`pytest` → `/pytest-dev` OR `/fastapi-run-backend-tests`; `jest` →
`/jest-dev`; `vitest` → `/vitest-dev`; etc. If NONE detected → BLOCKED
with `{"blocker": "UNKNOWN_STACK", "checked_markers": [...],
"remediation": "Add a stack-marker file (pyproject.toml, package.json, etc.)
or override by setting stack=<runner> in test-pipeline.yml"}`.

---

## STEP 3: WAVE 1 — Functional + API + UI (parallel runners)

**v3.0.0 architecture change (M2):** UI is now an independent Wave 1 runner
with its own dedicated `tester-agent` dispatch (`lane=ui`). UI tests RUN in
Wave 1 and produce screenshots. STEP 4 (formerly the UI lane runner) is now
exclusively a screenshot verification stage that operates on Wave 1's UI
lane outputs.

**Lane skip rule (REQ-M001 / v1 §3.3 NN-4):** If a lane's queue is empty,
record a synthetic `SKIP` result in `test-results/{lane}.json` with
`{"result": "SKIP", "reason": "EMPTY_QUEUE"}` and do NOT dispatch. This
is checked per-lane BEFORE any dispatch.

### Parallel topology (default for >= min_test_count tests)

Emit all 3 lane `Agent()` calls in **one T0 assistant message** (this is
how parallel dispatch actually works — see agent-orchestration.md §2):

```
Agent(subagent_type="tester-agent", prompt="""
## Lane: functional
## Capture proof: <bool>
## Run ID: <run_id>
## Manifest: test-results/manifest.json
## Queue: <queues.functional or sidecar path>
## Output: test-results/functional.json + functional.jsonl
## Screenshots: test-evidence/<run_id>/screenshots/
## Stack runner: <detected — pytest-dev | jest-dev | vitest-dev | fastapi-run-backend-tests | etc.>

You MUST execute EVERY test in the queue. Subsetting under wall-clock or
any other pressure is FORBIDDEN — if you cannot complete the queue,
return gate=FAILED with blocker=INCOMPLETE_QUEUE_EXECUTION and an
explicit `unrun: [test_ids]` list. The orchestrator's JOIN reconciles
your `executed[]` against the manifest and treats unexercised tests as
verdict gaps.

Return v3.0.0 lane contract: {
  "gate": "PASSED|FAILED",
  "lane": "functional",
  "manifest_total": <int — count of manifest tests where lanes_required includes functional>,
  "executed_count": <int — len of executed[]>,
  "executed": [<test_ids actually run>],
  "unexercised": [<test_ids in manifest you did NOT run>],
  "passed": <int>,
  "failed": <int>,
  "skipped_by_test": <int — test.skip() invocations the runner saw>,
  "summary": "<line>",
  "artifacts": {...},
  "failures": [...]
}
""")

Agent(subagent_type="fastapi-api-tester-agent", prompt="""
## Lane: api
## Run ID: <run_id>
## Manifest: test-results/manifest.json
## Queue: <queues.api>
## Output: test-results/api.json + api.jsonl

Run EVERY API test in the queue. Same v3.0.0 contract as functional —
`executed[]` + `unexercised[]` + manifest reconciliation fields are
mandatory. If contract files are present, invoke
Skill(\"/contract-test\", ...). Combined verdict per spec §3.2.
""")

Agent(subagent_type="tester-agent", prompt="""
## Lane: ui
## Capture proof: true (mandatory for ui lane)
## Run ID: <run_id>
## Manifest: test-results/manifest.json
## Queue: <queues.ui>
## Output: test-results/ui.json + ui.jsonl
## Screenshots: test-evidence/<run_id>/screenshots/

Run EVERY UI test in the queue with capture-proof MANDATORY. Each test
MUST produce a `.png` screenshot AND a `.aria.yaml` (Playwright only).
The screenshot capture is the test verdict per testing.md UI authority
rule. Same v3.0.0 contract — `executed[]` + `unexercised[]` mandatory.

Note: tests classified as both `functional` AND `ui` (overlap, see
manifest.overlap.functional_and_ui) run independently in BOTH lanes per
v3.0.0 M2 architecture. This is intentional — functional verdict checks
exit codes; UI verdict checks visual rendering. Same test, two verdicts.
""")
```

For non-FastAPI projects, the api-lane owner is `tester-agent` + stack-
appropriate runner skill (`/contract-test` + `/integration-test`) — same
v3.0.0 contract.

### Serial topology (for small suites or classifier disabled)

Dispatch functional first; wait for contract; then dispatch api; then ui.
Same prompts.

### After all lane contracts return

1. Read `test-results/functional.json`, `api.json`, and `ui.json`.
2. **Per-lane manifest-completeness gate (replaces v2 contract completeness check).**
   For each lane that ran, assert `lane.executed_count + len(lane.unexercised)
   == lane.manifest_total`. If a worker returned numbers that don't
   add up, transition `step_status.WAVE1 = failed` with reason
   `LANE_VERDICT_ARITHMETIC_INVALID` and abort to STEP 9.
3. Merge lane gates into `state.json` → `step_status.WAVE1 = done`. Lanes
   with non-empty `unexercised[]` are NOT failed at WAVE1; they propagate
   to STEP 5 JOIN reconciliation which decides the final verdict.
4. Increment `dispatches_used` by the number of `Agent()` calls issued.
5. **Emit granular events** — `WAVE1_DISPATCH_FUNCTIONAL`,
   `WAVE1_DISPATCH_API`, `WAVE1_DISPATCH_UI` at dispatch time (not just
   `WAVE1_DONE` at return). Dispatch-start events capture
   `dispatched_at: <iso>` so timeouts and stalls are observable from
   events.jsonl alone.

---

## STEP 4: WAVE 2 — UI Visual Verification

**v3.0.0 architecture change (M2):** Wave 2 is now exclusively visual
verification of Wave 1 UI-lane screenshots. The UI tests themselves RAN in
Wave 1 (STEP 3, lane=ui dispatch). Wave 2 reads the screenshots that
Wave 1's ui lane produced and applies the dual-signal verdict matrix.

**Skip rule:** If Wave 1 ui lane was SKIP (empty queue) or BLOCKED (no
screenshots produced), STEP 4 records `test-results/ui-verification.json`
with `{"result": "SKIP", "reason": "NO_UI_LANE_SCREENSHOTS"}` and proceeds
to STEP 5. The JOIN reconciliation will already have flagged the underlying
gap from manifest reconciliation — STEP 4 SKIP is informational only.

**Single-signal confidence cap.** When screenshots are present but ARIA
snapshots are absent (or vice-versa), `visual-inspector-agent` caps its
per-test verdict confidence at MEDIUM per its NON-NEGOTIABLE #3
("single-signal cap"). For HIGH confidence, tester-agent must have captured
BOTH `.png` and `.aria.yaml` (Playwright only — see tester-agent.md
Evidence Capture step). Non-Playwright UI frameworks cap at MEDIUM by design.

### Dispatch

```
Agent(subagent_type="visual-inspector-agent", prompt="""
## Lane: ui-verification
## Run ID: <run_id>
## Source lane output: test-results/ui.json + ui.jsonl (from Wave 1 ui lane)
## Screenshots: test-evidence/<run_id>/screenshots/
## Mode: <verify | update-baselines>
## Baselines: <path from test-pipeline.yml>

Read the ui lane's executed[] from test-results/ui.json. For each test_id
that produced a screenshot, apply dual-signal verdict (ARIA + screenshot
AI diff) per spec §3.2. If mode=update-baselines, overwrite baselines
without comparison.

Return verification contract:
{
  "gate": "PASSED|FAILED",
  "verified_count": <int>,
  "verdict_per_test": {<test_id>: {"verdict": "PASS|FAIL", "confidence": "..."}},
  "expected_changes": [...],
  "first_run_artifacts": [...]
}

Note: this verification lane does NOT report `executed[]`/`unexercised[]`
fields — that contract belongs to Wave 1 lanes which actually run tests.
Verification operates only on screenshots Wave 1 ui lane produced.
""")
```

If `--update-baselines` is set, the entire STEP is a baseline-write-only
operation; STEPS 6 and 7 are unconditionally skipped after this step.

After contract returns:

1. Read `test-results/ui-verification.json` and update state.
2. Increment `dispatches_used`.
3. If any `expected_changes` or `first_run_artifacts`, hold them for STEP 9.

---

## STEP 5: JOIN + Manifest Reconciliation + Per-Test Report

**v3.0.0 — strict execution contract reconciliation.** JOIN owns the
authoritative pass/fail decision by comparing the SCOUT manifest against
each lane's `executed[]` and the per-lane JSONL streams.

### 1. Reconciliation algorithm

Read `test-results/manifest.json` and every `test-results/{lane}.json`
plus `test-results/{lane}.jsonl`. Compute:

```
manifest_test_ids        = {t.test_id for t in manifest.tests}
manifest_total_unique    = len(manifest_test_ids)

per_lane = {}
for lane in ("functional", "api", "ui"):
    expected_in_lane     = {t.test_id for t in manifest.tests if lane in t.lanes_required}
    executed_in_lane     = set(verdict[lane].executed)
    jsonl_test_ids       = {row.test_id for row in lane.jsonl}
    unexercised_in_lane  = expected_in_lane - executed_in_lane

    # Ledger consistency: lane verdict's executed[] MUST equal lane's JSONL contents
    if executed_in_lane != jsonl_test_ids:
        emit LANE_LEDGER_MISMATCH event with the diff
        treat lane as gate=FAILED with blocker=LANE_LEDGER_MISMATCH

    per_lane[lane] = {
        "manifest": len(expected_in_lane),
        "executed": len(executed_in_lane),
        "unexercised": len(unexercised_in_lane),
        "unexercised_test_ids": sorted(unexercised_in_lane),
    }

# Cross-lane: a test_id is "exercised" if at least one of its required lanes ran it
all_executed = union of executed_in_lane for every lane
unexercised_total = manifest_test_ids - all_executed
```

### 2. Determine `result`

```
if any lane.gate == FAILED with blocker in {SCOUT_FAILED, LANE_LEDGER_MISMATCH,
   LANE_VERDICT_ARITHMETIC_INVALID, MANIFEST_MISSING_OR_MALFORMED}:
    result = BLOCKED
elif any test failed in any lane (executed but result=fail):
    result = FAILED
elif unexercised_total > 0:
    result = PASSED_WITH_GAPS
else:
    result = PASSED
```

### 3. Determine `ci_gate` (Q5 strict default — breaking change)

```
if result == PASSED:
    ci_gate = PASSED
elif result == PASSED_WITH_GAPS:
    ci_gate = PASSED if --allow-gaps else FAILED
elif result in (FAILED, BLOCKED):
    ci_gate = FAILED
```

### 4. Write `test-results/pipeline-verdict.json` (v3.0.0 schema)

```json
{
  "schema_version": "3.0.0",
  "run_id": "<id>",
  "result": "PASSED|PASSED_WITH_GAPS|FAILED|BLOCKED",
  "ci_gate": "PASSED|FAILED",
  "result_reasons": ["LANE_INCOMPLETE_EXECUTION:functional", ...],
  "manifest_total_unique_tests": <int>,
  "executed_unique_tests": <int>,
  "unexercised_total": <int>,
  "lane_summaries": {
    "functional": {"manifest": N, "executed": M, "unexercised": K},
    "api":        {"manifest": N, "executed": M, "unexercised": K},
    "ui":         {"manifest": N, "executed": M, "unexercised": K}
  },
  "strict_mode": true,
  "allow_gaps": <bool>,
  "failures": [...],
  "triage": null,
  "commit": null
}
```

### 5. Per-test report

Write `test-results/per-test-report.md` with sections for:
- Failing tests (test_id, lanes that ran, per-lane verdict, screenshot paths)
- Unexercised tests (test_id, lanes_required, why-not-run if known)
- Lane-level summaries

### 6. Routing

1. Update state: `step_status.JOIN = done`. Compute `failures[]` list.
2. If `result == BLOCKED`: jump to STEP 9 immediately (no triage useful).
3. If `result == PASSED` AND `--update-baselines` is NOT set:
   jump to STEP 8 (or STEP 9 if `--full-suite-before-success` is off).
4. If `result == PASSED_WITH_GAPS`: emit `JOIN_PASSED_WITH_GAPS` event.
   Behavior depends on flags:
   - `--allow-gaps` set → treat as PASSED for routing (jump to STEP 8/9)
   - default (strict) → fall through to triage path; gaps become FAILED
5. If `--skip-fix` is set: jump to STEP 9 (report only, no triage).
6. If `--update-baselines` is set: jump to STEP 9 (baseline-update complete).
7. Otherwise (FAILED OR strict-mode PASSED_WITH_GAPS): proceed to STEP 6 triage.

---

## STEP 6: TRIAGE (Inline at T0)

Triage fans out three worker waves. All dispatches originate at T0; workers
never chain-dispatch. Each fan-out chunk is **one T0 assistant message with
up-to-N parallel `Agent()` calls** (N = `concurrency.max_concurrent_*` for
that wave).

### Budget guard (REQ-M015, v2 §3.3 end)

Before every chunk dispatch — **pre-check accounts for the chunk-add**, not
just the current used-count:

```
chunk_size = min(failures_remaining, config.concurrency.max_concurrent_<wave>)
if state.dispatches_used + chunk_size > config.budget.max_total_dispatches:
    emit BLOCKED verdict "BUDGET_EXHAUSTED_DISPATCHES" with
      {"would_use": state.dispatches_used + chunk_size, "cap": max},
    go to STEP 9
if wall_clock_elapsed_minutes(state) >= config.budget.max_wall_clock_minutes:
    emit BLOCKED verdict "BUDGET_EXHAUSTED_WALL_CLOCK", go to STEP 9
```

Track `wall_clock_elapsed_minutes` as `(now - state.wall_clock_started_at).total_seconds() / 60`.

Emit granular events: `TRIAGE_ANALYZER_CHUNK_<i>_DISPATCH`,
`TRIAGE_ANALYZER_CHUNK_<i>_DONE` (same shape for issue-manager and fixer
fan-outs). This lets events.jsonl reconstruct the dispatch timeline without
reading state.json. Also emit `TRIAGE_BUDGET_CHECK` events at each guard
evaluation, with `{used: N, would_use: M, cap: X, verdict: PROCEED|BLOCKED}`.

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

### Recommended-action dispatch matrix

For each analyzed failure, Fan-outs 2+3 are gated by the analyzer's
`recommended_action`. Summary: `AUTO_HEAL` fires both; `ISSUE_ONLY` /
`QUARANTINE` / `ESCALATE` fire issue-manager only; `RETRY_INFRA` fires
neither (re-dispatches in STEP 7).

Full decision table (all 6 action types, edge cases, dispatch rules):
see `references/dispatch-reference.md` § "Recommended-action dispatch matrix".

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

1. **Derive affected test subset (deterministic algorithm).**
   a. Start set = originally-failing test IDs from STEP 5 JOIN's `failures[]`.
   b. For each applied diff file in `test-results/fixes/*.diff`, parse
      changed source paths. For each changed path, add to set:
      - The test file itself if it IS a test (matches
        `tests/**`, `**/*.spec.*`, `**/*.test.*`, `**/test_*.py`, etc.)
      - Test files that import the changed file (via grep — no import graph
        library required; filename-based `grep -rl "from X" tests/` works
        for most stacks)
   c. Cap subset size at `retry.max_verify_affected_tests` (default 25,
      new config key). If the set exceeds the cap → log WARNING event,
      truncate to the N highest-priority originally-failing tests.
   d. Filter subset to tests in `queues.*` — don't re-scout, but validate
      each test_id is still in a queue (handles scout queue invalidation).

2. **Re-dispatch Wave 1 + Wave 2 for the subset.** Same `Agent()` call
   shape as STEPS 3–4, but with `queues.*` narrowed to the affected subset.
   Emit `VERIFY_AFFECTED_ITERATION_<n>_DISPATCH` event per iteration.

3. **Loop.** Up to `retry.global_budget` (default 15) retries per failure;
   decrement `global_retries_remaining` per re-dispatch. Re-dispatch counts
   toward `dispatches_used` (not a separate bucket).

4. **Termination:**
   - All affected tests green → proceed to STEP 8, emit `VERIFY_AFFECTED_DONE`
   - `global_retries_remaining <= 0` → BLOCKED, STEP 9 with reason
     `VERIFY_BUDGET_EXHAUSTED`
   - `dispatches_used + 2 > max_total_dispatches` (can't afford another
     Wave 1+2 iteration) → BLOCKED with `VERIFY_DISPATCH_BUDGET_EXHAUSTED`
   - Specific test flaps 3+ times (passes/fails alternately) → mark
     `flaky_detected: true`; treat as FAILED per testing.md flakiness rule.
     Stop retrying this specific test but continue others.

---

## STEP 8: FINAL FULL-SUITE PASS

Run only when `--full-suite-before-success` is set OR configured. One more
Wave 1 + Wave 2 over the complete suite to catch collateral regressions
from applied fixes (REQ-S006 equivalent).

Same dispatch pattern as STEPS 3–4. Emit `FINAL_FULL_SUITE_DISPATCH` event
at start; count dispatches toward `dispatches_used` (subject to budget guard
pre-check — if we can't afford Wave 1+2, STEP 8 is SKIPPED with reason
`BUDGET_INSUFFICIENT_FOR_FINAL_SUITE`, not BLOCKED, because triage+verify
already succeeded).

**Regression re-entry semantics:** If final full-suite finds failures that
did NOT appear in the earlier Wave 1+2 runs (collateral regressions from
STEP 6 fixes), re-enter STEP 6 triage with:
- Budget counters **NOT reset** — `dispatches_used` and
  `global_retries_remaining` continue from their STEP 7 values
- New failures appended to the working failure set
- `regression_source: STEP_8_FULL_SUITE` field added to each new failure
  entry so analyzers know this is a regression (may inform fix strategy)
- Maximum ONE re-entry pass — if STEP 6+7 after STEP 8 produce yet more
  regressions, emit BLOCKED with reason `RECURRENT_REGRESSION` and escalate
  to user

Skip entirely if `--update-baselines` or `--skip-fix` mode.

---

## STEP 9: COMMIT + REPORT

STEP 9 MUST always complete — even on failure of its own sub-skills — so that
`pipeline-verdict.json` always has a `finalized_at` field and the lock file
is always released. Wrap sub-skill invocations in "try → fall-through" so a
/post-fix-pipeline failure degrades to `result: INCONCLUSIVE` rather than
leaving an incomplete verdict file.

1. **Invoke post-fix skill:**
   ```
   Skill("/post-fix-pipeline", args="<run_id>, <pipeline-verdict.json path>")
   ```
   This skill handles final documentation updates, commit message, and git
   commit (unless `--fix-pr-mode` already opened a PR in STEP 6).

   If `/post-fix-pipeline` ERRORS or returns non-PASSED: capture the error
   message, set `commit.performed = false`, `commit.error = <message>`, and
   CONTINUE to step 2 (do NOT exit without writing the verdict). Set
   `result: INCONCLUSIVE` if no result was previously determined by STEPs 5–8,
   else keep the earlier-determined result.

2. **Finalize `pipeline-verdict.json`** (MUST happen even if step 1 errored):
   set `result` to `PASSED | FAILED | BLOCKED | INCONCLUSIVE`; fill `triage`,
   `commit`, `artifacts`; set `finalized_at` to current ISO timestamp.

2a. **Release the lock file.** Delete `.workflows/testing-pipeline/.lock`
    unconditionally. Emit `LOCK_RELEASED` event. A missing lock at this
    point is not an error (some cleanup paths pre-delete).

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

### Dispatch counter, artifacts, --only-issues, event taxonomy

For the detailed rules on:

- What counts toward `dispatches_used` (and what doesn't, e.g., STEP 8
  screenshot-reuse optimization)
- Forward-slash path convention and filesystem-safe name sanitization
- `run_id` timestamp/sha format + `:` → `-` rule for filenames
- Lock file lifecycle (`LOCK_ACQUIRED`, `LOCK_RELEASED`)
- `--only-issues N,M,P` resolution via `gh issue view`
- Complete events.jsonl taxonomy (dispatch-start + completion + gate +
  failure-signal event names)

See **`references/dispatch-reference.md`** (loaded on-demand).

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
- MUST fail-fast with `CONFIG_SCHEMA_INCOMPATIBLE` BLOCKED verdict at STEP 1
  sub-step 2a if the local `test-pipeline.yml` schema_version is missing or
  not "2.0.0", OR if required v2.2 keys (e.g., `lanes.parallel_classifier`)
  are absent. Silent inlining against mismatched config produces unpredictable
  behavior — the actual 2026-04-24 downstream gap. Remediation: `/update-practices`.
- MUST fail-fast with `CONFIG_MISSING` BLOCKED verdict at STEP 1 step 2 if
  `.claude/config/test-pipeline.yml` does not exist. Remediation pointer
  MUST name `/update-practices` as the fix path.
- MUST fail-fast with `PIPELINE_IN_PROGRESS` BLOCKED verdict at STEP 1
  sub-step 1a if a fresh `.workflows/testing-pipeline/.lock` file exists
  (younger than `budget.max_wall_clock_minutes`). Protects against
  concurrent-run state corruption. `--force` overrides; stale locks
  (older than the budget window) are auto-ignored.
- MUST reject mutually-exclusive flag combos before any state is touched:
  `--skip-fix` + `--update-baselines` and `--fix-pr-mode` + `--update-baselines`
  are invalid. BLOCKED with `INVALID_FLAG_COMBO` + specific flags named.
- MUST verify every lane's v3.0.0 contract arithmetic in STEP 3 Wave 1:
  `executed_count + len(unexercised) == manifest_total` per lane. If a worker
  returned numbers that don't add up, transition to BLOCKED with
  `LANE_VERDICT_ARITHMETIC_INVALID` and abort to STEP 9.
- MUST reconcile every lane's `executed[]` against `manifest.json` in STEP 5
  JOIN (v3.0.0 strict execution contract). Tests in `manifest.tests` whose
  `lanes_required` includes lane L but who are NOT in lane L's `executed[]`
  are recorded as `unexercised` in JOIN's reconciliation. Any non-zero
  `unexercised_total` produces `result: PASSED_WITH_GAPS` (downgraded to
  `ci_gate: FAILED` unless `--allow-gaps` is set). The pre-v3.0.0
  partial-execution gate is replaced by this reconciliation.
- MUST reject manifest-vs-JSONL ledger mismatch as BLOCKED in STEP 5: if
  any lane's `executed[]` set is not equal to the `test_id` set parsed
  from `{lane}.jsonl`, emit `LANE_LEDGER_MISMATCH` and BLOCK the pipeline.
  Lane verdict and per-test JSONL must agree by construction; disagreement
  is a worker bug.
- MUST pre-check budget BEFORE chunk dispatch using `dispatches_used + chunk_size`,
  not just `dispatches_used`. The simple post-check would allow one chunk
  past the cap.
- MUST always write `finalized_at` to pipeline-verdict.json in STEP 9, even
  on `/post-fix-pipeline` error. Incomplete verdict files break downstream
  aggregators and leave users guessing whether the run finished.
- MUST release `.workflows/testing-pipeline/.lock` in STEP 9, even on error.
  A stuck lock blocks every future invocation until manually cleared.
- MUST emit granular dispatch-start events (`*_DISPATCH_*`), not only
  completion events. Stalls between dispatch and return are undiagnosable
  from events.jsonl otherwise.
- MUST fail-fast with `WORKER_REGISTRY_NOT_LOADED` BLOCKED verdict at
  STEP 1 sub-step 2b if any required worker subagent_type returns
  "Agent type not found" at runtime probe. File existence on disk does
  NOT equal runtime dispatchability — Claude Code pins the agent registry
  at session start. Remediation MUST always point at session restart,
  never at re-running /update-practices (which can't fix what the user's
  prior /update-practices just caused).
