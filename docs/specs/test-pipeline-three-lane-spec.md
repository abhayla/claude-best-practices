# Spec: Three-Lane Test Pipeline with Per-Test GitHub Issues + Parallel Auto-Fix

## Meta
- Author: Claude Code (Opus 4.7)
- Date: 2026-04-23
- Status: READY FOR /writing-plans (after 5 independent reviewer passes; reviewer-pass-5 declared "READY, high confidence" after v1.6 cleanup)
- Version: 1.6
- Source brainstorm: `/brainstorm` session 2026-04-23 with user
- Revision history:
  - 1.0 (2026-04-23) — initial spec from brainstorm
  - 1.1 (2026-04-23) — closed 20 self-review gaps
  - 1.2 (2026-04-23) — closed 10 reviewer-pass-1 gaps
  - 1.3 (2026-04-23) — closed 5 reviewer-pass-2 gaps (mostly)
  - 1.4 (2026-04-23) — closed reviewer-pass-3 findings (N5 inline schema, Gap 6 validator extension, NEW-4 PR1 T1 extension, trade-offs documented)
  - 1.5 (2026-04-23) — closed reviewer-pass-4 findings (split off /agent-evaluator skill, hash migration, rollback rm fix, NN block update)
  - 1.6 (2026-04-23) — closed reviewer-pass-5 cleanup findings: (a) PR1 task list still said "Extend /skill-evaluator" — corrected to "NEW /agent-evaluator skill" matching §4 EVALS body text; (b) added `agent-evaluator` to REGISTRY task list (was missing); (c) `/agent-evaluator` confirmed in PR1 (not PR2) so it's available for evals gate that runs in PR2 per REQ-M033
- References:
  - `docs/QA-AGENT-ECOSYSTEM-RESEARCH-2026-04-22.md` (peer architectures: nirarad, fugazi)
  - `docs/specs/workflow-master-agents-spec.md` (T0/T1/T2 conventions)
  - `core/.claude/rules/agent-orchestration.md` (4-tier model + 11 constraints)
  - `core/.claude/rules/testing.md` (verdict authority, manifest schemas)
  - `core/.claude/rules/pattern-structure.md` (NON-NEGOTIABLE block + tool grant invariants)

---

## 1. Problem Statement

Today's test pipeline (`/test-pipeline`, `testing-pipeline-master-agent`) treats each test as a single signal: pass or fail driven by an exit code, with screenshot review only for E2E flows. Real failures are rarely so monochromatic — a checkout test can pass functionally but break the API contract, or pass the API while a screenshot reveals a broken UI. The current sequential model (`fix_loop → auto_verify → post_fix`) cannot surface these multi-signal divergences as separate, actionable verdicts, and when something fails, the human still has to read logs, decide if it's a real bug, file an Issue, then dispatch a fix.

**What goes wrong without this:**
1. **Silent regressions.** API drift slips through because the functional test mocks the API; UI regressions slip through because the assertion only checks `getByRole`, not what the screen actually looks like.
2. **One verdict, many causes.** A failure marked "broken" gives no signal about whether code, contract, or pixels are at fault — the human has to triage.
3. **Detection-to-tracked-work gap.** Real bugs surface in transient logs and disappear into the next run.
4. **Manual fix dispatch.** A failure detected at 14:00 is fixed at the developer's next free moment.

---

## 2. Chosen Approach

**Two functional + API lanes run in true parallel; a third UI/Visual lane runs in parallel with the API lane but starts after the functional lane has produced screenshots; results are joined per-test, with autonomous Issue creation and parallel fix-agent fan-out — orchestrated by two split T2 agents to honor responsibility caps.**

For every test pipeline invocation:
1. A **scout** classifies each discovered test against ALL detection rules (rules accumulate, not first-match-wins) and populates three queues plus a `tracks_required_per_test` map.
2. **`test-pipeline-agent` (T2A)** dispatches Functional + API lanes concurrently (Wave 1). Functional lane runs ALL tests including UI tests with `--capture-proof: true`, producing screenshots for the UI lane.
3. **UI/Visual lane** is dispatched as soon as the functional lane signals UI tests done. `visual-inspector-agent` reviews screenshots — never runs tests.
4. After all lanes return, T2A evaluates the JOIN per-test gate and writes the per-test report.
5. **`failure-triage-agent` (T2B, NEW)** is dispatched by T2A with the consolidated failure set. T2B owns the entire failure-triage subgraph: analyzer fan-out → issue-manager fan-out → fixer fan-out → serialize → escalation report. (This split closes the T2 responsibility-cap violation.)
6. **Parallel fix agents** fan out in batches (cap: `max_concurrent_fixers: 5`) — each invokes `/fix-issue --diff-only` against its assigned Issue. Diffs are written to disk; T2B invokes `/serialize-fixes` to apply them sequentially with `git apply --check` first, `git reset --hard HEAD` cleanup on partial failure.
7. After fixes land, T2A re-runs only affected tests through the lanes. The loop continues until green or budgets exhausted. Before declaring success, a **final full-suite pass** runs to catch collateral regressions (configurable, default on).
8. On per-test success: Issue closed with fix commit SHA. On budget exhaustion: Issues stay open with `pipeline-fix-failed` label and `/escalation-report` is invoked.
9. On GitHub-not-connected: pipeline halts with structured `{result: "BLOCKED", blocker: "GITHUB_NOT_CONNECTED"}` contract — exit code 2, never silently skipped.
10. **`testing-pipeline-master-agent` (T1) Issue-creation step is RETIRED.** All Issue creation flows through the new `github-issue-manager-agent` to eliminate the dual-system duplication risk.

### Why This Approach Over Alternatives

| Alternative considered | Why rejected |
|---|---|
| Per-test fan-out (3 agents per test) | 100 tests × 3 agents = 300 dispatches; blows budgets |
| Three per-lane analyzers | Breaks cross-lane root-cause detection |
| Mid-flight per-lane Issues | Issue churn + stale "consolidated" diagnosis |
| Watcher subagent for live event triggers | Requires polling primitive Claude Code lacks |
| Worktree-per-fixer | Worktree overhead exceeds commit-serialization cost; deferred to REQ-C001 |
| Universal-only lane owners | Wastes stack-specific testers downstream projects already have |
| UI lane runs UI tests itself with new ui-runner-agent | Violates "no new agents unless needed"; functional lane already runs UI tests |
| Single T2 owns all 9 responsibilities | Violates `agent-orchestration.md` rule 8 (max 4); split into T2A + T2B |
| Keep T1 master's Issue-creation step alongside new system | Two dedup hashes → guaranteed duplicate Issues; retire the old one |

### Peer Pattern Provenance

| Decision | Source |
|---|---|
| Confidence-gated auto-heal (0.85 threshold) | nirarad `AGENT_CONFIDENCE_THRESHOLD` |
| Deterministic regex pre-classification | nirarad's `RULE_BASED_BROKEN_LOCATOR_CONFIDENCE` (already applied 2026-04-22) |
| Playwright MCP for healer browser inspection | fugazi `playwright-test-healer.agent.md` (already applied 2026-04-22) |
| GitHub Issue auto-creation with sha256 dedup | nirarad `enableBugIssue` (extended to per-test consolidation in this spec) |
| `maxFailuresPerRun` cap | nirarad — maps to `global_retry_budget: 15` + new `max_concurrent_fixers: 5` + new `max_total_tokens: 2000000` |
| Constitution / NON-NEGOTIABLE inlined per agent | fugazi (already applied 2026-04-22; new agents in this spec inherit) |

---

## 3. Design Sections

### 3.1 Track-Required Detection (Scout Phase)

The `test-scout-agent` (T3, existing) is extended to classify each discovered test by which tracks apply. **All detection rules run for every test; results accumulate (not first-match-wins).** A test in `tests/api/` that imports Playwright appears in BOTH the API queue AND the UI queue. (Closes reviewer Gap 9.)

| Track | Required when (any rule matches) |
|---|---|
| **Functional** | Always — every test runs the functional lane |
| **API** | Test path matches `**/tests/api/**`, `**/tests/integration/**`, `**/tests/contract/**` OR test imports an HTTP client (`httpx`, `requests`, `axios`, `node-fetch`, `supertest`, `pact`, `@pact-foundation/pact`) OR file declares `@pytest.mark.api` / `describe.api` |
| **UI** | Test imports a UI test framework (full list per `core/.claude/rules/testing.md` § "UI Test Classification": Playwright, Selenium, Cypress, Detox, Maestro, Espresso, Compose Test, Flutter Test, Puppeteer, WebdriverIO) OR matches `visual-tests.yml`'s `ui_test_patterns.include` glob |

**Override:** `core/.claude/config/test-track-overrides.yml` may map test paths → required tracks (escape hatch).

**State ownership (closes G3 from self-review):** `test-pipeline-agent` (T2A) owns its own sub-orchestrator state at `.workflows/testing-pipeline/sub/test-pipeline.json`. T1 owns `.workflows/testing-pipeline/state.json` and may READ T2A's sub-state but MUST NOT write to it. Honors `agent-orchestration.md` rule 6.

**Schema versioning (closes reviewer Gap 7 + N4):** state schema bumps from `1.0.0` → `2.0.0` for the three-queue shape. Migration policy:
- Every agent reading state files in the `.workflows/testing-pipeline/` namespace MUST check `schema_version`. If major version differs, abort with structured error `STATE_SCHEMA_INCOMPATIBLE`.
- New agents in this spec only read/write `2.0.0+`.
- Existing agents in the namespace (T1 master's aggregator, `test-pipeline-agent` standalone mode legacy path) get migration shims in their MODIFY tasks: detect `1.0.0` and upgrade in place by re-running scout to populate the new queue shape.
- **`e2e-conductor-agent` is EXEMPT from this migration** — it reads/writes its own state file at `.workflows/e2e/state.json` (different namespace from `.workflows/testing-pipeline/`), so the schema version check does not apply to it. Earlier v1.2 spec text mentioning e2e-conductor "ignoring" the schema was contradictory with the abort policy; corrected here to a clean exemption. `e2e-conductor-agent` is NOT added to the MODIFY task list.
- The cleanup step in T1 wipes state files on standalone INIT, so projects mid-run during deploy lose state — acceptable; documented in CHANGELOG.

T2A's sub-state file shape:

```json
{
  "schema_version": "2.0.0",
  "owner": "test-pipeline-agent",
  "run_id": "2026-04-23T14-30-00Z_abc1234",
  "queues": {
    "functional": ["tests/test_a.py::ta", ...],
    "api":        ["tests/api/test_users.py::tu", ...],
    "ui":         ["tests/e2e/test_checkout.py::tc", ...]
  },
  "tracks_required_per_test": {
    "tests/test_a.py::ta": ["functional"],
    "tests/api/test_users.py::tu": ["functional", "api"],
    "tests/api/test_widget.py::tw": ["functional", "api", "ui"],
    "tests/e2e/test_checkout.py::tc": ["functional", "ui"]
  }
}
```

**Queue overflow handling (closes G15 from self-review):** queues with >1000 entries are written to sidecar files `.workflows/testing-pipeline/sub/queues/{lane}.json`; main state file references via `{"sidecar": "queues/functional.json", "count": 1234}`.

### 3.2 Lane Owner Selection (Stack-Aware with Universal Fallback)

T2A reads project stack via existing detection (same as `bootstrap.py` STACK_PREFIXES + `recommend.py` DEP_PATTERN_MAP):

| Lane | FastAPI | Bun/Elysia | Vue/Nuxt | Android | React Native | Flutter | Generic fallback |
|---|---|---|---|---|---|---|---|
| Functional (runs ALL tests including UI w/ `--capture-proof`) | `tester-agent` + `/fastapi-run-backend-tests` | `tester-agent` + `/bun-elysia-test` | `tester-agent` + `/vue-test` | `tester-agent` + `/android-run-tests` | `tester-agent` + `/react-native-e2e` | `tester-agent` + `/flutter-e2e-test` | `tester-agent` + `/pytest-dev` ∨ `/jest-dev` ∨ `/vitest-dev` |
| API (independent endpoint validation + contract checks) | `fastapi-api-tester-agent` (extended: `Skill` tool grant + invokes `/contract-test`) | `tester-agent` + `/contract-test` + `/bun-elysia-test` | `tester-agent` + `/contract-test` + `/middleware-test` | `tester-agent` + `/contract-test` | `tester-agent` + `/contract-test` | `tester-agent` + `/contract-test` | `tester-agent` + `/contract-test` + `/integration-test` |
| UI / Visual (post-functional review of screenshots — never runs tests) | `visual-inspector-agent` + `/verify-screenshots` (universal across all stacks) | (same) | (same) | (same) | (same) | (same) | (same) |

**No new agent per stack.** Universal `tester-agent` is the fallback.

**Tool grant updates (closes self-review G5 + reviewer Gap 3):**

| Agent | Current tools | Required tools | Rationale |
|---|---|---|---|
| `tester-agent` | (verify) | Must include `Skill` (already does) | Invokes test-runner skills |
| `fastapi-api-tester-agent` | `["Read", "Grep", "Glob", "Bash"]` | Add `"Skill"` | New: invokes `/contract-test` |
| `test-healer-agent` | NO `tools:` field declared | Add explicit `tools: "Bash Read Write Edit Grep Glob Skill"` | Currently relies on Claude Code default; default may exclude `Skill` → silent collapse on `Skill('fix-issue')` |
| `test-failure-analyzer-agent` | (verify) | Must include `Read` and `Bash`; verify `Skill` if it invokes any | Read failure data; potential skill invocation for evidence gathering |
| `visual-inspector-agent` | (verify) | Must include `Read` (multimodal) and `Skill` | Invokes `/verify-screenshots` |
| `github-issue-manager-agent` (NEW) | n/a | `"Bash Read Skill"` | Invokes `/create-github-issue`, runs `gh` checks |
| `failure-triage-agent` (NEW T2B) | n/a | `"Agent Bash Read Write Edit Grep Glob Skill"` | T2 dispatcher — needs `Agent` tool to fan out to T3 workers |

**`tester-agent` extension also requires (closes reviewer Gap 2):**
1. Add `## NON-NEGOTIABLE` block (currently absent — reviewer confirmed)
2. Inside, declare verdict authority by lane:
   - **`lane=functional` for non-UI tests:** exit code is authoritative (existing behavior)
   - **`lane=functional` for UI tests:** screenshot is authoritative (existing per testing.md)
   - **`lane=api`:** exit code is authoritative ONLY if `/contract-test` is also invoked AND returns PASSED. If `/contract-test` is unavailable in the project, the API lane verdict is `NEEDS_CONTRACT_VALIDATION` (treated as FAILED for gating with category `INFRASTRUCTURE`) — this prevents broken contracts from passing because exit code says OK
3. Inside, declare `lane` parameter is mandatory for new dispatch context

### 3.3 Lane Execution Model (Closes self-review G1)

**Wave 1 — Functional + API in parallel.** T2A dispatches both in a single Agent() message:

```
T2A dispatches in one message:
  Agent(subagent_type=tester-agent OR stack-specific functional owner,
        prompt=functional lane prompt with --capture-proof:true, lane=functional)
  Agent(subagent_type=fastapi-api-tester-agent OR tester-agent,
        prompt=API lane prompt, lane=api)
```

Functional lane runs every test in the project including UI tests with `--capture-proof: true`. API lane runs only tests in `api_queue`. The two lanes touch disjoint test sets at the API level — they race only for system resources.

**Wave 2 — UI/Visual lane.** Dispatched after Wave 1 returns (or, optimization REQ-S006: as soon as functional lane writes `test-results/functional.ui-tests-complete.flag` checkpoint). UI lane reads `test-evidence/{run_id}/manifest.json` and reviews each screenshot for tests in `ui_queue`.

**Net pipeline time** ≈ max(Functional, API) + UI. UI is typically <30s (review-only) vs minutes for the lanes that produced its inputs.

Each lane:
- Reads its queue from T2A's sub-state file (or sidecar if >1000 tests)
- Runs/reviews tests in its queue
- Appends per-test progress to `test-results/{lane}.jsonl`
- Writes final batch report to `test-results/{lane}.json`
- Returns structured contract: `{lane, tests_processed, passed, failed, failures: [...], duration_seconds, retry_budget_consumed}`

**Lane skip rule:** if a queue is empty, T2A does not dispatch that lane (synthetic skip result).

#### 3.3.1 Intra-Lane Parallelism (Closes self-review G14)

Cross-lane parallelism is what this spec orchestrates. Intra-lane parallelism delegates to the test runner:

| Functional lane runner | Native parallelism flag |
|---|---|
| pytest | `pytest -n auto` (requires `pytest-xdist`) |
| jest | `jest --maxWorkers=50%` |
| vitest | `vitest --pool=threads --poolOptions.threads.maxThreads=8` |
| Gradle (Android) | `--parallel` |
| Bun test | `bun test` (parallel by default) |

Configurable via `lanes.functional.intra_lane_parallelism: auto | <int> | 1 (off)`. UI lane processes screenshots sequentially in `visual-inspector-agent`.

### 3.4 JOIN + Per-Test Gate Evaluation

After all dispatched lanes return, T2A evaluates the per-test gate:

```python
required = tracks_required_per_test[test_id]
verdict = ALL(lane_results[lane][test_id] == PASSED for lane in required)
```

T2A produces per-test report (Markdown) at `test-results/per-test-report.md` and end-of-run console summary (formats as in v1.1; unchanged).

T2A then dispatches `failure-triage-agent` (T2B) with the consolidated failure set (see §3.5).

### 3.5 Failure Triage (NEW T2B `failure-triage-agent` — Closes Reviewer Gap 6)

To honor `agent-orchestration.md` rule 8 (max 4 responsibilities per orchestrator), the failure-handling subgraph is extracted from T2A into a sibling T2 agent.

**`failure-triage-agent` (T2B, NEW):**

```yaml
---
name: failure-triage-agent
description: >
  Process the consolidated failure set from `test-pipeline-agent` (T2A) for the
  three-lane test pipeline. Owns analyzer fan-out, Issue creation fan-out,
  fixer fan-out, diff serialization, and escalation report. Dispatches T3
  workers (analyzer, issue-manager, healer) and invokes utility skills
  (`/serialize-fixes`, `/escalation-report`). Returns the triage outcome
  (issues_created, fixes_applied, fixes_pending) to T2A so T2A can re-verify.
tools: "Agent Bash Read Write Edit Grep Glob Skill"
model: inherit
color: orange
version: "1.0.0"
---

## NON-NEGOTIABLE
1. **Single triage owner.** All failure analysis, Issue creation, and fix dispatching flow through this agent — never bypassed by T2A.
2. **Honor batched fan-out.** `max_concurrent_fixers` cap (default 5) is enforced for analyzer, issue-manager, AND fixer dispatches.
3. **Dispatch budget enforcement.** Track cumulative `Agent()` dispatch count and elapsed wall-clock minutes (proxies for cost — `tokens_used` is NOT a Claude Code subagent return field, do not assume it). If `max_total_dispatches` (default 100) OR `max_wall_clock_minutes` (default 90) exceeded, abort with structured BLOCKED contract before next batch dispatch. T2A receives the BLOCKED contract → propagates to T1 → exits code 2.
4. **Hard-fail propagation.** A single GITHUB_NOT_CONNECTED preflight failure aborts the entire triage with BLOCKED contract — does not continue with remaining failures.
```

**T2B responsibilities (5):** (1) analyzer fan-out, (2) issue-manager fan-out + fan-in coordination, (3) fixer fan-out (batched), (4) `/serialize-fixes` invocation, (5) `/escalation-report` invocation on budget exhaustion.

**T2A responsibilities (after split, 4):** (1) scout dispatch, (2) lane dispatch (Wave 1 + Wave 2) + JOIN + per-test report, (3) T2B dispatch with failure set, (4) re-verify loop + final full-suite pass.

**Acknowledged rule-8 deviation:** T2A meets the cap at 4. T2B sits at 5 — one over the rule-8 hard cap. This is an explicit, justified deviation rather than a hidden violation. Splitting T2B further would fragment the failure-triage chain (analyzer → issue-manager → fixer → serialize → escalation) into pieces that share so much context they would need to pass it back and forth, defeating the cohesion benefit of having a single triage owner. Each of T2B's 5 responsibilities is a step in one logical pipeline (triage), not 5 unrelated concerns.

**CI enforcement (closes reviewer-pass-3 finding on Gap 6):** earlier v1.3 incorrectly claimed `workflow_quality_gate_validate_patterns.py` already has an allowlist mechanism — **it does not**, and it does not check orchestrator responsibility counts at all today. Correction: this spec adds BOTH the responsibility-count check AND the allowlist mechanism to the validator as a new §4 MODIFY task. The check parses `## Core Responsibilities` (or equivalent canonical section) from each orchestrator agent body, counts top-level numbered items, and compares against rule-8 cap. The allowlist is a YAML file `core/.claude/config/orchestrator-responsibility-allowlist.yml` with one entry per known deviation:

```yaml
allowlist:
  - agent: failure-triage-agent
    responsibility_count: 5
    rule_8_cap: 4
    deviation: 1
    justification: "Triage chain (analyzer → issue-manager → fixer → serialize → escalation) is one logical pipeline; further split would fragment context-sharing"
    spec_reference: "docs/specs/test-pipeline-three-lane-spec.md#35-failure-triage-new-t2b-failure-triage-agent"
    review_quarter: "2026-Q2"   # re-review yearly
```

If any orchestrator's responsibility count exceeds rule-8 cap AND lacks an allowlist entry, the validator fails. T2B's deviation is the single inaugural entry. This makes the safety claim verifiable in CI.

For each failed test, T2B dispatches `test-failure-analyzer-agent` (extended) with all three lanes' failure data. Analyzer:
1. Applies the existing 18 deterministic regex pre-classification rules first (preserved from 2026-04-22 overhaul)
2. If no regex matches, uses LLM classification with multi-lane evidence
3. Cross-lane root cause detection: same test failed in multiple lanes → classify with combined signals
4. Returns structured contract:

```json
{
  "test_id": "tests/api/test_users.py::test_create_user",
  "failed_lanes": ["functional", "api"],
  "category": "SCHEMA_MISMATCH",
  "confidence": 0.91,
  "classification_source": "regex_rule_3" | "llm",
  "evidence_summary": "Pydantic UserCreate model expects 'full_name' but POST sends 'name'",
  "recommended_action": "AUTO_HEAL" | "ISSUE_ONLY" | "QUARANTINE" | "RETRY_INFRA"
}
```

### 3.6 Auto-Fix Authority Matrix (Unchanged from v1.1)

| Category | Lane(s) typical | Default action | Healer touches |
|---|---|---|---|
| `BROKEN_LOCATOR` | Functional, UI | AUTO_HEAL | test code (selector) |
| `TIMEOUT_TIMING` | Functional, UI | AUTO_HEAL | test code (waits) |
| `ASSERTION_ERROR` | Functional | AUTO_HEAL (conf > 0.85) | test code (assertion) |
| `IMPORT_ERROR` | Functional | AUTO_HEAL | test code (imports) |
| `MISSING_FIXTURE` | Functional | AUTO_HEAL | conftest |
| `SCHEMA_MISMATCH` | API | AUTO_HEAL (conf > 0.85) | Pydantic model / schema file |
| `BASELINE_DRIFT_INTENTIONAL` | UI | AUTO_HEAL (with `--update-baselines` flag) | baseline files |
| `FLAKY` | Any | QUARANTINE | tag with `@flaky`, log Issue, continue |
| `INFRASTRUCTURE` | Any | RETRY_INFRA (once) | nothing — re-run; on persist, escalate |
| `LOGIC_BUG` | Functional | ISSUE_ONLY | nothing — Issue created |
| `STATUS_CODE_DRIFT` | API | ISSUE_ONLY | nothing — Issue created |
| `CONTRACT_BROKEN` | API | ISSUE_ONLY | nothing — Issue created |
| `VISUAL_REGRESSION` | UI | ISSUE_ONLY | nothing — Issue created |
| `NEEDS_CONTRACT_VALIDATION` (NEW per Gap 2) | API | ISSUE_ONLY | nothing — surface that contract validation tooling is missing |

### 3.7 GitHub Issue Creation (UNIFIED — Closes Reviewer Gap 4)

**T1 master's existing Issue-creation step is RETIRED.** All Issue creation flows through the new system. The MODIFY task for `testing-pipeline-master-agent` includes deleting the inline Issue-creation step entirely and replacing it with a pointer to T2A → T2B → `github-issue-manager-agent`. Single source of truth, no dual-system duplication.

**Unified dedup hash** = sha256 of `(test_id + category + failing_commit_sha_short)` (closes reviewer-pass-2 Gap N3). The 7-char short SHA of the commit being tested is included so the same test failing for genuinely-different bugs in different commits gets separate Issues. Same commit + same test + same category = same Issue (within the 30-day window). Used by:
- New `/create-github-issue` skill
- (Retired) T1 master's Issue creation — now removed entirely

No other dedup hash exists in the system.

**Trade-off:** A test that flakes (transient infrastructure) on the same commit produces one Issue; the dedup window comments on the existing Issue with each new run_id rather than spawning duplicates. A real refactor that changes the commit SHA but introduces the same logical bug produces a NEW Issue — acceptable, because the failing commit IS different and the team likely wants visibility on the regression even if the symptom looks identical.

**New skill `/create-github-issue`** (universal, ~150 lines).

**Preflight checks (HARD FAIL on any):**

| Check | Command | Failure message |
|---|---|---|
| `gh` installed | `command -v gh` | `GITHUB_NOT_CONNECTED: gh CLI not installed. Install from https://cli.github.com/.` |
| `gh` authenticated | `gh auth status` | `GITHUB_NOT_CONNECTED: gh not authenticated. Run: gh auth login.` |
| Git remote is GitHub | `git remote get-url origin` (must contain `github.com`) | `GITHUB_NOT_CONNECTED: origin remote is not a github.com URL.` |
| Token has repo write | `gh repo view --json viewerPermission` (must be `WRITE` or `ADMIN`) | `GITHUB_NOT_CONNECTED: token lacks Issue creation permission.` |

**Pipeline-level blocker semantics (closes self-review G16):** T2B receives `GITHUB_NOT_CONNECTED` from any issue-manager → aborts triage immediately → returns `{result: "BLOCKED", blocker: "GITHUB_NOT_CONNECTED", failed_check: "<which>", remediation: "<command>"}` to T2A. T2A propagates to T1. T1:
- Prints red ANSI error: `❌ PIPELINE BLOCKED — GITHUB_NOT_CONNECTED — <remediation>`
- Writes `test-results/pipeline-blocker.json` with the structured contract
- Exits with code 2 (distinct from 1 = test failure, 0 = success)
- Does NOT delete state files (user can resume after fixing)

**Inputs to the skill, body template, labels** — unchanged from v1.1, with empty-field defaults preserved (closes G17).

**New agent `github-issue-manager-agent`** (T3, ~80 lines) — unchanged from v1.1 spec.

#### 3.7.1 T2B Issue-Manager Fan-In Coordination (Closes Reviewer Gap 1)

When T2B fans out N `github-issue-manager-agent` invocations in parallel, it must reconcile the batch return contract.

**Batch dispatch + fan-in protocol:**

```
T2B dispatches in one message (one batch of size ≤ max_concurrent_fixers):
  Agent(subagent_type=github-issue-manager-agent,
        prompt=issue_creation_prompt(test_id_1, failure_profile_1, ...))
  Agent(subagent_type=github-issue-manager-agent,
        prompt=issue_creation_prompt(test_id_2, failure_profile_2, ...))
  ... (N invocations)

Each agent returns:
  {test_id, result: "CREATED" | "DEDUPED" | "BLOCKED",
   issue_number?, issue_url?, blocker?, remediation?}

T2B aggregates the batch:
  blocked_results = [r for r in batch_results if r.result == "BLOCKED"]
  if blocked_results:
      # Partial-failure policy: ABORT entire triage on any BLOCKED
      # (per NON-NEGOTIABLE #4 in failure-triage-agent body)
      return {result: "BLOCKED",
              blocker: blocked_results[0].blocker,
              issues_created_so_far: [r.issue_number for r in batch_results if r.result == "CREATED"],
              remediation: blocked_results[0].remediation}

  for r in batch_results:
      if r.result == "CREATED" or r.result == "DEDUPED":
          state.issue_numbers[r.test_id] = r.issue_number
          state.deduped[r.test_id] = (r.result == "DEDUPED")

  proceed to next batch OR to fixer fan-out
```

**Partial-failure policy:** any single `BLOCKED` from a `GITHUB_NOT_CONNECTED` preflight aborts the whole triage. Rationale: if one preflight fails, all subsequent ones will too (same env), so continuing wastes budget and produces inconsistent partial state.

**Dedup interaction:** `DEDUPED` results are still valid `issue_number` returns; T2B treats them identically to `CREATED` for downstream fixer dispatch — except it does NOT close the existing Issue if a fixer succeeds (the existing Issue may have ongoing comments from prior runs; T2B comments instead of closing on dedup-hit fixes).

### 3.8 Parallel Fixer Fan-Out (Closes self-review G6 + Reviewer Gap 5)

#### 3.8.1 Batched Fan-Out with Hard Concurrency + Token Budgets

**Configuration:**
```yaml
concurrency:
  max_concurrent_fixers: 5
  max_concurrent_analyzers: 5
  max_concurrent_issue_managers: 5
budget:
  global_retry_budget: 15            # fix-attempt count
  max_total_dispatches: 100          # NEW: hard cap on TOTAL agent dispatches per pipeline run
  max_wall_clock_minutes: 90         # NEW: pipeline timeout budget (proxy for cost)
  warn_at_dispatch_pct: 0.75
```

**Why dispatch count + wall clock instead of token count (closes reviewer-pass-2 Gap N1):** Claude Code subagents do NOT expose `tokens_used` in their structured return contracts. The earlier v1.2 proposal `cumulative_tokens += sum(r.tokens_used for r in results)` would silently dead-zero because that field doesn't exist — making the safety valve dead code. We replace it with two **measurable** proxies T2B can actually observe:

1. **Dispatch count** — T2B increments a counter per Agent() call. Reasonable proxy for cost since each dispatch carries a roughly-bounded prompt + return.
2. **Wall clock** — T2B records a start timestamp and checks elapsed minutes before each batch. Pipeline-wide timeout cap.

Either exceeded → abort with `BLOCKED: BUDGET_EXCEEDED` contract.

**Algorithm (T2B owns):**

```python
failed_with_auto_heal = [t for t in failed_tests if t.recommended_action == "AUTO_HEAL"]

for batch in chunks(failed_with_auto_heal, size=max_concurrent_fixers):
    # Pre-batch budget check
    if dispatch_count >= max_total_dispatches:
        abort_with_contract({"result": "BLOCKED",
                             "blocker": "DISPATCH_BUDGET_EXCEEDED",
                             "dispatch_count": dispatch_count,
                             "remediation": "Increase max_total_dispatches or reduce failure batch size"})

    if elapsed_minutes() >= max_wall_clock_minutes:
        abort_with_contract({"result": "BLOCKED",
                             "blocker": "WALL_CLOCK_BUDGET_EXCEEDED",
                             "elapsed_minutes": elapsed_minutes(),
                             "remediation": "Increase max_wall_clock_minutes or pre-filter failure set"})

    results = dispatch_parallel([
        Agent(subagent_type=test-healer-agent,
              prompt=fixer_prompt(test, issue_number, commit_mode='diff_only'))
        for test in batch
    ])

    dispatch_count += len(batch)
    if dispatch_count >= max_total_dispatches * warn_at_dispatch_pct:
        emit_warning(f"Dispatch budget at {dispatch_count}/{max_total_dispatches}")

    collect(results)

return all_results
```

This algorithm uses only primitives T2B can directly observe (counter + clock). No assumed platform metadata.

Each fixer:
- Receives `{issue_number, test_id, category, evidence, commit_mode: "diff_only"}` in dispatch context
- Invokes `/fix-issue --diff-only`
- `/fix-issue --diff-only` runs analyze → plan → implement → STOP (no `/post-fix-pipeline`)
- Writes diff to `test-results/fixes/{issue_number}.diff`
- Returns `{fix_applied: bool, diff_path: str, fix_verified: bool, retries_used: int, tokens_used: int}`

### 3.9 Commit Serialization (Closes self-review G2 + G4 + G8 + Reviewer Gap 10)

#### 3.9.1 `/fix-issue` `--diff-only` Flag

`/fix-issue` skill is extended with `--diff-only` flag:

| Flag | Behavior |
|---|---|
| `--diff-only` (NEW) | Run analyze → plan → implement → STOP. Do not invoke `/post-fix-pipeline`. Write proposed changes as unified diff to `test-results/fixes/{issue_number}.diff`. |
| (default, no flag) | Existing behavior preserved — full chain including commit. |

#### 3.9.2 Healer `commit_mode` Gating

`test-healer-agent` reads `commit_mode` from dispatch context:

| `commit_mode` | Behavior |
|---|---|
| `direct` (default) | Existing behavior — commits via `/post-fix-pipeline`. Used by `/fix-loop`, `e2e-conductor-agent`, `development-loop-master-agent`. |
| `diff_only` | Writes diff to disk; T2B handles commits. Used only by new three-lane T2B. |

#### 3.9.3 Atomic Sequential Diff Application

T2B invokes new dedicated skill:

```
Skill('serialize-fixes',
      diffs=['test-results/fixes/1234.diff', 'test-results/fixes/1235.diff', ...])
```

`/serialize-fixes` algorithm (closes Reviewer Gap 10):

```bash
for diff in $diffs; do
    # Phase 1: dry-run check (atomic, never dirties tree)
    if ! git apply --check "$diff" 2>/dev/null; then
        # Conflict detected — discard diff, mark Issue
        gh issue edit "$issue_num" --add-label pipeline-fix-conflict
        rm "$diff"   # explicit discard so re-dispatch computes fresh
        record_in_state "$issue_num" "stale_diff_discarded"
        continue
    fi

    # Phase 2: real apply (only if check passed)
    if ! git apply "$diff"; then
        # Should not happen given check passed, but handle defensively
        git reset --hard HEAD   # MANDATORY cleanup on any failure between apply and commit
        gh issue edit "$issue_num" --add-label pipeline-fix-failed
        record_in_state "$issue_num" "apply_failed_after_check"
        continue
    fi

    # Phase 3: commit
    if ! git add -A && git commit -m "fix(test-pipeline): heal $test_id (#$issue_num)"; then
        # Commit failure (e.g., pre-commit hook rejected) — clean up
        git reset --hard HEAD   # MANDATORY cleanup
        gh issue edit "$issue_num" --add-label pipeline-fix-failed
        record_in_state "$issue_num" "commit_failed"
        continue
    fi

    record_in_state "$issue_num" "applied" "$commit_sha"
done

return {applied: [...], conflicted: [...], failed: [...], commits: [...]}
```

**NON-NEGOTIABLE in `/serialize-fixes` SKILL.md:**
1. ALWAYS run `git apply --check` before `git apply`. Never apply without dry-run first.
2. ALWAYS `git reset --hard HEAD` on any failure between apply and commit. Never leave a dirty working tree.
3. NEVER retain stale diffs on conflict — `rm` them so the next iteration computes fresh.
4. Process diffs in order; do not parallelize within this skill.

This closes the partial-apply corruption risk identified by the reviewer.

### 3.10 Re-Verification Loop + Final Full Pass (Closes self-review G10 + G13)

After all fix commits land (T2B returns to T2A), T2A runs:

1. Build re-run queues from `union(failed_test_ids)` only
2. Re-dispatch lanes (Wave 1 then Wave 2) with smaller queues
3. JOIN again, evaluate per-test verdicts
4. For tests now PASSED: close Issue with `gh issue close --comment "Fixed in {commit_sha}: {one-line diff summary}"`
5. For tests still FAILED: increment `retries_used` (per-test cap of 3), re-dispatch T2B with the still-failing subset (subject to global budget)
6. When global budget hits 0: ABORT — leave Issues open with `pipeline-fix-failed` label, dispatch `/escalation-report`

**Final full-suite pass before declaring success:** when affected-tests loop greens, T2A runs ONE final pass through all three lanes against the FULL test set to catch collateral regressions caused by fixes. Configurable via `final_full_suite_check: true | false` (default `true`). New failures from the final pass continue the loop (still subject to global budget).

#### 3.10.1 Retry Budget + Token Budget Accounting (Closes self-review G13 + Reviewer Gap 5)

The global `retry_budget: 15` decrements ONLY on:
- (a) Per-lane retries within a lane execution (one decrement per lane invocation, not per intra-lane retry)
- (b) Fixer dispatches that mutate files (one decrement per fixer dispatched in a batch)

Does NOT decrement: analyzer dispatches (read-only), issue-manager dispatches (Issue side-effect), re-verification lane re-dispatches (the dispatch itself), final full-suite pass (the dispatch itself).

The dispatch budget `max_total_dispatches: 100` increments on EVERY Agent() invocation by T2B (analyzer, issue-manager, fixer). When exceeded → `BLOCKED: DISPATCH_BUDGET_EXCEEDED`. Wall-clock budget `max_wall_clock_minutes: 90` tracked from T1's INIT timestamp; when exceeded → `BLOCKED: WALL_CLOCK_BUDGET_EXCEEDED`. Either contract → T2A propagates → T1 → exit code 2.

**Worked example:** 100 tests, 5 fail → 5 analyzer dispatches (count=5) + 5 issue-manager dispatches (count=10) + 5 fixer dispatches (count=15) + retry budget decrements 5 (fix attempts) + 1 re-verify lane batch (retry budget decrement 1) + 1 final full-suite pass (retry budget decrement 1) = retry budget 7/15 consumed, dispatch budget 15/100 consumed. Plenty of headroom. If failures cascade to 30 affected tests with 2 fix iterations each, dispatch budget reaches 30×3×2 = 180 → would trip `DISPATCH_BUDGET_EXCEEDED` at 100, surfacing the runaway before retry budget exhaustion.

### 3.11 Escalation Report

When budget exhausted with failures present, T2B invokes `/escalation-report` skill (NEW). Generates `test-results/escalation-report.md` (format unchanged from v1.1).

### 3.12 Live Progress (Tail-the-JSONL)

Each lane appends one JSON line per completed test to `test-results/{lane}.jsonl`. Users tail in another terminal. Main agent does not poll — documented constraint, not a bug.

### 3.13 Configuration Schema (Updated for v1.2)

Full merged `core/.claude/config/test-pipeline.yml`:

```yaml
schema_version: "2.0.0"   # bumped from 1.0.0 for three-lane refactor

pipeline:
  name: three-lane-test-pipeline
  version: "2.0.0"

lanes:
  functional:
    enabled: true
    intra_lane_parallelism: auto
    capture_proof: true
  api:
    enabled: true
    intra_lane_parallelism: auto
    invoke_skills_after_runner:
      - contract-test
      - integration-test
  ui:
    enabled: true
    runs_after: functional
    intra_lane_parallelism: 1

track_detection:
  api_path_globs:
    - "**/tests/api/**"
    - "**/tests/integration/**"
    - "**/tests/contract/**"
  api_import_signals:
    - httpx
    - requests
    - axios
    - supertest
    - pact
  override_file: "core/.claude/config/test-track-overrides.yml"
  detection_mode: accumulate   # NEW: explicit — all rules run, results accumulate (closes reviewer Gap 9)

retry:
  global_budget: 15
  per_stage_max_attempts: 3
  per_test_cap: 3

# UPDATED: separate caps per fan-out type + token budget (closes Reviewer Gap 5)
concurrency:
  max_concurrent_analyzers: 5
  max_concurrent_issue_managers: 5
  max_concurrent_fixers: 5

budget:
  max_total_dispatches: 100         # NEW: hard cap on total Agent() calls per run (measurable)
  max_wall_clock_minutes: 90        # NEW: pipeline timeout (measurable)
  warn_at_dispatch_pct: 0.75

capture_proof:
  enabled: true

contradictions:
  action: warn

auto_heal:
  BROKEN_LOCATOR: AUTO_HEAL
  TIMEOUT_TIMING: AUTO_HEAL
  ASSERTION_ERROR: AUTO_HEAL
  IMPORT_ERROR: AUTO_HEAL
  MISSING_FIXTURE: AUTO_HEAL
  SCHEMA_MISMATCH: AUTO_HEAL
  BASELINE_DRIFT_INTENTIONAL: AUTO_HEAL_WITH_FLAG
  FLAKY: QUARANTINE
  INFRASTRUCTURE: RETRY_INFRA
  LOGIC_BUG: ISSUE_ONLY
  STATUS_CODE_DRIFT: ISSUE_ONLY
  CONTRACT_BROKEN: ISSUE_ONLY
  VISUAL_REGRESSION: ISSUE_ONLY
  NEEDS_CONTRACT_VALIDATION: ISSUE_ONLY  # NEW per reviewer Gap 2

issue_creation:
  enabled: true
  preflight_required: true
  dedup_window_days: 30
  dedup_hash_fields: ["test_id", "category", "failing_commit_sha_short"]   # includes commit SHA to prevent cross-run conflation (closes Reviewer Gap N3)
  labels_default:
    - pipeline-failure
  comment_on_dedup: true
  partial_failure_policy: abort_on_first_blocked   # NEW (closes Reviewer Gap 1)

reverify:
  affected_tests_only: true
  final_full_suite_check: true

state:
  master_file: ".workflows/testing-pipeline/state.json"
  sub_file: ".workflows/testing-pipeline/sub/test-pipeline.json"
  triage_file: ".workflows/testing-pipeline/sub/failure-triage.json"   # NEW for T2B
  results_dir: "test-results"
  evidence_dir: "test-evidence"
  fixes_dir: "test-results/fixes"
  schema_compatibility:                                                   # NEW (closes Reviewer Gap 7)
    minimum_required: "2.0.0"
    on_mismatch: "abort_with_STATE_SCHEMA_INCOMPATIBLE"

cleanup_standalone_only:
  - "test-results/"
  - "test-evidence/"
  - ".pipeline/test-pipeline-state.json"
  - ".workflows/testing-pipeline/sub/"
```

### 3.14 Backward Compatibility (Unchanged from v1.1)

Skills unchanged: `/fix-loop`, `/auto-verify`, `/post-fix-pipeline`, all stack-specific test skills.

Agents have additive changes only: `commit_mode`, `lane`, multi-lane data, `Skill` tool grant — all backward-compatible.

Other workflow callers (e.g., `development-loop-master-agent`) continue to work unchanged.

### 3.15 Known Trade-offs and Implementation-Phase Decisions (Closes reviewer-pass-3 NEW-1, 2, 3, 5)

The following are documented design trade-offs identified in review but accepted as-is for v1.4. Each will be revisited if observed in production.

**TRADE-OFF-1 — Dispatch counter is a coarse cost proxy (NEW-1):** Each `Agent()` dispatch counts as 1 unit, regardless of agent type. A fixer dispatch is empirically ~10× more expensive than an analyzer dispatch (more tools, more tokens). The 100-dispatch cap is conservative on the analyzer end, generous on the fixer end. **Acceptable because:** (a) the cap is configurable per-project; (b) the wall-clock budget provides a second backstop; (c) weighted counters (fixer=5, analyzer=1) add complexity without observable cost data to validate the weights. **Revisit trigger:** if real-world runs trip dispatch budget while wall-clock budget has plenty remaining (or vice versa), introduce per-agent-type weights. Tracked as REQ-S007.

**TRADE-OFF-2 — Wall-clock budget is single pipeline-wide cap (NEW-2):** The 90-minute budget is shared between lane execution and triage. On slow CI runners, lanes can consume 60+ minutes leaving triage starved; on fast machines this is fine. **Acceptable because:** per-phase timeouts add config surface for marginal gain in normal hardware. **Revisit trigger:** if slow-CI users report triage budget exhaustion despite lane completing before 90min cap was reached, split into `max_lane_minutes` + `max_triage_minutes`. Tracked as REQ-S008.

**TRADE-OFF-3 — Squash-merge produces duplicate Issues (NEW-3):** When a feature branch's failing commit gets squash-merged to main, the post-merge SHA differs from the branch commit SHA. The dedup hash (which includes `failing_commit_sha_short`) treats them as different bugs and creates a fresh Issue at merge. **Acceptable because:** (a) the same bug failing on a new commit IS information worth tracking (the merge introduced or preserved the bug); (b) team can use Issue cross-references to link branch-Issue and main-Issue; (c) alternative (excluding SHA from hash) re-introduces the cross-run conflation problem N3 was trying to solve. **Revisit trigger:** if teams report Issue churn at PR-merge boundaries dominates manual triage time, introduce a "merge-aware dedup" mode that follows the squashed commit's parent chain. Tracked as REQ-S009.

**TRADE-OFF-4 — No automated rollback playbook for PR2 atomic switchover (NEW-5):** PR2 atomically deletes T1's inline Issue-creation step + activates T2B body. Reverting PR2's commit re-enables T1's old code, but in-flight Issues from T2B (with the new dedup hash format) won't dedupe against T1's old hash → duplicate Issues if a failure recurs post-revert. **Acceptable because:** (a) PR2 is gated by full eval suite + manual review per REQ-M033; (b) production rollback is rare and can be manually triaged; (c) building a feature-flag system to make rollback one-config-change adds permanent complexity for a one-time-event safety net. **Revisit trigger:** if PR2 ships and rollback is genuinely needed within the first month, build out the feature-flag approach for future similar switchovers. Tracked as REQ-S010. **Manual rollback procedure** documented in PR2 description: (1) revert PR2 commit; (2) close all Issues with `pipeline-failure` label created in past 24h with comment "Reverted to legacy Issue-creation system; please re-triage manually"; (3) `rm -rf .workflows/testing-pipeline/sub/` (NOT `git rm` — `.workflows/` is gitignored, so `git rm` is a no-op; correction per reviewer-pass-4 NEW gap); (4) inform team via Slack #engineering channel.

---

## 4. Files to Create / Modify

### NEW (6 files)
| File | Purpose | Approx LOC |
|---|---|---|
| `core/.claude/agents/github-issue-manager-agent.md` | T3 — wraps `/create-github-issue` | 80 |
| `core/.claude/agents/failure-triage-agent.md` | NEW T2B — owns triage subgraph (closes Reviewer Gap 6) | 200 |
| `core/.claude/skills/create-github-issue/SKILL.md` | Universal — preflight + gh issue create + sha256 dedup | 150 |
| `core/.claude/skills/serialize-fixes/SKILL.md` | T2B helper — atomic diff apply with `--check` + reset on failure | 100 |
| `core/.claude/skills/escalation-report/SKILL.md` | T2B helper — generate escalation report | 60 |
| `core/.claude/skills/agent-evaluator/SKILL.md` | NEW — agent-eval tool with 5-criterion rubric, scenario discovery from `agents/*/evals/scenarios/*.json` (separate from skill-evaluator per reviewer-pass-4) | 180 |

### MODIFY (10 files — additive changes only per §3.14)
| File | What changes |
|---|---|
| `core/.claude/agents/testing-pipeline-master-agent.md` (T1) | DELETE inline Issue-creation step entirely (closes Reviewer Gap 4). Update aggregator to read three-lane results. Keep cleanup + global retry-budget ownership. Handle BLOCKED contract from T2A → emit pipeline-blocker JSON + exit code 2. Bump state schema check to require "2.0.0+" |
| `core/.claude/agents/test-pipeline-agent.md` (T2A) | Major rewrite (responsibilities reduced from 9 → 4 by T2B split): scout dispatch → Wave 1 (functional+API parallel) → Wave 2 (UI) → JOIN → per-test report → dispatch T2B failure-triage-agent → re-verify loop → final full-suite pass. Owns sub-state file. Bump owned state schema to "2.0.0" |
| `core/.claude/agents/test-scout-agent.md` (T3) | Extend to classify per-test track requirements (accumulate semantics — closes Reviewer Gap 9); populate three queues + `tracks_required_per_test` map; sidecar files for queues >1000; bump written schema_version to "2.0.0" |
| `core/.claude/agents/tester-agent.md` (T3) | Add `## NON-NEGOTIABLE` block (closes Reviewer Gap 2); declare verdict authority by `lane` parameter (functional non-UI: exit code; functional UI: screenshot; api: contract-required else NEEDS_CONTRACT_VALIDATION). Add `lane` parameterization. Confirm `Skill` in tools |
| `core/.claude/agents/fastapi-api-tester-agent.md` (T3) | Add `Skill` to tools; extend body to invoke `/contract-test` after pytest when contract files present (no-op if absent) |
| `core/.claude/agents/visual-inspector-agent.md` (T3) | Confirm queue consumption pattern matches new `ui_queue` shape; adapt verdict file path; read `tracks_required_per_test` to filter to UI-required tests only |
| `core/.claude/agents/test-failure-analyzer-agent.md` (T3) | Multi-lane awareness — accept three lanes' failure data; cross-lane root cause detection; return `recommended_action` field; fallback to single-lane if only one lane present |
| `core/.claude/agents/test-healer-agent.md` (T3) | Add explicit `tools: "Bash Read Write Edit Grep Glob Skill"` declaration (closes Reviewer Gap 3 — currently absent → silent collapse risk on `Skill` calls). Accept optional `commit_mode` and `issue_number` in dispatch context. When `commit_mode=diff_only`, invoke `/fix-issue --diff-only` and write to `test-results/fixes/{issue_num}.diff` |
| `core/.claude/skills/fix-issue/SKILL.md` | Add `--diff-only` flag; when present, skip `/post-fix-pipeline` and write diff |
| `core/.claude/config/test-pipeline.yml` | Bump schema_version to 2.0.0; add `lanes:`, `track_detection:`, `concurrency:`, `budget:`, `auto_heal:`, `issue_creation:`, `reverify:` blocks per §3.13; add per-test cap, fixes_dir, schema_compatibility |

### REGISTRY
- `registry/patterns.json` — add entries for `github-issue-manager-agent`, `failure-triage-agent`, `create-github-issue`, `serialize-fixes`, `escalation-report`, `agent-evaluator`

### TESTS (closes self-review G20 + Reviewer Gap 8)
- Extend `scripts/tests/fixtures/playwright-demo/`:
  - Add API tests at `tests/api/test_users.py` with `SCHEMA_MISMATCH` failure
  - Add unit-test scenario with `LOGIC_BUG` failure (no auto-fix)
  - Add multi-lane scenario where same test fails in functional + API
  - Add overlap scenario: test in `tests/api/` that imports Playwright (covers accumulate semantics)
- New `scripts/tests/test_pipeline_three_lane.py` covering:
  - Track auto-detection (path + import + override + accumulate)
  - Per-test gate logic (functional only / +API / +UI / all three)
  - Cross-lane root cause detection
  - Dedup hash stability across line-number changes
  - Preflight failure → BLOCKED contract + exit 2 + state preserved
  - Conflict marking when two diffs touch same file; stale diff discarded
  - Atomic diff apply: `git apply --check` first; partial-apply failure triggers `git reset --hard HEAD`
  - Escalation report generation on budget exhaustion
  - Token budget exhaustion → BLOCKED contract
  - Backward compatibility: standalone `/fix-loop` still commits directly
  - `commit_mode` parameter gating in healer
  - Final full-suite pass catches a regression introduced by a fix
  - Issue-manager batch fan-in: partial GITHUB_NOT_CONNECTED aborts entire triage
  - Schema version mismatch: agent reading 1.0.0 state file aborts with STATE_SCHEMA_INCOMPATIBLE

### EVALS (NEW — Closes Reviewer Gap 8)

Pre-merge eval requirement for new agents and modified agents with non-trivial logic changes. Invoke via `/skill-evaluator full <agent-path>` per CLAUDE.md eval workflow.

| Agent | Eval scenarios (≥5 each) |
|---|---|
| `github-issue-manager-agent` | (1) successful create, (2) dedup hit comments existing Issue, (3) preflight failure GITHUB_NOT_CONNECTED returns BLOCKED, (4) confidence below threshold (still creates Issue with low_confidence flag), (5) QUARANTINE action (no Issue created — but only if user wants quarantine to skip Issue; spec currently has FLAKY=QUARANTINE which DOES create an Issue per matrix — this eval verifies behavior matches spec) |
| `failure-triage-agent` | (1) all-AUTO_HEAL batch succeeds end-to-end, (2) one failed test with ISSUE_ONLY skips fixer dispatch, (3) GITHUB_NOT_CONNECTED on first issue-manager aborts entire triage, (4) token-budget exhaustion mid-batch aborts, (5) cross-lane shared root cause produces single Issue, (6) batch of 12 failures fans out as 3 batches of ≤5 each |
| `test-failure-analyzer-agent` (extended) | (1) regex pre-classification short-circuits LLM, (2) multi-lane failure consolidated to one category, (3) confidence threshold gating works, (4) NEEDS_CONTRACT_VALIDATION emitted when API lane has no contract tooling, (5) backward compat: single-lane data produces same classification as before |
| `test-healer-agent` (extended) | (1) `commit_mode=direct` preserves existing commit behavior, (2) `commit_mode=diff_only` writes diff and does not commit, (3) `issue_number` propagates correctly to `/fix-issue`, (4) Skill tool grant works (no silent collapse), (5) backward compat: dispatch without `commit_mode` defaults to direct |
| `tester-agent` (extended) | (1) `lane=functional` non-UI tests use exit-code authority, (2) `lane=functional` UI tests use screenshot authority, (3) `lane=api` with contract tooling present uses combined verdict, (4) `lane=api` without contract tooling emits NEEDS_CONTRACT_VALIDATION, (5) backward compat: dispatch without `lane` defaults to legacy single-lane |

**LLM-as-judge rubric (5 criteria, 1–5 score each, pass threshold ≥4 average):**
1. Trigger reliability — does the agent fire when its conditions are met?
2. Output structure — does the return contract match the documented JSON schema?
3. NON-NEGOTIABLE adherence — are the agent's NON-NEGOTIABLE rules respected?
4. Side-effect correctness — do file writes, gh calls, git operations match expected behavior?
5. Error propagation — are failures returned as structured contracts vs swallowed?

**Pre-merge gate:** ALL new agents and modified agents must pass eval with average score ≥4 across all scenarios. Eval evidence committed to `core/.claude/agents/{agent}/evals/` (existing repo convention per CLAUDE.md "Eval Workflow" section).

**Scenario construction process (closes reviewer-pass-3 finding on N5):**

Earlier v1.3 incorrectly pointed to `core/.claude/skills/skill-evaluator/EVAL-WORKFLOW.md` claiming it defines the agent-scenario schema. **It does not** — that file defines the structural audit + behavioral evaluation workflow for SKILLS (Steps 0-8), with no `evals/scenarios/*.json` schema, no `{input, expected_contract, rubric_hints}` format, and no `--agent-path` invocation. Correction: this spec defines the agent-scenario schema INLINE here as a NEW convention (no prior repo source defines it).

**Scenario file convention (defined HERE for the first time):**
- Location: `core/.claude/agents/{agent-name}/evals/scenarios/{scenario-name}.json`
- File format:
  ```json
  {
    "scenario_name": "preflight-failure-no-gh-auth",
    "description": "GH CLI not authenticated — expect BLOCKED contract returned",
    "input": {
      "dispatch_context": { /* exact JSON the agent receives */ },
      "filesystem_setup": { /* files to create before running */ },
      "env_setup": { /* env vars to set, e.g., gh auth state */ }
    },
    "expected_contract": { /* JSON shape the agent's return must match */ },
    "rubric_hints": {
      "trigger_reliability": "Agent should detect missing gh auth on first preflight call",
      "output_structure": "Return must include result, blocker, remediation fields",
      "non_negotiable_adherence": "Must hard-fail per NN#1 — never swallow GITHUB_NOT_CONNECTED",
      "side_effect_correctness": "Must not call gh issue create when preflight fails",
      "error_propagation": "Return contract must be structured, not freeform error string"
    }
  }
  ```
- Real fixtures preferred over mocks; scenarios that need a failing test set point to `scripts/tests/fixtures/playwright-demo/` paths
- Each scenario MUST be runnable in isolation (no inter-scenario state)
- The `/skill-evaluator full <agent-path>` command needs to be EXTENDED (added to MODIFY list) to discover `evals/scenarios/*.json` files for agents (today it operates on skills only)
- Scenarios for `failure-triage-agent` consume the extended `playwright-demo` fixture per §4 TESTS

**Implication (corrected in v1.5):** the earlier v1.4 spec called this a "small extension" to `/skill-evaluator`. **That framing was wrong.** Reviewer-pass-4 spot-check confirmed `/skill-evaluator` is tightly coupled to skill-specific concepts (trigger evaluation across 20 queries, activation rate scoring, description optimization, cross-skill conflict checks, reference self-update) — none of which transfer to agent eval. The actual agent-eval surface area requires:
- Different file discovery (`agents/*/evals/scenarios/*.json` instead of `skills/*/evals/evals.json`)
- Different rubric (5 criteria from §4 EVALS instead of skill activation/coverage)
- Different scoring threshold (avg ≥4 instead of skill-specific PASS/FIX/FAIL)
- Different invocation surface (`<agent-path>` instead of `<skill-name>`)
- No reuse of skill-specific steps 0–8 from EVAL-WORKFLOW.md

Therefore v1.5 corrects this: **a NEW `/agent-evaluator` skill is created** instead of overloading `/skill-evaluator`. Cleaner separation, no dual-mode complexity. REQ-M036 split accordingly into REQ-M036 (NEW skill `/agent-evaluator`) — see §4 NEW table.

### DOCUMENTATION
- `docs/QA-AGENT-ECOSYSTEM-RESEARCH-2026-04-22.md` — append "Applied — 2026-04-23 (v2)" section with this spec's commit SHA

---

## 5. Requirement Tiers

### Must Have (MVP)
- **REQ-M001:** Three-lane execution model with functional + API parallel (Wave 1) and UI post-functional (Wave 2) [§3.3]
- **REQ-M002:** Auto-detect required tracks per test with accumulate semantics (path + import + annotation + override) [§3.1]
- **REQ-M003:** Stack-aware lane owner selection with universal `tester-agent` fallback [§3.2]
- **REQ-M004:** JOIN per-test gate; verdict combines only required-and-applicable lanes [§3.4]
- **REQ-M005:** Per-test Markdown report at `test-results/per-test-report.md` + console echo [§3.4]
- **REQ-M006:** NEW T2B `failure-triage-agent` owns the triage subgraph (T2A keeps lane orchestration) [§3.5]
- **REQ-M007:** Cross-lane-aware single analyzer with regex pre-classification preserved [§3.5]
- **REQ-M008:** New `/create-github-issue` skill with hard-fail preflight (no silent skip) [§3.7]
- **REQ-M009:** New `github-issue-manager-agent` invoked per failed test [§3.7]
- **REQ-M010:** One consolidated Issue per failed test (all 3 lanes' findings) [§3.7]
- **REQ-M011:** UNIFIED dedup hash on `(test_id + category + failing_commit_sha_short)` — T1 master's old Issue-creation step DELETED in PR2 atomic switchover [§3.7, §8]
- **REQ-M012:** Pipeline-level blocker contract on GITHUB_NOT_CONNECTED, exit code 2, state preserved [§3.7]
- **REQ-M013:** T2B issue-manager fan-in coordination with abort-on-first-blocked partial failure policy [§3.7.1]
- **REQ-M014:** Batched parallel fixer fan-out with separate caps per fan-out type [§3.8.1]
- **REQ-M015:** Measurable budget enforcement: `max_total_dispatches: 100` (counter T2B owns) AND `max_wall_clock_minutes: 90` (clock T1 owns) — both abort with structured `BLOCKED` contract on exceed. (Token-count primitive does NOT exist in Claude Code subagent returns; this spec uses observable proxies only.) [§3.8.1, §3.10.1]
- **REQ-M016:** `commit_mode: direct | diff_only` parameter on `test-healer-agent` [§3.9.2]
- **REQ-M017:** `/fix-issue --diff-only` flag — write diff, do not commit [§3.9.1]
- **REQ-M018:** New `/serialize-fixes` skill with atomic apply (`git apply --check` first, `git reset --hard HEAD` on failure, discard stale diffs) [§3.9.3]
- **REQ-M019:** Re-verification of only affected tests after each healing pass [§3.10]
- **REQ-M020:** Final full-suite pass before declaring success (configurable, default on) [§3.10]
- **REQ-M021:** Global retry budget composition with explicit accounting rules [§3.10.1]
- **REQ-M022:** On fixer success → close Issue with commit SHA; on failure → leave open + label [§3.10, §3.11]
- **REQ-M023:** New `/escalation-report` skill on budget exhaustion [§3.11]
- **REQ-M024:** Tail-able JSONL per lane at `test-results/{lane}.jsonl` [§3.12]
- **REQ-M025:** T2A owns sub-state at `.workflows/testing-pipeline/sub/test-pipeline.json` (rule 6 compliance) [§3.1]
- **REQ-M026:** State schema bumped 1.0.0 → 2.0.0 with mismatch abort policy [§3.1]
- **REQ-M027:** `fastapi-api-tester-agent` adds `Skill` tool grant + invokes `/contract-test` [§3.2]
- **REQ-M028:** `tester-agent` adds NON-NEGOTIABLE block + verdict-authority-by-lane rules [§3.2]
- **REQ-M029:** `test-healer-agent` adds explicit `tools:` declaration including `Skill` [§3.2]
- **REQ-M030:** Intra-lane parallelism via test runner (pytest-xdist, jest --maxWorkers) [§3.3.1]
- **REQ-M031:** Sidecar queue files for queues >1000 entries [§3.1]
- **REQ-M032:** Backward compatibility — `/fix-loop`, `/auto-verify`, `/post-fix-pipeline`, all stack-specific test skills unchanged [§3.14]
- **REQ-M033:** Pre-merge evals (LLM-as-judge rubric, ≥5 scenarios per new/modified agent, threshold avg ≥4) [§4 EVALS]
- **REQ-M034:** PR1 extends T1's inline Issue-creation to handle 4 new API categories (`SCHEMA_MISMATCH`, `STATUS_CODE_DRIFT`, `CONTRACT_BROKEN`, `NEEDS_CONTRACT_VALIDATION`) using existing dedup hash — prevents PR1 silent-drop window for new categories [§8]
- **REQ-M035:** Extend `workflow_quality_gate_validate_patterns.py` with orchestrator responsibility-count check + YAML allowlist (`core/.claude/config/orchestrator-responsibility-allowlist.yml`); T2B is inaugural entry [§3.5]
- **REQ-M036:** NEW skill `/agent-evaluator` (separate from `/skill-evaluator` — reviewer-pass-4 confirmed extension surface is too large for dual-mode). Discovers `core/.claude/agents/*/evals/scenarios/*.json`, runs LLM-as-judge with the 5-criterion rubric defined in §4 EVALS, scoring threshold avg ≥4. Scenario schema defined inline in §4 EVALS (NOT in EVAL-WORKFLOW.md as v1.3 incorrectly claimed) [§4 EVALS]

### Should Have (v1.1+)
- **REQ-S001:** `--only-issues N,M,...` flag to re-run pipeline against specific Issues
- **REQ-S002:** `--update-baselines` flag for `BASELINE_DRIFT_INTENTIONAL` auto-heal
- **REQ-S003:** Per-project `core/.claude/config/test-track-overrides.yml`
- **REQ-S004:** Configurable per-category auto-heal matrix in `test-pipeline.yml`
- **REQ-S005:** Post-pipeline `git rebase -i --autosquash` to consolidate fix commits
- **REQ-S006:** UI lane starts on `functional.ui-tests-complete.flag` checkpoint instead of full functional return
- **REQ-S007:** Weighted dispatch counter (fixer=5, analyzer=1, issue-manager=1) — revisit if production runs trip dispatch budget while wall-clock budget has plenty remaining (TRADE-OFF-1)
- **REQ-S008:** Per-phase wall-clock timeouts (`max_lane_minutes` + `max_triage_minutes`) — revisit if slow-CI users report triage starvation (TRADE-OFF-2)
- **REQ-S009:** Merge-aware dedup hash that follows squashed commit's parent chain — revisit if squash-merge Issue churn dominates manual triage (TRADE-OFF-3)
- **REQ-S010:** Feature-flag-based switchover for PR2 to make rollback a one-config-change rather than a code revert — revisit if PR2 rollback needed within first month (TRADE-OFF-4)

### Could Have (future)
- **REQ-C001:** Worktree-per-fixer (escape hatch for frequent same-file conflicts)
- **REQ-C002:** Slack notification on `pipeline-fix-failed` Issue creation
- **REQ-C003:** Fixer batches into a single PR (vs one commit per fix)
- **REQ-C004:** Auto-assign reviewer on `pipeline-fix-failed` Issues based on CODEOWNERS

### Won't Have (out of scope)
- **REQ-W001:** Mid-flight per-test fixer trigger before lanes return — not feasible in Claude Code dispatch model
- **REQ-W002:** Per-lane analyzer agents — breaks cross-lane root cause detection
- **REQ-W003:** Auto-fix for `LOGIC_BUG`, `VISUAL_REGRESSION`, `CONTRACT_BROKEN`, `NEEDS_CONTRACT_VALIDATION` — these stay ISSUE_ONLY by design
- **REQ-W004:** Real-time streaming progress to T1's context — Claude Code does not support this
- **REQ-W005:** UI lane runs UI tests itself — functional lane already runs UI tests with `--capture-proof`
- **REQ-W006:** Single T2 owning all 9 responsibilities — split into T2A + T2B per rule 8

---

## 6. Success Criteria

| # | Measurable outcome | How verified |
|---|---|---|
| 1 | A FastAPI project with mixed unit/API/E2E tests runs `/test-pipeline` and produces three-lane verdicts per test | Manual run + extended fixture + `test-results/per-test-report.md` |
| 2 | A test that fails functional + API gets ONE consolidated Issue, not two | `gh issue list --label pipeline-failure` after triggered failure |
| 3 | Identical failure on re-run dedups to existing Issue | sha256 hash check + Issue count assertion |
| 4 | Same test + same category at SAME commit dedups; same test + same category at DIFFERENT commit creates new Issue | Two synthetic tests: (a) re-run pipeline at same SHA → assert single Issue; (b) commit a refactor and re-run with same logical bug → assert NEW Issue (commit SHA included in hash) |
| 5 | `gh auth logout` before run → pipeline halts with `GITHUB_NOT_CONNECTED`, exit code 2, state preserved | Test scenario in `test_pipeline_three_lane.py` |
| 6 | After 3 fix iterations on same test (per-test cap), loop escalates without exhausting global budget | Synthetic always-failing test |
| 7 | Pipeline never exceeds global retry budget of 15 across all dispatches | Unit test on T2B's budget tracking with §3.10.1 worked example |
| 8 | Dispatch budget exhaustion (>100 dispatches) → `DISPATCH_BUDGET_EXCEEDED` BLOCKED contract + exit code 2 | Mock test that fans out 101+ dispatches; verify abort and structured contract |
| 8b | Wall-clock budget exhaustion (>90 min) → `WALL_CLOCK_BUDGET_EXCEEDED` BLOCKED contract + exit code 2 | Mock test with timestamp injection |
| 9 | `max_concurrent_fixers: 5` cap respected — 12 failures result in 3 batches | Mock test verifying batch chunking |
| 10 | Successful fix closes Issue with commit SHA in close comment | gh API check after run |
| 11 | Final full-suite pass catches a regression introduced by a fix | Synthetic: fix that breaks unrelated test → second Issue → loop continues |
| 12 | Two fixer diffs touching same file: first applies, second discarded with `pipeline-fix-conflict` label, fresh diff next iteration | Synthetic two-fixer same-file test |
| 13 | Standalone `/fix-loop` still commits directly (commit_mode default `direct`) | Existing `/fix-loop` test continues to pass |
| 14 | Standalone `/fix-issue` (no `--diff-only`) still runs full chain including commit | Backward compat test |
| 15 | All existing tests in `test_pipeline_e2e.py` continue to pass | CI |
| 16 | `workflow_quality_gate_validate_patterns.py` passes after registry update | CI |
| 17 | Empty Issue body fields render with placeholders | Template unit test |
| 18 | Test in overlapping path (`tests/api/` + Playwright import) appears in BOTH api_queue AND ui_queue (accumulate semantics) | New fixture + assertion |
| 19 | T2A has ≤4 owned responsibilities (rule 8 cap); T2B has 5 (1-over deviation, allowlisted in `workflow_quality_gate_validate_patterns.py` with justification) | Static review + lint check enforces allowlist entry exists |
| 20 | Old T1 Issue-creation step is fully removed (no orphan code paths) | Grep for removed callsites in T1 agent body |
| 21 | Schema version mismatch in state file → agent aborts with STATE_SCHEMA_INCOMPATIBLE | Synthetic stale-state-file test |
| 22 | All new/modified agents pass `/skill-evaluator full` with avg score ≥4 across ≥5 scenarios | Eval evidence files committed under `core/.claude/agents/{agent}/evals/` |
| 23 | Partial diff-apply failure triggers `git reset --hard HEAD` (working tree clean after) | Synthetic broken-diff test; verify `git status` clean post-failure |
| 24 | Issue-manager batch with one GITHUB_NOT_CONNECTED aborts entire triage (no remaining Issues created) | Mock test with mid-batch preflight failure |
| 25 | PR1 deployment: failures still produce GitHub Issues via T1's preserved inline step (no failure-tracking dead zone) | Run synthetic failure scenario against PR1 head; assert Issue created |
| 26 | PR2 atomic switchover: T1 deletion + T2B activation in same commit; no window with double-Issue creation | Inspect PR2 commit boundary; verify both changes in one commit |
| 27 | `e2e-conductor-agent` continues operating against its own `.workflows/e2e/state.json` namespace, unaffected by `.workflows/testing-pipeline/` schema bump | Existing e2e-conductor tests continue to pass |
| 28 | PR1 deployment: a `SCHEMA_MISMATCH` failure produces a GitHub Issue via T1's extended inline step (no silent drop for the 4 new API categories) | Trigger each of the 4 new categories against PR1 head; assert Issue created for each |
| 29 | `workflow_quality_gate_validate_patterns.py` new responsibility-count check fails when an orchestrator exceeds rule-8 cap WITHOUT an allowlist entry; passes when entry exists | Synthetic test: add a rule-violating orchestrator; assert validator fails; add allowlist entry; assert validator passes |
| 30 | NEW `/agent-evaluator` skill discovers and runs `core/.claude/agents/*/evals/scenarios/*.json` files; `/skill-evaluator` is unchanged | Run `/agent-evaluator <new-agent-path>` against `github-issue-manager-agent` evals; assert all 5 scenarios execute and produce avg score ≥4 |
| 31 | PR2 deployment: pre-merge migration script closes all open `pipeline-failure` Issues from PR1 window before PR2 ships; no duplicate Issues for cross-PR-boundary failures | Run synthetic test: create open Issue with PR1 hash format → deploy PR2 → re-trigger same failure → assert single Issue (the new PR2-format one), old Issue closed |

---

## 7. Open Questions

None at spec time — all decisions resolved across both review passes.

For transparency:
- Whether `pipeline-fix-failed` Issues should auto-assign a reviewer (REQ-C004 deferred)
- Whether escalation report should auto-trigger `/handover` for next session (deferred)
- Whether commit pollution warrants automatic squash (REQ-S005 deferred)

---

## 8. Handoff

### Recommended PR Split (Reviewer's Holistic Recommendation)

The reviewer flagged that this spec's `test-pipeline-agent` rewrite is the single highest-risk file change. To reduce blast radius, **the implementation is staged into two PRs**:

**PR1: Lanes + JOIN + T1 category extension (REQ-M001 through REQ-M005, M025–M032, M034)**
- New: `failure-triage-agent` agent body (skeleton, no triage logic yet — returns no-op contract)
- Extend: `test-scout-agent`, `tester-agent`, `fastapi-api-tester-agent`, `visual-inspector-agent`, `test-healer-agent` (tools field only)
- **Extend `testing-pipeline-master-agent` (T1) inline Issue-creation step to handle 4 NEW API categories** (`SCHEMA_MISMATCH`, `STATUS_CODE_DRIFT`, `CONTRACT_BROKEN`, `NEEDS_CONTRACT_VALIDATION`) using existing dedup hash — temporary code, replaced in PR2 (closes NEW-4)
- **Extend `workflow_quality_gate_validate_patterns.py`** to add orchestrator responsibility-count check + allowlist mechanism (closes Gap 6 properly); create `core/.claude/config/orchestrator-responsibility-allowlist.yml` with T2B's inaugural entry
- **NEW `/agent-evaluator` skill** (do NOT extend `/skill-evaluator` — different rubric, different scoring, different file format; see §4 EVALS for scenario schema and §3.5 corrected implication note). `/skill-evaluator` remains untouched.
- Major rewrite: `test-pipeline-agent` (T2A) for the lane orchestration only — NO triage dispatch yet (passes failure set to no-op T2B → falls through to T1's extended inline step)
- Update: `test-pipeline.yml` (lanes/track_detection/concurrency blocks)
- Updates: state schema bump 1.0.0 → 2.0.0
- Tests: lane execution, JOIN, per-test report, accumulate semantics, schema mismatch, T1 handles 4 new categories, validator allowlist mechanism rejects new violations

**PR1 Issue-creation behavior (closes reviewer-pass-2 Gap N2 + reviewer-pass-3 NEW-4):** T1 master's INLINE Issue-creation step is **kept ALIVE during PR1's lifetime** — it is NOT deleted in PR1. The new `/create-github-issue` skill and `github-issue-manager-agent` do not yet exist in PR1. T2A passes the failure set to the no-op T2B skeleton, which returns immediately; T2A then surfaces failures back to T1, which uses its existing Issue-creation step to produce Issues.

**T1 must be EXTENDED in PR1 to handle the 4 new API-lane categories (closes reviewer-pass-3 NEW-4):** T1's existing inline step today only handles `LOGIC_BUG` and `VISUAL_REGRESSION` (per the 2026-04-22 overhaul). PR1 introduces the API lane which can emit `SCHEMA_MISMATCH`, `STATUS_CODE_DRIFT`, `CONTRACT_BROKEN`, and `NEEDS_CONTRACT_VALIDATION`. Without extension, PR1 would silently drop Issues for these four categories — defeating the "no failure-tracking dead zone" claim. Therefore PR1's MODIFY task for `testing-pipeline-master-agent` MUST include: extend the inline Issue-creation switch to cover all 6 categories that PR1 can emit. The switch handler for the 4 new categories produces Issues using T1's existing template + `(test_id + category)` dedup hash (NOT the new commit-SHA hash — that comes in PR2 with the new system). This is a temporary T1 extension that is fully replaced in PR2 when the inline step is deleted; the temporary code lives for one PR cycle only.

The dual-system risk (Gap 4) remains absent during PR1 because T1 is the only Issue creator. The new commit-SHA dedup hash is introduced atomically with the new Issue-creation system in PR2.

**Hash transition migration (closes reviewer-pass-4 NEW-4 PARTIAL):** PR1 creates Issues with the 2-field hash `(test_id + category)`. PR2 introduces the 3-field hash `(test_id + category + failing_commit_sha_short)`. A failure that persisted across the PR1→PR2 boundary (open Issue from PR1, same failure recurs after PR2 deploys) would not dedupe — PR2's 3-field hash doesn't match PR1's 2-field hash → duplicate Issue. **Mandatory PR2 pre-merge migration step:** as part of PR2's deployment, run a one-shot script that closes all open Issues with `pipeline-failure` label created in the past 30 days (PR1's window) with comment `"Closing pre-PR2 Issue. If this failure recurs after PR2 deploys, a new Issue will be created with the v2 dedup format. Manual cross-link if needed."` Documented as a PR2 deployment checkbox in §8. Added as success criterion #31.

**PR2: Issue Creation + Auto-Fix (REQ-M006 through M024, M033)**
- New: `github-issue-manager-agent`, `/create-github-issue`, `/serialize-fixes`, `/escalation-report` skills
- Activate: `failure-triage-agent` body (was no-op skeleton in PR1)
- Extend: `test-failure-analyzer-agent` (multi-lane awareness), `test-healer-agent` (commit_mode), `/fix-issue` (--diff-only flag)
- **Atomic switchover in T1:** in the SAME commit, (a) DELETE T1's inline Issue-creation step AND (b) wire T1 to receive triage results from T2B. No window where Issues are double-created. This is the moment dual-system risk closes permanently.
- Tests: Issue creation, dedup with commit SHA, fixer fan-out, atomic diff apply, escalation, evals
- Evals: required pre-merge per REQ-M033

This split lets PR1 ship the lane infrastructure (already a substantial improvement) and validates it in real use before PR2 wires up the autonomous-fix loop.

### Implementation Sequencing (Within Each PR)

Run `/writing-plans` against this spec to produce atomic tasks. Suggested order within PR1:
1. Bump state schema (config + scout writes)
2. Extend `test-scout-agent` (track classification + accumulate)
3. Add `tester-agent` NON-NEGOTIABLE + lane parameterization
4. Add `Skill` to `fastapi-api-tester-agent` + `test-healer-agent` tools
5. Major rewrite `test-pipeline-agent` (T2A) — lanes only
6. Skeleton `failure-triage-agent` (returns no-op)
7. Tests + fixture extensions
8. Run all CI gates

Within PR2:
1. NEW `/create-github-issue` skill (universal, used by everything else)
2. NEW `github-issue-manager-agent`
3. NEW `/serialize-fixes` and `/escalation-report` skills
4. EXTEND `/fix-issue` with `--diff-only`
5. EXTEND `test-failure-analyzer-agent` for multi-lane
6. EXTEND `test-healer-agent` for `commit_mode`
7. ACTIVATE `failure-triage-agent` body (full triage subgraph)
8. DELETE T1 master's Issue-creation step
9. EVALS for all new/modified agents (REQ-M033) — gate the merge
10. Run all CI gates

After plan approval → `/executing-plans` runs the implementation; existing CI gates (validate-pr.yml + tests) verify correctness; `/skill-evaluator` gates the merge.
