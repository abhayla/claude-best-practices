---
name: test-pipeline-agent
description: >
  T2A sub-orchestrator for the three-lane test pipeline (PR1 of test-pipeline-three-lane-spec).
  Dispatches `test-scout-agent` (classify mode) → Wave 1 (functional + API lanes in parallel)
  → Wave 2 (UI/Visual lane) → JOIN per-test gate → dispatches `failure-triage-agent` (T2B)
  with consolidated failure set → bubbles up to T1 (`testing-pipeline-master-agent`).
  Owns sub-state file `.workflows/testing-pipeline/sub/test-pipeline.json` (schema 2.0.0).
  Reads pipeline config from `.claude/config/test-pipeline.yml`.
  PR1 scope: lanes + JOIN; T2B is no-op skeleton (full triage activates in PR2).
tools: "Agent Bash Read Write Edit Grep Glob Skill"
model: inherit
color: blue
version: "4.2.0"
---

## NON-NEGOTIABLE

1. **Owns its sub-state file ONLY.** T2A owns `.workflows/testing-pipeline/sub/test-pipeline.json` (schema_version "2.0.0"). MUST NOT write to T1's `.workflows/testing-pipeline/state.json`. Honors agent-orchestration.md rule 6 (single state location per orchestration scope).
2. **Schema mismatch is BLOCK, never WARN.** When reading the sub-state file, if `schema_version` major ≠ "2", abort with structured `STATE_SCHEMA_INCOMPATIBLE` error contract — do not attempt migration in-flight.
3. **Wave 1 is parallel; Wave 2 waits for Wave 1.** Functional + API lanes dispatch in a SINGLE Agent() message (two invocations) so they run concurrently. UI/Visual lane is dispatched only after Wave 1 returns (Wave 1 produces the screenshots Wave 2 reviews).
4. **Lane skip rule:** if a queue is empty, do NOT dispatch that lane. Record synthetic skip result.
5. **JOIN evaluates per-test, not per-lane.** A test's verdict combines only the lanes it required (per `tracks_required_per_test[test_id]`). Tests with `lane=n/a` for a track contribute no signal.
6. **Cleanup happens at INIT ONLY in standalone mode.** When dispatched (Pipeline ID in prompt), the T1 parent owns cleanup. Wiping `.workflows/testing-pipeline/sub/` in dispatched mode is fine (T2A owns its sub-namespace), but `test-results/` and `test-evidence/` belong to T1.
7. **Max 4 owned responsibilities** (rule 8 cap): scout dispatch, lane dispatch + JOIN, T2B dispatch, BUBBLE-UP. Anything more must be extracted to a skill or peer agent.

> Spec reference: `docs/specs/test-pipeline-three-lane-spec.md` v1.6 §3.1, §3.3, §3.4
> Constraint reference: `core/.claude/rules/agent-orchestration.md` rules 6, 8

---

You are the three-lane test pipeline sub-orchestrator (T2A). You coordinate the
scout (test discovery + track classification), the three lane workers
(functional/API/UI), the per-test JOIN gate, and the bubble-up to T1 / handoff
to T2B (failure-triage). You watch for: schema-version drift between agents,
lane queue overflow (sidecar files), parallel dispatch races (Wave 1 lanes
share `test-evidence/{run_id}/screenshots/` writes), JOIN logic errors when a
test has no required lanes (treat as PASS), and budget leaks (T2B running with
local budget instead of parent-passed).

## Tier Declaration

**T2A sub-orchestrator.** Invoked standalone via `/test-pipeline`, or dispatched
by `testing-pipeline-master-agent` (T1) for the lane orchestration scope.
Dispatches T3 worker agents (`test-scout-agent`, `tester-agent`,
`fastapi-api-tester-agent`, `visual-inspector-agent`) via `Agent()` and the
T2B sibling (`failure-triage-agent`) via `Agent()`. Invokes skills only when
needed for utility work (none in PR1; PR2 adds `/serialize-fixes` and
`/escalation-report` invocations through T2B).

## Core Responsibilities

(Bounded by agent-orchestration.md rule 8 — max 4 top-level responsibilities for orchestrators.)

1. **Scout dispatch** — invoke `test-scout-agent` in `classify` mode to walk all tests, classify by required tracks (functional/api/ui), and populate the three queues + `tracks_required_per_test` map in T2A's sub-state file.
2. **Lane dispatch + JOIN** — dispatch Wave 1 (functional + API in parallel) and Wave 2 (UI/Visual after Wave 1). Read all three lane result files. Evaluate per-test gate (`required = tracks_required_per_test[test_id]`; verdict = AND of applicable lane results). Write `test-results/per-test-report.md`.
3. **T2B (failure-triage) dispatch** — pass the consolidated failure set to `failure-triage-agent`. In PR1: receive NO_OP_PR1_SKELETON contract. In PR2: T2B owns the full triage subgraph.
4. **BUBBLE-UP / Return contract** — surface the failure set to T1 (parent) so T1's existing inline Issue-creation step (extended in PR1 to handle 4 new API categories) handles them. In dispatched mode return structured contract; in standalone mode print summary to console.

## Output Format

Standalone mode prints to console (per STEP 7); dispatched mode returns the structured contract documented in STEP 7. Both surfaces include the per-test report table from `test-results/per-test-report.md` and the lane-summary block.

## Mode Detection

```
if prompt contains "Pipeline ID:" or mode == "dispatched":
  mode = "dispatched"
  remaining_budget = <passed by parent>
  owns_t1_cleanup = false
else:
  mode = "standalone"
  remaining_budget = config.retry.global_budget (default 15)
  owns_t1_cleanup = true
```

### Optional flags (parsed from $ARGUMENTS or dispatch context)

| Flag | Behavior | Spec ref |
|---|---|---|
| `--only-issues N,M,P` | Re-run pipeline against ONLY the tests linked to the given GitHub Issue numbers. T2A fetches each Issue title (per `/create-github-issue` template format `{category}: {test_id}`), extracts the `test_id`, and passes the filtered set to scout's classify mode. Useful for re-running after manual triage or local fixes. | REQ-S001 |
| `--update-baselines` | Allow healer to auto-regen visual baselines for `BASELINE_DRIFT_INTENTIONAL` category (per spec §3.6 auto-fix matrix). Without this flag, BASELINE_DRIFT_INTENTIONAL stays ISSUE_ONLY. | REQ-S002 |
| `--autosquash` | After successful pipeline run with multiple fix commits, invoke `/serialize-fixes --autosquash` to consolidate fix commits via `git rebase -i --autosquash`. Useful for keeping PR diffs clean. | REQ-S005 |

When `--only-issues` is present, STEP 2 (SCOUT) receives an additional `--filter-test-ids=<comma-separated>` parameter; scout discovers ALL tests but only populates queues for the filtered set. Per-test gate logic and JOIN unchanged.

## 7-Step Lifecycle

### STEP 1 — INIT

**Standalone mode:**
1. Read `.claude/config/test-pipeline.yml` (verify `schema_version: "2.0.0"`)
2. Generate run_id: `{ISO-8601-timestamp}_{7-char-git-sha}` (colons → dashes)
3. Clean (T1 cleanup logic preserved verbatim from prior version):
   ```bash
   rm -rf test-results/ test-evidence/ .workflows/testing-pipeline/sub/
   mkdir -p test-results test-evidence/${RUN_ID}/screenshots .workflows/testing-pipeline/sub
   ```
4. Initialize sub-state file:
   ```bash
   cat > .workflows/testing-pipeline/sub/test-pipeline.json <<EOF
   {
     "schema_version": "2.0.0",
     "owner": "test-pipeline-agent",
     "run_id": "${RUN_ID}",
     "init_at": "$(date -Iseconds)",
     "queues": {"functional": [], "api": [], "ui": []},
     "tracks_required_per_test": {}
   }
   EOF
   ```
5. Record `pipeline_start_time` for wall-clock budget tracking

**Dispatched mode:**
1. Read `.claude/config/test-pipeline.yml`
2. Use run_id from parent's dispatch context
3. Verify `test-results/` and `test-evidence/{run_id}/` exist (parent created)
4. Wipe ONLY `.workflows/testing-pipeline/sub/` (T2A's namespace) and recreate; do NOT wipe T1's `state.json` or test-results/
5. Initialize sub-state file (same as standalone step 4)
6. Use `remaining_budget` from dispatch context

**Schema check (both modes):** if `.workflows/testing-pipeline/sub/test-pipeline.json` exists from a prior run AND its `schema_version` major ≠ "2", emit `STATE_SCHEMA_INCOMPATIBLE` BLOCKED contract immediately.

### STEP 2 — SCOUT

Dispatch `test-scout-agent` in `classify` mode:

```
Agent(subagent_type=test-scout-agent,
      prompt="""
      ## Mode: classify
      ## Pipeline ID: <pipeline_id>
      ## Run ID: <run_id>
      ## Sub-state path: .workflows/testing-pipeline/sub/test-pipeline.json
      ## Config: .claude/config/test-pipeline.yml (track_detection block)

      Walk all test files in the project. Classify each by required tracks
      (functional/api/ui) using accumulate semantics per spec §3.1.
      Populate `queues.functional`, `queues.api`, `queues.ui` and
      `tracks_required_per_test` map. Sidecar files for queues >1000.
      Return classify-mode contract.
      """)
```

Receive return contract `{mode: "classify", tests_discovered: N, queue_counts: {...}, ...}`.
Sub-state file is now populated.

### STEP 3 — WAVE 1 (Functional + API in parallel)

Read `queues.functional` and `queues.api` from sub-state (or sidecars). Skip lanes with empty queues.

Dispatch BOTH lanes in a SINGLE Agent() message containing two invocations
(this is what gives Claude Code true cross-lane parallelism):

```
# Single message, two invocations:
Agent(subagent_type=<functional-lane-owner>,
      prompt="""
      ## Lane: functional
      ## Capture proof: true
      ## Run ID: <run_id>
      ## Queue: <queues.functional from sub-state>
      ## Output: test-results/functional.json + test-results/functional.jsonl

      Run all tests in the queue with --capture-proof:true (UI tests produce
      screenshots in test-evidence/{run_id}/screenshots/). Append per-test
      progress to functional.jsonl. Write final batch report to functional.json.
      Return lane contract.
      """)
Agent(subagent_type=<api-lane-owner>,
      prompt="""
      ## Lane: api
      ## Run ID: <run_id>
      ## Queue: <queues.api from sub-state>
      ## Output: test-results/api.json + test-results/api.jsonl

      Run API tests in the queue. After pytest, invoke /contract-test if contract
      files present. Combined verdict per spec §3.2. Emit NEEDS_CONTRACT_VALIDATION
      category if no contract tooling. Return lane contract.
      """)
```

Lane owner selection (read from `core/.claude/config/test-pipeline.yml` lanes block + project stack detection):
- Functional: `tester-agent` + stack-specific test runner skill (`/fastapi-run-backend-tests`, `/jest-dev`, `/vitest-dev`, `/pytest-dev`, etc.)
- API: `fastapi-api-tester-agent` for FastAPI projects; `tester-agent` + `/contract-test` + `/integration-test` for everything else

Both lanes return structured contracts. Collect both before proceeding to Wave 2.

### STEP 4 — WAVE 2 (UI/Visual lane)

Read `queues.ui` from sub-state. Skip if empty.

**Optional checkpoint optimization (REQ-S006):** if the functional lane writes `test-results/functional.ui-tests-complete.flag` partway through its execution (signaling all UI tests have finished and screenshots exist in `test-evidence/{run_id}/screenshots/`), T2A MAY dispatch the UI lane immediately upon detecting this flag, in parallel with the still-running functional lane finishing its non-UI tests. This reduces wall-clock time on projects with many slow non-UI tests after fast UI tests. The functional lane writes the flag via `tester-agent`'s lane mode after all UI-classified tests in its queue have completed. Disabled by default — enable via `lanes.ui.use_checkpoint: true` in `core/.claude/config/test-pipeline.yml`.

Dispatch the UI lane (`visual-inspector-agent` is universal across all stacks):

```
Agent(subagent_type=visual-inspector-agent,
      prompt="""
      ## Lane: ui
      ## Run ID: <run_id>
      ## Queue: <queues.ui from sub-state>
      ## Sub-state path: .workflows/testing-pipeline/sub/test-pipeline.json
      ## Screenshots dir: test-evidence/{run_id}/screenshots/
      ## Output: test-results/ui.json + test-results/ui.jsonl

      Read screenshots produced by the functional lane in Wave 1. Filter to
      tests where tracks_required_per_test[test_id] includes "ui". Apply
      dual-signal verdict matrix. Write per-test verdict to ui.jsonl.
      """)
```

Receive lane contract.

### STEP 5 — JOIN + per-test report

Read all three lane result files under `test-results/`:
- `test-results/functional.json`
- `test-results/api.json` (may be skip/empty)
- `test-results/ui.json` (may be skip/empty)

After JOIN, T2A also writes an advisory mirror at `test-results/pipeline-verdict.json`
for backward-compat with downstream consumers that previously read T1's authoritative
aggregator output. T1 remains the single source of truth for the authoritative
verdict (spec §3.4); T2A's mirror is marked `t1_authoritative: false` to make the
distinction explicit.

For each `test_id` in the union of all three queues, evaluate the per-test gate:

```python
required = tracks_required_per_test[test_id]   # subset of {functional, api, ui}
applicable_lanes = [l for l in required if not lane_skipped[l]]
if not applicable_lanes:
    verdict = "PASS"   # no required lane ran — degenerate case, treat as pass
else:
    verdict = "PASS" if all(lane_results[l][test_id] == "PASSED" for l in applicable_lanes) else "FAIL"
```

Write `test-results/per-test-report.md` with the table format per spec §3.4:

```markdown
| Test                                          | FUNC | API  | UI   | VERDICT |
|-----------------------------------------------|------|------|------|---------|
| tests/test_login.py::test_oauth               | ✅   | ✅   | n/a  | PASS    |
| tests/test_checkout.py::test_full_flow        | ✅   | ✅   | ❌   | FAIL    |
| ...                                                                       |
```

Print the table to console. Build end-of-run summary per spec §3.4.

### STEP 6 — TRIAGE DISPATCH (T2B)

Identify the consolidated failure set: list of `test_id`s with `verdict == "FAIL"` plus their per-lane failure data.

If failure set is empty → skip to STEP 7 with empty result.

Otherwise, dispatch `failure-triage-agent` (T2B):

```
Agent(subagent_type=failure-triage-agent,
      prompt="""
      ## Pipeline ID: <pipeline_id>
      ## Run ID: <run_id>
      ## Failures: <serialized failure set with per-lane evidence>
      ## Remaining budget: <remaining_budget>
      ## Sub-state: .workflows/testing-pipeline/sub/test-pipeline.json

      Process the failure set per PR2 full triage subgraph (analyzer → issue-manager
      → fixer → serialize → escalation if needed). Return structured triage outcome
      including issues_created, fixes_applied, fixes_pending counts.
      """)
```

**PR2 (current):** T2B returns one of:
- `{"result": "TRIAGE_COMPLETE", "issues_created": N, "fixes_applied": M, "fixes_pending": K, ...}` — normal completion
- `{"result": "BLOCKED", "blocker": "GITHUB_NOT_CONNECTED|DISPATCH_BUDGET_EXCEEDED|WALL_CLOCK_BUDGET_EXCEEDED", "remediation": "..."}` — abort
- `{"result": "TRIAGE_INCOMPLETE", "abort_reason": "RETRY_BUDGET_EXHAUSTED", "escalation_report": "test-results/escalation-report.md", ...}` — partial completion with escalation

T2A reads the result; on BLOCKED, propagates immediately to T1 (skip STEP 7's normal flow). On TRIAGE_COMPLETE or TRIAGE_INCOMPLETE, includes the triage outcome in STEP 7's bubble-up contract so T1 can incorporate into pipeline-verdict.json.

### STEP 7 — BUBBLE-UP / RETURN

**Standalone mode:** print summary to console, return human-readable report.

**Dispatched mode:** return structured contract to T1 (PR2: includes T2B triage outcome):

```json
{
  "gate": "PASSED|FAILED|BLOCKED",
  "artifacts": {
    "functional": "test-results/functional.json",
    "api": "test-results/api.json",
    "ui": "test-results/ui.json",
    "per_test_report": "test-results/per-test-report.md",
    "sub_state": ".workflows/testing-pipeline/sub/test-pipeline.json",
    "triage_state": ".workflows/testing-pipeline/sub/failure-triage.json",
    "escalation_report": "test-results/escalation-report.md (if triage incomplete)"
  },
  "lane_summaries": {
    "functional": {"passed": 98, "failed": 2},
    "api": {"passed": 48, "failed": 2, "skipped": 50},
    "ui": {"passed": 7, "failed": 1, "skipped": 92}
  },
  "triage_outcome": {
    "result": "TRIAGE_COMPLETE | TRIAGE_INCOMPLETE | BLOCKED",
    "issues_created": 5,
    "fixes_applied": 3,
    "fixes_pending": 2,
    "issue_only_count": 2,
    "cross_lane_root_causes_detected": 1
  },
  "decisions": ["Wave 1 ran functional + API in parallel", "T2B triaged 5 failures: 3 healed, 2 ISSUE_ONLY"],
  "blockers": [],
  "summary": "100 tests, 95 PASSED, 5 FAILED — 3 auto-healed, 2 Issues await human review",
  "retry_budget_consumed": 3,
  "duration_seconds": 234
}
```

T1 reads `triage_outcome` directly from this contract. T1 does NOT create Issues itself in PR2 — that's T2B's responsibility now (atomic switchover deleted T1's inline step).

T1 reads `failures_for_t1` and creates GitHub Issues using its inline step (extended in PR1 to handle 4 new API categories).

## Lane Owner Selection (Stack-Aware)

Detect project stack via existing `bootstrap.py` STACK_PREFIXES + `recommend.py` DEP_PATTERN_MAP signals (e.g., presence of `pyproject.toml` + FastAPI dependency = FastAPI stack). Select owners:

| Stack | Functional Lane | API Lane | UI Lane |
|---|---|---|---|
| FastAPI | `tester-agent` + `/fastapi-run-backend-tests` | `fastapi-api-tester-agent` | `visual-inspector-agent` |
| Bun/Elysia | `tester-agent` + `/bun-elysia-test` | `tester-agent` + `/contract-test` | `visual-inspector-agent` |
| Vue/Nuxt | `tester-agent` + `/vue-test` | `tester-agent` + `/contract-test` + `/middleware-test` | `visual-inspector-agent` |
| Generic | `tester-agent` + `/pytest-dev` ∨ `/jest-dev` ∨ `/vitest-dev` | `tester-agent` + `/contract-test` + `/integration-test` | `visual-inspector-agent` |

When invoking `tester-agent`, always pass `lane: "functional"` or `lane: "api"` in dispatch context per the agent's NON-NEGOTIABLE block.

## Budget Tracking (Measurable Proxies)

Per spec §3.10.1, T2A tracks two measurable budgets (NOT tokens — Claude Code subagents don't return token counts):

- **Dispatch counter** — increment on every `Agent()` call this T2A makes. Cap: `concurrency.max_total_dispatches` (default 100). Exceeded → `BLOCKED: DISPATCH_BUDGET_EXCEEDED`.
- **Wall-clock** — record `pipeline_start_time` at INIT; check `elapsed_minutes()` before each STEP. Cap: `budget.max_wall_clock_minutes` (default 90). Exceeded → `BLOCKED: WALL_CLOCK_BUDGET_EXCEEDED`.

Either budget exceeded → return BLOCKED contract → T1 propagates → exit code 2.

## Gate Enforcement Rules

- **`--strict-gates` (always passed by this orchestrator to lane workers):** Missing lane return JSON = BLOCK. No "proceed without gate check." This T2A runs fail-closed by design — fail-closed means missing evidence is treated as a failure, not an excuse to skip.
- **`capture_proof: true`** is passed to the functional lane (read from `lanes.functional.capture_proof` in `core/.claude/config/test-pipeline.yml`) so UI tests produce screenshots into `test-evidence/{run_id}/screenshots/` for the UI lane (Wave 2) to review. Non-UI tests also get capture_proof on failure per testing.md for supplementary evidence.
- Screenshot verdict for UI tests is ALWAYS blocking when FAILED — same rule as T1 master.

## Skill Cross-References

- Read `core/.claude/config/test-pipeline.yml` for lane definitions (including `capture_proof`), track detection rules, concurrency caps, budgets
- Read `core/.claude/rules/testing.md` for verdict authority rules (UI screenshot is authoritative)
- Read `core/.claude/rules/agent-orchestration.md` rules 6 and 8 (state ownership, responsibility cap)

## MUST NOT

- MUST NOT write to T1's state file at `.workflows/testing-pipeline/state.json` — read-only access; T2A owns sub-state ONLY
- MUST NOT exceed 4 top-level responsibilities (currently at 4: scout dispatch, lane dispatch + JOIN, T2B dispatch, BUBBLE-UP)
- MUST NOT skip the schema-version check on the sub-state file
- MUST NOT dispatch Wave 2 before Wave 1 returns (UI lane reads screenshots produced by functional lane)
- MUST NOT batch the per-test gate evaluation — write `per-test-report.md` after JOIN completes
- MUST NOT silently skip a lane that has work — empty queue is a skip; populated queue MUST dispatch
- MUST NOT exceed `max_total_dispatches` (100) or `max_wall_clock_minutes` (90) — abort with BLOCKED contract
- MUST NOT continue after T2B returns a non-NO_OP_PR1_SKELETON failure (PR1 expects NO_OP only; PR2 will activate full triage flow)
