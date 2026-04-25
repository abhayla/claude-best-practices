# Spec: Three-Lane Test Pipeline (v2 — skill-at-T0 pattern)

## Meta

- Author: Claude Code (Opus 4.7)
- Date: 2026-04-24
- Status: **ACCEPTED** — approved design for Phase 3.1 of the subagent-dispatch-platform-limit remediation. Implementation in progress on branch `feat/phase3-1-test-pipeline-skill-at-t0`; this doc is the design that branch encodes.
- Version: 2.2
- Revision history:
  - 2.0 (2026-04-24) — initial draft; encodes skill-at-T0 design from Phase 3.0 template
  - 2.1 (2026-04-24) — traceability audit against v1 found 2 concrete gaps + 5 unclear-ownership items; this revision addresses all of them. Specifically: REQ-S002 `--update-baselines` flag added to CLI signature; REQ-S006 UI-lane early-start checkpoint preserved with T0 polling logic; REQ-M015 + §3.5 NN-3 dispatch-budget ownership explicitly assigned to T0; REQ-M035 validator allowlist disposition specified; §3.3 lane-skip rule restated.
  - 2.2 (2026-04-24) — §7 open questions resolved with user-approved "lean" answers: Q1 inline orchestration, Q2 preserve empty `sub_orchestrators:`, Q3 `/e2e-visual-run` independent, Q4 complexity classifier in 3.1 behind feature flag. Status promoted DRAFT/PROPOSED → ACCEPTED. Branch `feat/phase3-1-test-pipeline-skill-at-t0` cut.
- Supersedes: `docs/specs/test-pipeline-three-lane-spec.md` (v1.7) — v1's **functional contract is preserved**; only the **dispatch architecture** changes. All v1 requirements (REQ-M001 through REQ-C001) remain in force unless explicitly amended here.
- Triggered by:
  - `.claude/tasks/lessons.md` 2026-04-24 entry: "Parallel tool dispatch in Claude Code is more restricted than prompt-engineering guidance suggests"
  - `.claude/tasks/lessons.md` 2026-04-24 entry: "Platform constraints cascade — one broken primitive can invalidate an entire architectural pattern"
  - Anthropic official docs: [*"subagents cannot spawn other subagents"*](https://code.claude.com/docs/en/sub-agents)
  - GH #19077, GH #4182 (platform-constraint corroboration)
- References:
  - `core/.claude/rules/agent-orchestration.md` §1–3, §10 (Phase 1 rewrite — single-level dispatch model)
  - `core/.claude/rules/pattern-structure.md` Tool Grants (Phase 1 rewrite — context-aware Agent invariant)
  - `core/.claude/agents/workflow-master-template.md` v2.0.0 (Phase 3.0 — skill-at-T0 template)
  - `scripts/tests/test_orchestrator_tool_grants.py` (Phase 2 — context-aware validator using `dispatched_from:` field)
  - `docs/specs/test-pipeline-three-lane-spec.md` v1.7 (functional baseline — the what; this v2 only changes the how)

---

## 1. Why v2 exists

Claude Code does not forward the `Agent` tool to dispatched subagents ([official docs](https://code.claude.com/docs/en/sub-agents), GH #19077, GH #4182, three independent 2026-04-24 runtime probes). v1's architecture depends on nested `Agent(subagent_type=...)` dispatch at every tier — specifically:

- §3.3 Wave 1: `test-pipeline-agent` (T2A) dispatches functional + API lane workers via `Agent()`
- §3.5 T2B triage: `failure-triage-agent` (T2B) fans out to analyzer, issue-manager, and fixer workers via `Agent()`
- §3.8 Wave 2: T2A dispatches `visual-inspector-agent` via `Agent()`

**None of these executes as designed at runtime.** Each dispatch silently inlines because the dispatched T2 agent cannot access the `Agent` tool. The testbed run on 2026-04-24 (testbed `SUBAGENT_DISPATCH_PROBE` event) confirmed this directly, as did two independent probes.

v2 preserves every functional goal of v1 but relocates the orchestration from a dispatched T2 agent to the **user's T0 session**, via a skill-at-T0 pattern. `/test-pipeline`'s body IS the orchestrator; workers remain flat single-responsibility subagents dispatched from T0 (where `Agent()` actually works).

---

## 2. What v1 requirement numbers remain unchanged

All v1 requirements keep their IDs and functional meaning. Only the **execution topology** changes. Specifically unchanged:

- REQ-M001–M032 (must-have functional behavior — scout, lanes, JOIN gate, per-test verdicts, triage, fix fan-out, Issue lifecycle, budget enforcement, auto-fix matrix)
- REQ-M033 (pre-merge evals gate)
- REQ-S001–S010 and REQ-C001–C003 (should-have / could-have — all retain their original meaning and deferral / ship status)
- All artifact contracts (`test-results/*.json`, `test-evidence/{run_id}/`, per-test report format)
- All gate evaluation semantics (screenshot authority, dual-signal verdict)
- All schemas (`schema_version` pinning, `classification_source` provenance, etc.)

What v2 amends is strictly the architectural topology in §3.3, §3.5, §3.8 of v1, plus the introductory §2 approach description. Every downstream consumer of a v1 requirement (tests, code, downstream projects) reads the same artifact format and gets the same verdict.

---

## 3. v2 Architecture — skill-at-T0

### 3.0 Execution Model Constraint (NEW §0)

The orchestrator MUST run at T0 (the user's session). Concretely:

- `/test-pipeline` is a **skill whose body is injected into the user's T0 session**. The T0 session then executes the injected orchestration logic.
- Workers (test-scout-agent, tester-agent, fastapi-api-tester-agent, visual-inspector-agent, test-failure-analyzer-agent, github-issue-manager-agent, fixer agents) are dispatched via `Agent(subagent_type=…)` from T0. This works because T0 has the `Agent` tool.
- **No intermediate orchestrator agent exists.** Neither `testing-pipeline-master-agent` (T1) nor `test-pipeline-agent` (T2A) nor `failure-triage-agent` (T2B) is invoked. All three are deprecated in Phase 1; v2 dissolves their orchestration logic into the `/test-pipeline` skill body. Phase 3.1 deletes the `sub_orchestrators:` declarations from `config/workflow-contracts.yaml` for this workflow.
- Parallelism at T0: multiple `Agent()` calls in a **single assistant message** run concurrently (empirically verified 2026-04-24). This is the ONLY reliable parallelism in Claude Code — `Skill()` and `Bash()` in one message serialize.
- Workers MUST NOT nest-dispatch. Worker bodies that attempt `Agent(subagent_type=…)` silently inline at runtime. Phase 2's `dispatched_from: worker` frontmatter + `test_orchestrator_tool_grants.py` validator enforces this at CI.

### 3.1 Lifecycle (rewrites v1 §3.2, §3.3, §3.5, §3.8)

```
/test-pipeline [failure_output] [--capture-proof | --no-capture-proof]
               [--skip-fix] [--only-issues N,M] [--fix-pr-mode]
               [--full-suite-before-success] [--update-baselines]
      ↓
      (skill body injected into T0 session)
      ↓
┌─────────────────────────────────────────────────────────────────┐
│  T0 SESSION (the user's) — runs /test-pipeline body             │
│                                                                 │
│  STEP 1  INIT                                                   │
│     • Read .claude/config/test-pipeline.yml (schema 2.0.0)      │
│     • Generate run_id = {ISO-8601}_{7-char-git-sha}             │
│     • Clean test-results/ test-evidence/ .workflows/            │
│       testing-pipeline/ (standalone — no parent owns cleanup)   │
│     • Initialize state at .workflows/testing-pipeline/          │
│       state.json (schema 2.0.0)                                 │
│     • Append INIT event to events.jsonl                         │
│                                                                 │
│  STEP 2  SCOUT                                                  │
│     • Agent(subagent_type=test-scout-agent, prompt="            │
│         ## Mode: classify                                       │
│         ## Run ID: <run_id>                                     │
│         ## State: .workflows/testing-pipeline/state.json        │
│         ## Config: .claude/config/test-pipeline.yml             │
│         Walk all test files; classify by required tracks       │
│         (functional/api/ui); populate queues + tracks_required  │
│         map. Sidecar files for queues >1000.")                 │
│     • Parse return contract; sub-state file now populated       │
│                                                                 │
│  STEP 3  WAVE 1 (Functional + API in true parallel)             │
│     • Skip lane if its queue is empty (REQ-M001 lane skip rule) │
│       — record synthetic SKIP result, do NOT dispatch            │
│     • Otherwise, in a SINGLE T0 message, Agent() per lane:      │
│         Agent(subagent_type=<functional-lane-owner>, prompt="...│
│         Agent(subagent_type=<api-lane-owner>, prompt="...       │
│     • Wait for both; read lane JSON artifacts                   │
│                                                                 │
│  STEP 4  WAVE 2 (UI/Visual lane)                                │
│     • Skip if UI queue empty (record SKIP, do NOT dispatch)     │
│     • Checkpoint-early-start (REQ-S006): if the functional     │
│       lane writes test-results/functional.ui-tests-complete.    │
│       flag partway through its run AND lanes.ui.use_checkpoint  │
│       is true in test-pipeline.yml, T0 polls for the flag       │
│       (short sleep loop, max 30s) and dispatches visual-        │
│       inspector-agent as soon as the flag appears — in parallel │
│       with the still-running functional lane's non-UI tests.   │
│       Else: wait for Wave 1 to fully return, then dispatch.     │
│     • Agent(subagent_type=visual-inspector-agent, prompt="      │
│         ## Lane: ui                                             │
│         Read screenshots from Wave 1; filter to UI-required     │
│         tests; dual-signal verdict per spec §3.2")              │
│     • Read ui.jsonl + ui.json                                   │
│     • If --update-baselines flag set: visual-inspector-agent    │
│       overwrites baselines for the captured run instead of      │
│       comparing — per v1 REQ-S002 semantics. Triage and          │
│       verify-affected steps SKIP in baseline-update mode.       │
│                                                                 │
│  STEP 5  JOIN + per-test report                                 │
│     • Per-test verdict = AND of applicable lane results         │
│     • Write test-results/per-test-report.md                     │
│                                                                 │
│  STEP 6  TRIAGE (inline, dispatches workers directly)           │
│     • If any failures, enter triage subgraph at T0:             │
│         - Analyze: N batched Agent() calls (max 5 concurrent)   │
│           to test-failure-analyzer-agent                        │
│         - Issue-manage: N batched Agent() calls (max 5)         │
│           to github-issue-manager-agent (hard-fail on           │
│           GITHUB_NOT_CONNECTED per v1 REQ-M015)                 │
│         - Fix: N batched Agent() calls (max 5) to               │
│           stack-specific fixer agents                           │
│         - Apply: Skill("/serialize-fixes", ...) inline          │
│         - Escalate: Skill("/escalation-report", ...) if budget  │
│           exhausted                                             │
│     • If --fix-pr-mode, Skill("/pipeline-fix-pr", ...) instead  │
│                                                                 │
│  STEP 7  VERIFY-AFFECTED                                        │
│     • If fixes applied, loop: re-dispatch Wave 1 + Wave 2 for   │
│       the affected test subset only                             │
│     • Continue until green OR budget exhausted                  │
│                                                                 │
│  STEP 8  FINAL FULL-SUITE PASS (when configured)                │
│     • Wave 1 + Wave 2 over complete suite to catch collateral   │
│       regressions (v1 REQ-S006 equivalent)                      │
│                                                                 │
│  STEP 9  COMMIT + REPORT                                        │
│     • Skill("/post-fix-pipeline", ...)                          │
│     • Print completion dashboard + handoff suggestions          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Parallelism at T0 (rewrites v1 §3.3)

v1 used a dispatched T2A agent that then dispatched lane workers via `Agent()` — **broken**. v2 issues the dispatch from T0 directly:

```
# Inside the T0 session, one assistant message with two tool_use blocks:
Agent(subagent_type="tester-agent",
      prompt="""## Lane: functional
                ## Capture proof: true
                ## Run ID: {run_id}
                ## Queue: {queues.functional}
                ## Output: test-results/functional.json + functional.jsonl
                Run all tests in the queue with --capture-proof:true.
                Return lane contract.
             """)

Agent(subagent_type="fastapi-api-tester-agent",
      prompt="""## Lane: api
                ## Run ID: {run_id}
                ## Queue: {queues.api}
                ## Output: test-results/api.json + api.jsonl
                Run API tests. Invoke /contract-test if contract files
                present. Combined verdict per spec §3.2.
                Return lane contract.
             """)
```

Both calls run concurrently. Once both return, T0 reads both lane artifacts and proceeds to Wave 2.

Lane-owner resolution rules from v1 §3.3 carry forward unchanged:

- **Functional:** `tester-agent` + stack-specific runner skill (`/pytest-dev`, `/jest-dev`, `/vitest-dev`, `/fastapi-run-backend-tests`, etc.)
- **API:** `fastapi-api-tester-agent` for FastAPI projects; `tester-agent` + `/contract-test` + `/integration-test` otherwise

### 3.3 Triage subgraph (rewrites v1 §3.5)

v1 had T2B (`failure-triage-agent`) with three fan-outs via `Agent()` — broken. v2 runs the fan-outs directly from T0:

```
# Inside T0, after STEP 5 produces consolidated failure set:

# Fan-out 1 — analyzers (max_concurrent_analyzers=5)
for failure_chunk in chunks(failures, size=5):
    # Single T0 message, up-to-5 Agent() calls:
    for failure in failure_chunk:
        Agent(subagent_type="test-failure-analyzer-agent",
              prompt="""## Failure: {failure_id}
                        ## Test log: {path}
                        ## Config: .claude/config/test-pipeline.yml
                        Classify; return analyzer contract with
                        recommended_action per auto-heal matrix.""")

# Fan-out 2 — issue-managers (max_concurrent_issue_managers=5)
# ... same pattern ...

# Fan-out 3 — fixers (max_concurrent_fixers=5)
# Only for AUTO_HEAL recommended_action per v1 §3.6 auto-heal matrix
# ... same pattern ...

# Skill apply:
Skill("/serialize-fixes", args="...")

# Or in --fix-pr-mode:
Skill("/pipeline-fix-pr", args="...")

# Budget guard:
if global_retries_remaining == 0 or failures_unresolved:
    Skill("/escalation-report", args="...")
```

Chunking of fan-outs: each chunk is one T0 message with up-to-5 `Agent()` calls. The orchestrator waits for all 5 in a chunk to return, aggregates, then starts the next chunk. Preserves v1's `max_concurrent_*` semantics; honors the `partial_failure_policy: abort_on_first_blocked` rule from v1 §3.7.1 (a single `GITHUB_NOT_CONNECTED` from any issue-manager aborts the entire triage).

**Budget ownership (REQ-M015 + §3.5 NN-3 at T0).** v1 assigned `max_total_dispatches` (default 100) and `max_wall_clock_minutes` (default 90) tracking to `failure-triage-agent` (T2B). With T2B dissolved, the T0 orchestrator assumes these responsibilities:

- `dispatches_used` and `wall_clock_elapsed_minutes` counters live in `.workflows/testing-pipeline/state.json` (the single consolidated state file per §3.4).
- The T0 orchestrator increments `dispatches_used` by N at each fan-out chunk dispatch (N = chunk size).
- Before dispatching each chunk, the T0 orchestrator checks `dispatches_used < max_total_dispatches` AND `wall_clock_elapsed_minutes < max_wall_clock_minutes`. If either is exceeded, the chunk is NOT dispatched — instead the pipeline emits a `BLOCKED` contract: `{"result": "BLOCKED", "blocker": "BUDGET_EXHAUSTED", "dispatches_used": N, "wall_clock_elapsed": M}` into `test-results/pipeline-verdict.json`, invokes `/escalation-report`, and returns exit-code-2-equivalent (i.e., a non-zero terminal return to the user's T0 session).
- Exit-code-2 semantics at T0: since T0 is the user's interactive session, there is no process exit code. Instead the verdict JSON's `result: "BLOCKED"` field IS the signal. The session prints a visible `BLOCKED` banner + the escalation-report path so the user sees the failure before any handoff suggestions.

### 3.4 State ownership (rewrites v1 §3.4)

v1 had three state files with tiered parent/child ownership: T1 owned `state.json`, T2A owned `sub/test-pipeline.json`, T2B owned a sub-sub-file. Runtime-broken because the children couldn't dispatch; also unnecessary because there's only one orchestrator now.

v2 collapses to a **single state file** owned by the T0 orchestrator:

```
.workflows/testing-pipeline/state.json    (schema 2.0.0)
.workflows/testing-pipeline/events.jsonl  (append-only)
```

The state file includes queues, `tracks_required_per_test`, and per-step status (previously split across three files). Workers READ the state file to scope their work (via paths in their dispatch context) but never write to it — they return structured contracts that T0 merges into state.

Migration from v1's three-file layout: one-time cleanup in Phase 3.1 PR. No downstream compatibility concern — state files are per-run ephemeral.

---

## 4. Functional requirements preserved from v1

Per §2, every v1 requirement remains in force. Selected high-impact pins:

| Requirement | v1 location | v2 mapping |
|---|---|---|
| REQ-M001 (three-lane per-test gate) | v1 §3.1, §3.3 | STEP 3 + STEP 4 + STEP 5 above |
| REQ-M009 (screenshot verdict authority) | v1 §3.2, testing.md | Preserved — visual-inspector-agent returns authoritative verdict |
| REQ-M011 (T1 Issue-creation retired) | v1 §2 item 10 | Already retired in v1.x; unchanged |
| REQ-M015 (GITHUB_NOT_CONNECTED hard-fail) | v1 §3.7.1 | Preserved — first `GITHUB_NOT_CONNECTED` from any issue-manager aborts triage |
| REQ-M017 (auto-heal matrix config-driven) | v1 §3.6 (REQ-S004) | Preserved — analyzer reads `.claude/config/test-pipeline.yml` auto_heal block |
| REQ-M032 (screenshot capture on every test) | v1 §3.2, testing.md | Preserved — functional lane dispatched with `--capture-proof: true` |
| REQ-M033 (pre-merge evals gate) | v1 §4 | Preserved — applies to every worker touched in this refactor |
| Global retry budget (default 15) | v1 §3.4 | Preserved — T0 owns the budget, workers decrement via return contract |
| `max_concurrent_*` caps | v1 §3.5 | Preserved — enforced as T0 chunk size |
| REQ-M015 dispatch / wall-clock budget | v1 §3.5 | Preserved — T0 owns `dispatches_used` + `wall_clock_elapsed_minutes` counters in state.json; BLOCKED verdict emitted when exceeded (see §3.3 end) |
| REQ-M035 orchestrator-responsibility-count validator | v1 §4 | Validator **remains**; allowlist entry for `failure-triage-agent` **removed** when that agent's deprecated file is finally deleted (post-deprecation-window, not in Phase 3.1). Until then the allowlist entry stays pointing at the deprecated file — the validator skips `deprecated: true` agents per Phase 2 design |
| REQ-S002 `--update-baselines` flag | v1 §3.3 baseline-update mode | Preserved — flag added to §3.1 CLI signature; STEP 4 describes baseline-update semantics; triage + verify-affected SKIP in baseline-update mode |
| REQ-S006 UI-lane checkpoint early-start | v1 §3.3 REQ-S006 | Preserved — STEP 4 polls for `test-results/functional.ui-tests-complete.flag` when `lanes.ui.use_checkpoint: true` in `test-pipeline.yml` (default false, matching v1); falls back to serial Wave-1-then-Wave-2 otherwise |
| §3.3 Lane skip rule (empty queue ⇒ no dispatch) | v1 §3.3 NN-4 | Preserved — STEP 3 + STEP 4 explicitly record synthetic SKIP result for empty queues |

---

## 5. What's deleted, deprecated, or replaced in Phase 3.1

| Item | Action |
|---|---|
| `core/.claude/agents/testing-pipeline-master-agent.md` | Already `deprecated: true` (Phase 1). Phase 3.1 does nothing new with this file; it waits out the 2-version-cycle deprecation window. |
| `core/.claude/agents/test-pipeline-agent.md` | Same as above |
| `core/.claude/agents/failure-triage-agent.md` | Same as above |
| `core/.claude/agents/e2e-conductor-agent.md` | Same as above (deprecated in Phase 2) |
| `core/.claude/skills/testing-pipeline-workflow/SKILL.md` | Same as above (deprecated in Phase 1) |
| `core/.claude/skills/test-pipeline/SKILL.md` | **Full body rewrite** per §3.1 — from thin `Agent()` dispatch wrapper to skill-at-T0 orchestrator body |
| `core/.claude/skills/e2e-visual-run/SKILL.md` | **Full body rewrite** to dispatch queue workers (scout/inspector/healer) directly from T0, replacing the deleted e2e-conductor orchestration |
| `config/workflow-contracts.yaml` → `testing-pipeline` | Remove `sub_orchestrators:` list; keep `steps:`, `master_agent:` becomes meaningless but kept as `null` or removed per migration consensus |

---

## 6. Acceptance criteria

Phase 3.1 PR is acceptance-complete when all of the following hold:

### AC-001 — `/test-pipeline` runs end-to-end on a non-trivial suite

**Given** a repo with ≥50 tests spread across functional, api, and ui tracks  
**When** the user invokes `/test-pipeline` from a T0 session  
**Then** Wave 1 lanes run in measurable wall-clock parallel (functional end_time < api start_time + ε is FALSE — i.e., they overlap)  
**And** STEPS 1–9 complete with a valid `test-results/pipeline-verdict.json` written  
**And** the verdict matches what the v1-equivalent run would produce on the same suite (semantic equivalence check)

### AC-002 — No nested `Agent()` calls exist in any worker

**Given** the Phase 3.1 PR diff  
**When** `scripts/tests/test_orchestrator_tool_grants.py` runs (Phase 2 validator)  
**Then** every worker in `core/.claude/agents/` has `dispatched_from: worker` (explicit or default) AND does not declare `Agent` in `tools:`  
**And** grep for `Agent(subagent_type=` inside worker bodies returns zero hits  
**And** the runtime probe integration test (Phase 2) passes when run with `CLAUDE_CODE_INTEGRATION=1`

### AC-003 — Mid-phase eval gate (5-criterion rubric)

**Given** the Phase 3.1 PR and v1's last green main commit  
**When** both are run against a representative 50-test suite (fixture in `scripts/tests/fixtures/`)  
**Then** all 5 criteria score equal or better on v2 vs v1:
1. Lane-dispatch correctness (all classified tests run in their assigned lane)
2. Budget enforcement (`global_retries_remaining` decrement matches v1 semantics)
3. Gate evaluation (per-test verdicts match v1 on the same inputs)
4. Return-contract fidelity (`pipeline-verdict.json` schema unchanged)
5. Wall-clock time (v2 within 1.2× of v1; stretch: beat v1 due to T0 parallelism without the dispatch-overhead tax of broken nested calls)

**Human review checkpoint:** a human reviewer approves the 5-criterion rubric report before Phase 3.2 starts.

### AC-004 — No regression in CI gates

**Given** all 4 local CI gates  
**When** run on the Phase 3.1 branch  
**Then** all 4 PASS with 0 warnings:
- `dedup_check --validate-all`
- `dedup_check --secret-scan`
- `workflow_quality_gate_validate_patterns`
- `pytest scripts/tests/` — test count at or above current baseline (1407 passed on Phase 2 branch)

### AC-005 — Cutover safety

**Given** any in-progress `.workflows/testing-pipeline/` run  
**When** the Phase 3.1 PR attempts to merge  
**Then** the PR's pre-merge check fails fast with a `PIPELINE_IN_PROGRESS` error, preventing state corruption  
**And** the user is directed to complete or abort the in-flight run before re-triggering the merge

---

## 7. Resolved design decisions (2026-04-24)

All four questions resolved with user-approved "lean" answers. These are binding for the Phase 3.1 implementation PR.

- **Q1 RESOLVED — Inline orchestration.** The `/test-pipeline` skill body carries all 9 STEPS (§3.1 lifecycle) inline. No sub-skill delegation for orchestration *control flow*. Utility skills (`/serialize-fixes`, `/escalation-report`, `/pipeline-fix-pr`, `/post-fix-pipeline`) remain callees invoked via `Skill()` from the orchestrator — they execute concrete work, not orchestration.
- **Q2 RESOLVED — Preserve with empty list.** `config/workflow-contracts.yaml` → `testing-pipeline` keeps its entry; `sub_orchestrators:` is set to `[]`. Uniformity across workflows matters for Phase 3.2–3.8, which will follow the same shape. `master_agent:` is set to `null` (was `testing-pipeline-master-agent`, now dissolved).
- **Q3 RESOLVED — Independent.** `/e2e-visual-run` stays a standalone skill with its own body. No shared injection with `/test-pipeline`. The two skills have different argument contracts and different primary callers; coupling them now would mean a breaking change every time either evolves. Future code-sharing MAY happen after both stabilize.
- **Q4 RESOLVED — Ship in Phase 3.1 behind a feature flag.** The complexity classifier (size-based switch between parallel and serial Wave 1 execution) ships in the Phase 3.1 PR. Config key: `lanes.parallel_classifier` in `test-pipeline.yml`, with sub-keys `enabled: bool` (default `true`), `min_test_count: int` (default `50`). When `enabled: true` and `scout.test_count >= min_test_count`, Wave 1 runs in parallel per §3.2; otherwise Wave 1 runs serially (functional lane fully, then API lane). Scout contract extended by one field (`test_count: int`) — non-breaking addition per §2 (v1 requirements preserved unless explicitly amended).

---

## 8. Success metrics

- **Functional:** 100% of v1 requirements pass on v2 — no regression in any AC-001 through AC-005 criterion.
- **Performance:** Wave 1 wall-clock time ≤ 0.7× v1 on suites of ≥50 tests (v1 was serial-via-broken-dispatch anyway; v2 should materially beat it).
- **Adoption:** Downstream projects using `/test-pipeline` see no test failures attributable to the refactor on their first `/update-practices` after Phase 3.1 merges.
- **Validator:** 0 new agents introduced in `core/.claude/agents/` between Phase 3.1 and the end of Phase 3 that fail the `test_orchestrator_tool_grants.py` context-aware check — confirms the template (Phase 3.0) + validator (Phase 2) + skill-at-T0 pattern (Phase 3.1) combine to prevent regression.

---

## 9. Dependencies on other PRs

Phase 3.1 implementation PR cannot merge until:

- PR #20 (Phase 1 docs + deprecations) is merged — provides the agent-orchestration.md rewrite this spec references
- PR #21 (Phase 2 validator) is merged — provides the `dispatched_from:` field + test_orchestrator_tool_grants.py invariants this spec's AC-002 requires
- PR #22 (Phase 3.0 template) is merged — provides the skill-at-T0 template that the `/test-pipeline` rewrite conforms to

Phase 3.1 may start drafting on a branch stacked on the latest of those three, but acceptance testing (AC-003 eval gate) requires all three to be merged to main first — otherwise the v1-vs-v2 comparison baseline is contaminated.

---

## 10. Non-goals

- **Not changing the functional test protocol** — v1's detection rules, auto-heal matrix, Issue dedup signature, and screenshot capture semantics stay identical.
- **Not optimizing test-scout classification** — scout remains a single-agent walk; parallel scout was considered and rejected in v1.
- **Not migrating downstream projects' configurations** — projects update via `/update-practices` on their schedule; v2 is source-compatible with v1's `.claude/config/test-pipeline.yml` (schema 2.0.0 preserved).
- **Not implementing Option B (external script wrapper)** — v2 deliberately stays in-Claude-Code because empirical evidence from Phase 0 showed T0 `Agent()` parallelism is sufficient for lane-level concurrency. If a future measurement shows the 5-concurrent fan-out cap is a bottleneck, Option B becomes a Phase 4 consideration.
- **Not solving Claude Code's session-pinned agent registry** — Claude Code loads its agent registry at session start, not on-demand from `.claude/agents/`. Agents synced mid-session via `/update-practices` or manual curl are on disk but NOT dispatchable in the same session. The skill body works around this with STEP 1 sub-step 2b `WORKER_REGISTRY_PROBE` (BLOCKED with `WORKER_REGISTRY_NOT_LOADED` and restart remediation) and `/update-practices` `RESTART REQUIRED` banner. Surfaced 2026-04-25 during FIREKaro-Vue downstream validation when `/update-practices` synced 5 worker agents and the same session's `/test-pipeline` STEP 2 SCOUT dispatch failed with "Agent type 'test-scout-agent' not found" despite the file being on disk and committed. Documented in `core/.claude/rules/pattern-structure.md` "Agent registry session-pinning" subsection. A platform-side fix would belong in Claude Code itself, not the hub.

---

**End of spec v2.0 (draft).** Ready for review; will be refined to v2.1 based on reviewer feedback before the Phase 3.1 implementation PR is opened.
