---
name: e2e-visual-run
description: >
  Run a full Playwright E2E suite as a skill-at-T0 orchestrator with queue-based
  execution (test_queue → verify_queue → fix_queue), per-test screenshot capture,
  dual-signal visual verification (ARIA snapshot + screenshot AI diff), and
  confidence-gated auto-healing. The skill body IS the orchestrator — it runs
  at T0 and dispatches scout/tester/visual-inspector/healer workers directly
  via Agent(). Independent of /test-pipeline per spec v2.2 Q3. Playwright-only —
  NOT for Cypress/Selenium/Detox/Flutter (use native runners), one-off screenshot
  comparison (use /verify-screenshots), post-change targeted verification (use
  /auto-verify), or E2E best practices reference (use /e2e-best-practices).
triggers:
  - run e2e with screenshots
  - e2e visual verification
  - run e2e suite visually
  - visual e2e test run
  - e2e dual-signal verification
  - run e2e with auto-healing
type: workflow
allowed-tools: "Agent Bash Read Write Edit Grep Glob Skill"
argument-hint: "[section-name] [--update-baselines]"
version: "5.0.0"
---

# /e2e-visual-run — Skill-at-T0 Orchestrator (Playwright)

This skill's body is injected into the user's T0 session and executed there.
T0 dispatches queue workers (`test-scout-agent`, `tester-agent`,
`visual-inspector-agent`, `test-healer-agent`) via `Agent()` — the only
reliably-parallel dispatch in Claude Code. The deprecated `e2e-conductor-agent`
is NOT dispatched; its orchestration logic lives here.

Independent of `/test-pipeline` per spec v2.2 §7 Q3 RESOLVED. The two skills
do not share a body because they have different argument contracts and
primary callers. If both are invoked in one session, they run as two separate
T0 orchestrations with their own `run_id` scopes.

**Arguments:** `$ARGUMENTS`

---

## CLI Signature

```
/e2e-visual-run [section-name] [--update-baselines]
```

| Argument | Meaning |
|----------|---------|
| *(none)* | Full pipeline over every Playwright test |
| `<section-name>` | Restrict to tests matching the section (describe title / test title substring / `@tag` / file path glob) |
| `--update-baselines` | Baseline-update mode — capture screenshots + regenerate ARIA YAML; skip verification + healing |
| `<section-name> --update-baselines` | Baseline-update restricted to section |

---

## STEP 1: INIT

1. **Parse args.** Extract `section` (first non-flag token) and
   `update_baselines` (bool). If `--update-baselines` is set without a
   `section`, the update applies to all Playwright tests.
2. **Validate framework.** Confirm a Playwright config exists
   (`playwright.config.ts` / `.js` / `.mjs`). If not, abort with
   `NOT_PLAYWRIGHT_PROJECT` — recommend the user use their native runner
   (Cypress `cypress.config.*`, Detox `.detoxrc.*`, etc.).
3. **Read config.** `Read config/e2e-pipeline.yml` if it exists; else fall
   back to defaults: `retry_budget: 5`, `batch_size: 10`,
   `confidence_threshold_heal: 0.7`, `confidence_threshold_report: 0.5`,
   `flakiness_history_lookback_days: 7`.
4. **Generate `run_id`.** Same format as `/test-pipeline`:
   `{UTC ISO-8601}_{7-char git sha}` with `:` → `-`.
5. **Clean prior artifacts.** Remove `test-results/e2e-pipeline*.json` and
   `.workflows/e2e-visual/` from any prior run. Keep the 3 most recent
   `test-evidence/{run_id}/` directories (shared with `/test-pipeline`).
6. **Initialize state.**
   `Write .workflows/e2e-visual/state.json`:
   ```json
   {
     "schema_version": "2.0.0",
     "run_id": "<run_id>",
     "started_at": "<iso>",
     "mode": "run | update-baselines",
     "section_filter": "<string | null>",
     "queues": { "test_queue": [], "verify_queue": [], "fix_queue": [] },
     "step_status": { "INIT": "done", "SCOUT": "pending", ... },
     "retry_budget_remaining": 5,
     "expected_changes": [],
     "known_issues": [],
     "first_run_artifacts": []
   }
   ```
7. Append INIT to `.workflows/e2e-visual/events.jsonl`.

---

## STEP 2: SCOUT (E2E-specific classification)

Dispatch one scout to enumerate Playwright tests matching the filter:

```
Agent(subagent_type="test-scout-agent", prompt="""
## Mode: e2e-classify
## Run ID: <run_id>
## Framework: playwright
## Section filter: <section or null>
## State: .workflows/e2e-visual/state.json

Walk Playwright test files. For each test, record:
- file path + describe/test names
- @tags present
- baseline paths expected under the project's baseline dir

Populate state.queues.test_queue with ordered test identifiers. For queues
larger than 1000, emit sidecar .workflows/e2e-visual/test_queue.jsonl.
Return: {"gate": "PASSED|FAILED", "test_count": <int>, "sidecar": <path|null>,
         "baseline_dir": <path>, "summary": "<line>"}
""")
```

After the contract: merge counts into state. If `gate: FAILED` or `test_count == 0`,
abort with `NO_TESTS_MATCHED` + the section filter echoed back.

---

## STEP 3: Drain `test_queue` — Capture Runs

Run the Playwright suite (or filtered subset) with per-test screenshot capture.
This is a single long-running dispatch (Playwright itself parallelizes workers;
T0 does not chunk here):

```
Agent(subagent_type="tester-agent", prompt="""
## Lane: ui
## Framework: playwright
## Capture proof: true
## Run ID: <run_id>
## Queue: <queues.test_queue or sidecar>
## Output: test-results/e2e-pipeline.json + e2e-pipeline.jsonl
## Screenshots: test-evidence/<run_id>/screenshots/
## Baseline mode: <verify | update-baselines>

Run `npx playwright test` with the section filter. Capture a screenshot AND
an ARIA snapshot for every test. Write per-test records to e2e-pipeline.jsonl
in the schema defined by testing.md "Screenshot Proof Archive".

If mode=update-baselines: screenshots go to the baseline dir, not comparison.
Otherwise: screenshots and ARIA snapshots go to test-evidence/<run_id>/.

Return: {"gate": "PASSED|FAILED", "total": <n>, "passed": <n>, "failed": <n>,
         "captured_screenshots": <n>, "summary": "<line>"}
""")
```

After the contract: update state. Move every failing test id into
`queues.verify_queue`. If `mode: update-baselines`, skip STEPS 4–7 and
go to STEP 8 (report). All captured screenshots in that mode become new
baselines.

---

## STEP 4: Drain `verify_queue` — Dual-Signal Visual Verdict

Skip if `verify_queue` is empty (no failures → proceed to STEP 8 with PASSED).
Skip if `--update-baselines` mode (already jumped past).

Dispatch one visual inspector to apply dual-signal verdicts across the queue:

```
Agent(subagent_type="visual-inspector-agent", prompt="""
## Run ID: <run_id>
## Mode: verify
## Queue: <queues.verify_queue>
## Baselines: <baseline_dir from scout>
## Screenshots: test-evidence/<run_id>/screenshots/
## Thresholds: confidence_heal=<n>, confidence_report=<n>

For each test id in the queue:
- Compare captured ARIA snapshot to the baseline ARIA YAML
- Compare captured screenshot to the baseline screenshot (multimodal diff)
- Emit dual-signal verdict per spec v2 §3.2:
  * BOTH match → confirmed PASS (override test result if exit-code said FAIL)
  * BOTH diverge → confirmed FAIL
  * ARIA matches, screenshot diverges → visual regression (low confidence heal)
  * ARIA diverges, screenshot matches → semantic regression (needs review)

For each divergence, classify:
  * expected_change (intentional UI change — user needs to approve baselines)
  * regression (unintentional — needs fix)
  * known_issue (matches flakiness history in config)

Return: {
  "gate": "PASSED|FAILED",
  "verdict_per_test": { ... },
  "expected_changes": [...],
  "regressions": [...],
  "known_issues": [...],
  "summary": "<line>"
}
""")
```

After the contract:
- Write `test-evidence/<run_id>/visual-review.json` with the full verdicts.
- Move each `regression` into `queues.fix_queue`.
- Accumulate `expected_changes`, `known_issues` into state for STEP 8.

---

## STEP 5: Drain `fix_queue` — Confidence-Gated Auto-Heal

Skip if `fix_queue` is empty.

For each regression with `confidence >= confidence_threshold_heal`, dispatch
the healer. T0 chunks by `batch_size` (default 10):

```
# Per chunk, one T0 message with up-to-batch_size Agent() calls:
Agent(subagent_type="test-healer-agent", prompt="""
## Run ID: <run_id>
## Test: <test_id>
## Regression type: <selector | timing | assertion | visual>
## Analyzer output: <verdict details from STEP 4>
## Baselines: <baseline_dir>

Apply a targeted fix. Do NOT apply diffs — return a unified diff only.
T0 applies via /serialize-fixes. Retry budget: <retry_budget_remaining>.

Return: {"gate": "PASSED|FAILED", "diff": "<unified diff>", "confidence": <n>,
         "rationale": "<line>"}
""")
```

Regressions below the heal threshold go straight to the report as unhealed;
they are NOT dispatched to the healer.

### Apply healer diffs

Collect diffs from all healer contracts. If any diffs returned:

```
Skill("/serialize-fixes", args="<collected diffs>, <run_id>")
```

Decrement `retry_budget_remaining` by the number of healers dispatched.

### Re-verify after healing

If fixes were applied, re-enter STEP 3 (test_queue drain) for ONLY the
healed test subset. Loop back through STEPS 4 and 5 until:
- All healed tests confirm PASS, OR
- `retry_budget_remaining <= 0` (abort with BLOCKED → go to STEP 8)

---

## STEP 6: (reserved — intentionally not numbered in prior versions)

No-op in v5. Kept for step-number stability with external docs that reference
"STEP 7" and "STEP 8" by number.

---

## STEP 7: First-Run Artifact Detection

Before reporting, enumerate artifacts generated this run that are NOT
committed:

- New baseline files written under `baseline_dir` (for `--update-baselines`
  mode OR first-time runs with no prior baseline)
- Config edits (e.g., `playwright.config.*` updates during scout)
- Fixture files created by workers (test data, mock responses)

Store in `state.first_run_artifacts[]` with `{path, reason}`. These are
surfaced in STEP 8 for user review.

---

## STEP 8: Report

1. **Finalize state.** Write `test-results/e2e-pipeline.json` with fields
   matching `testing.md` Structured Test Output — specifically the `result`
   field MUST be `PASSED | FAILED | NEEDS_REVIEW | BLOCKED`.
   - `NEEDS_REVIEW` = any `expected_changes[]` non-empty
   - `BLOCKED` = retry budget exhausted OR scout/tester gate FAILED
2. **User-facing dashboard:**
   ```
   ============================================================
   E2E Visual Pipeline: <PASSED | FAILED | NEEDS_REVIEW | BLOCKED>
     Framework: playwright
     Mode: <run | update-baselines>
     Run ID: <run_id>
     Section filter: <section or "all">
     Tests: <total> | <passed> | <healed> | <known issues>
     Retry budget: <used>/<starting>
     Evidence: test-evidence/<run_id>/
     Visual review: test-evidence/<run_id>/visual-review.json
   ============================================================
   ```
3. **If `expected_changes` non-empty:** print the reminder
   > Run `/e2e-visual-run --update-baselines` to approve intentional visual changes.
4. **If `first_run_artifacts` non-empty:** list each file and remind
   > First-run artifacts have been created but not committed. Review via
   > `git status` and commit intentionally.
5. **If `known_issues` non-empty:** list them as informational — these tests
   failed but the failure matches a known flaky pattern in the flakiness
   history and is not treated as a regression.

---

## CRITICAL RULES

- MUST run at T0 — this skill's body is injected into the user's session; it
  MUST NOT be invoked by another agent via `Agent()`. Workers cannot dispatch
  further subagents (platform constraint).
- MUST NOT dispatch `e2e-conductor-agent` — that agent is deprecated
  (2026-04-24) as a nested-dispatch sub-orchestrator. Its logic lives here.
- MUST emit all per-chunk parallel `Agent()` calls in one T0 assistant
  message. Splitting across messages serializes dispatch.
- MUST write `test-evidence/<run_id>/visual-review.json` when STEP 4 runs —
  it is the authoritative source of truth for visual verdicts (per
  `testing.md` "Visual Review Schema"). `test-results/e2e-pipeline.json` is
  the aggregation contract; `visual-review.json` is the detail source.
- MUST NOT overwrite baselines outside `--update-baselines` mode. STEP 4
  and STEP 5 compare only.
- MUST surface `first_run_artifacts` and `expected_changes` in STEP 8 — they
  are uncommitted side-effects that need explicit user approval.
- MUST NOT decrement `retry_budget_remaining` for tests that are `known_issue` —
  those are expected-failure cases and do not consume budget.
- MUST respect `confidence_threshold_heal`: regressions below the threshold
  are reported unhealed, not dispatched to the healer.
