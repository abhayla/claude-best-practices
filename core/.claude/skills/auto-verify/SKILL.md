---
name: auto-verify
description: >
  Run a post-change verification pipeline that maps changed files to targeted tests,
  executes via tester-agent with UI screenshot verdicts, enforces quality gates, and
  produces structured results for pipeline consumption. Does NOT fix — use /fix-loop
  for fixes, /test-pipeline for the full fix-verify-commit chain.
triggers:
  - auto-verify
  - verify my changes
  - post-change verification
  - run verification
  - verify before commit
  - verify correctness
allowed-tools: "Bash Read Grep Glob Write Skill Agent"
argument-hint: "[--files <paths>] [--range <base>..<head>] [--full-suite] [--strict-gates] [--strict-quality] [--capture-proof | --no-capture-proof] [--allow-degraded-ui]"
version: "4.5.0"
type: workflow
---

# Auto-Verify — Post-Change Verification

Verify code changes by running targeted tests, reviewing visual proof, and enforcing
quality gates. Does NOT apply fixes — fixing belongs in `/fix-loop`. **Arguments:** $ARGUMENTS

---

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--files` | git diff | Specific files to verify (overridden by `--full-suite`) |
| `--range` | — | Verify a COMMITTED range: changed files come from `git diff --name-only <base>..<head>`; the git-stash pre-existing check is replaced by a run-at-base check (see STEP 3). For committed-merge callers like loop-engineering STEP 5 (`--range <pre_merge_sha>..HEAD`). Overrides `--files`/bare-diff detection |
| `--full-suite` | false | Run full test suite regardless of risk (overrides `--files`) |
| `--strict-gates` | false | Missing upstream JSON = BLOCK (set by orchestrator) |
| `--strict-quality` | false | Treat STEP 4 quality-gate failures as BLOCKING (default: non-blocking QUALITY_GATE warning) |
| `--capture-proof` | true (from config) | Capture screenshots on every test, pass or fail |
| `--no-capture-proof` | — | Disable screenshot capture even if config says true |
| `--allow-degraded-ui` | false | Allow PASSED verdict when UI tests are mapped but not screenshot-verified (silent-degradation opt-out) |

---

## STEP 0: Gate Check — Read Upstream Results

Check if the upstream `fix-loop` stage passed:

1. If `test-results/fix-loop.json` exists, read it:
   - If `result` is `FAILED`, or `flaky_detected` is `true` → BLOCK. Exit immediately.
     (No `FLAKY` result exists — per `testing.md` flaky arrives as `FAILED` + `flaky_detected: true`.)
   - If `result` is `PASSED` or `FIXED` (and not flaky) → proceed to STEP 1.
   - Unreadable/corrupt (`UNKNOWN`): with `--strict-gates` → BLOCK ("fix-loop.json
     unreadable — cannot trust the upstream gate"); without → WARN and proceed.

2. If `test-results/fix-loop.json` does NOT exist:
   - **With `--strict-gates` and no `--range`:** BLOCK. Report: "BLOCKED: fix-loop output missing — run fix-loop first or use orchestrator."
   - **With `--range`:** a missing upstream is EXPECTED — committed-change callers
     (loop-engineering STEP 5) run VERIFY before any fix-loop — WARN and proceed;
     strictness stays on the downstream gates (NO_TESTS_FOR_CHANGE, silent-degradation).
   - **Without `--strict-gates`:** WARN: "No fix-loop results found — proceeding without gate check." Proceed to STEP 1.

```bash
case " $ARGUMENTS " in *" --strict-gates "*) STRICT_GATES=true ;; *) STRICT_GATES=false ;; esac
RANGE=$(printf '%s' "$ARGUMENTS" | sed -n 's/.*--range \([^ ]*\).*/\1/p')
if [ -f test-results/fix-loop.json ]; then
  UPSTREAM_RESULT=$(python3 -c "
import json, sys
try:
    data = json.load(open('test-results/fix-loop.json'))
    print('FLAKY_DETECTED' if data.get('flaky_detected') is True else data.get('result', 'UNKNOWN'))
except (json.JSONDecodeError, IOError) as e:
    print(f'WARN: Could not parse fix-loop.json: {e}', file=sys.stderr)
    print('UNKNOWN')
")
  if [ "$UPSTREAM_RESULT" = "FAILED" ] || [ "$UPSTREAM_RESULT" = "FLAKY_DETECTED" ]; then
    echo "BLOCKED: fix-loop reported $UPSTREAM_RESULT"
    exit 1
  fi
  if [ "$UPSTREAM_RESULT" = "UNKNOWN" ]; then
    if [ "$STRICT_GATES" = "true" ]; then
      echo "BLOCKED: fix-loop.json unreadable — cannot trust the upstream gate (--strict-gates enforced)"
      exit 1
    fi
    echo "WARN: fix-loop.json unreadable — proceeding without gate check"
  else
    echo "fix-loop result: $UPSTREAM_RESULT — proceeding"
  fi
else
  if [ "$STRICT_GATES" = "true" ] && [ -z "$RANGE" ]; then
    echo "BLOCKED: fix-loop output missing (--strict-gates enforced)"
    exit 1
  else
    echo "WARN: No fix-loop results found — proceeding without gate check"
  fi
fi
```

---

## STEP 1: Map Changes to Tests (via /regression-test)

Delegate change identification and test mapping to `/regression-test`, which
provides 2-level import graph tracing, coverage-based mapping, and risk
classification. This is the single canonical mapper for the pipeline.

**IMPORTANT:** `/regression-test` is invoked for MAPPING ONLY — it identifies
which tests to run and classifies risk, but does NOT execute the tests itself.
Test execution happens in STEP 2 via `tester-agent`. This avoids double
execution where tests run once for mapping and again for verification.

**Change detection:** with `--range <base>..<head>`, changed files come from
`git diff --name-only <base>..<head>` — committed changes (e.g. loop-engineering STEP 5's
merged diff, `--range <pre_merge_sha>..HEAD`) where the tree is clean and a bare `git diff`
would be EMPTY. Bare invocation keeps today's uncommitted-diff behavior. Thread the range into the mapper:

```
Skill("/regression-test", args="$RANGE_OR_FILES_ARG --framework auto")  # "<base>..<head>" with --range, else $FILES_ARG
```

**Fallback if `/regression-test` is not installed:** Use `git diff --name-only
<base>..<head>` (with `--range`) or `git diff --name-only` (bare) to identify
changed files, then map to tests by naming convention (`*_test.py`,
`test_*.py`, `*.test.ts`, `*.spec.ts`) and directory adjacency. Set risk to
MEDIUM (no import graph tracing available). Log: "WARN: /regression-test not
available — using fallback file-based test mapping."

After `/regression-test` completes, read `test-results/regression-test.json`:

1. Extract the affected test list and overall risk level
2. If `regression-test` result is `FAILED` with `confidence: BLOCKED`
   (test infra broken — cannot map tests) → exit with BLOCKED
3. If `regression-test` result is `FAILED` with `confidence: LOW`
   (some tests failed during mapping) → note failures but proceed to STEP 2
   (tester-agent will re-run them with full verdict rules)
4. Use the mapped test files and risk classification for STEP 2
5. If zero affected tests found → classify the change before deciding the verdict
   (a code-producing change that ran 0 tests MUST NOT report a clean PASS — that
   is a vacuous-green / shape-vs-substance pass per `output-plausibility-verification.md`
   and `dod-verbs.md`; a runner like `node --test` exits 0 on an empty suite):
   - **Changed files include source/code** (not solely docs/config/fixtures —
     i.e. any `.py/.ts/.tsx/.js/.jsx/.kt/.java/.go/.rs/.vue/.svelte/...` outside
     `docs/`):
     - **With `--strict-gates`:** write `result: "FAILED"`, `summary.total: 0`,
       `failures: [{"test": "N/A", "category": "NO_TESTS_FOR_CHANGE", "message":
       "Code changed but 0 tests cover it — cannot verify; add a test or run /fix-loop"}]`.
       This is what stops `/development-loop` committing unverified code.
     - **Without `--strict-gates`:** write `result: "PASSED"`, `summary.total: 0`,
       and a prominent `warnings: ["UNVERIFIED: code changed but 0 tests cover it"]`
       (back-compat for non-gated callers — but the warning MUST be surfaced).
   - **No code changed** (docs/config/fixtures-only, or no changed files): write
     `result: "PASSED"`, `summary.total: 0`, `warnings: ["No tests mapped to
     changed files"]` — legitimately nothing to verify. **EXCEPTION — `--range`
     with ZERO changed files:** the caller asserted a committed change exists, so
     an empty range is a wrong range / vacuous verification: under `--strict-gates`
     write `result: "FAILED"`, category `NO_TESTS_FOR_CHANGE` ("--range <range>
     produced 0 changed files"); without it, WARN prominently.
   Then skip Steps 2-3 and proceed to Step 4 (quality gates still run).

Coverage gaps flagged by `/regression-test` (source files with no mapped tests)
are reported in the final auto-verify output as warnings.

### Monorepo runner scoping (MUST — multi-stack repos)

In a monorepo with more than one test runner, the runner MUST be scoped to the
**changed sub-package**, not detected at the repo root. Detecting at root picks
the wrong runner: e.g. a `backend/`-only change in a `backend/` (pytest) +
`frontend/` (vitest) repo whose ROOT `package.json` `test` script is
`playwright test` would run the E2E suite (or nothing relevant) instead of the
backend unit tests — a false verdict.

1. Detect monorepo via standard signals: `workspaces` in root `package.json`,
   `pnpm-workspace.yaml`, `lerna.json`, `nx.json`, or multiple package manifests
   at different depths.
2. Group the changed files by their owning sub-package (nearest ancestor dir
   containing a manifest: `package.json`, `pyproject.toml`/`requirements.txt`,
   `build.gradle`, `go.mod`, `Cargo.toml`).
3. For each affected sub-package, detect and run **that package's** runner from
   **that package's directory** (e.g. `pytest tests/` in `backend/`, `vitest` in
   `frontend/`). Aggregate per-package results into the single auto-verify verdict
   (union-of-failures).
4. Only fall back to a root-level runner when changes are not confined to a
   sub-package (cross-cutting/root changes).

## STEP 2: Execute Tests (via tester-agent)

> **⛔ `--team` SET → your FIRST tool call MUST be spawning the teammates.** Before running any test
> yourself or assessing whether a team is warranted (the flag already decided that), spawn the test-area
> teammates. If you catch yourself running the suite solo or deliberating about the mechanism, STOP —
> that violates `--team`. Spawn first; let teammates run their areas; reconcile after.
>
> **`--team` mode (optional, read-only).** For a large suite that splits into **independent test
> areas** (e.g. by package / layer / suite), the execution MAY fan out as a real agent team — each
> teammate runs a disjoint test area and they share results, rather than one sequential runner.
> Read-only (no source edits → no file partition; item B N/A). A teammate's verdict is NOT
> self-accepted: a separate read-only verifier (or the lead) re-runs/inspects the raw output per
> `independent-test-verification` (doer≠checker at the teammate boundary). Self-gates on
> `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` + the anti-fake-team ground-truth check; else use the flat
> `tester-agent` path below (cheaper, the default). A small or coupled suite stays flat.
>
> **`--team` is BINDING when explicitly set:** with the flag passed AND `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`,
> you MUST spawn REAL teammate sessions and confirm the anti-fake-team gate (`~/.claude/teams/<session>/config.json`
> `members` > 1 + `TaskCompleted by=<teammate>` / `TeammateIdle teammate=<name>`); you MUST NOT fall back to flat/
> background subagents or pause to ask how to run — the flag IS the instruction. The flat default applies ONLY when
> `--team` is absent or the env var is unset.
>
> **Spawn-first (no deliberation):** spawning the test-area teammates is your FIRST action — do NOT spend
> turns planning or ground-truthing the team mechanism before spawning. Spawn the shaped teammates
> immediately, let them run their areas, then verify the anti-fake-team gate AFTER they return.

**Fallback if `tester-agent` is not installed:** Run tests directly using the
project's test runner (detect from CLAUDE.md, pyproject.toml, package.json, or
build.gradle — scoped to the changed sub-package per "Monorepo runner scoping"
above). All tests use exit-code verdicts (no screenshot verification).
Log: "WARN: tester-agent not available — running tests directly without UI
screenshot verification."

**Terminal failure if no test runner detected:** If none of CLAUDE.md test
commands, pyproject.toml, package.json, or build.gradle exist, write
`test-results/auto-verify.json` with `result: "FAILED"`,
`failures: [{"test": "N/A", "category": "INFRA_MISSING", "message": "No test
framework detected — cannot execute tests"}]` and exit.

Delegate test execution to `tester-agent`, which provides: UI test detection
(import scanning); per-test screenshot verification for UI tests (run → capture
→ AI/baseline verify → screenshot verdict); batch exit-code execution for non-UI
tests; risk-ordered execution (CRITICAL → LOW); isolated re-run of failures to
detect pollution; structured output with per-test verdict_source.

```
Agent("tester-agent", prompt="Run these tests and provide a verdict.

Test files (from /regression-test mapping):
$AFFECTED_TESTS

Risk classification:
$OVERALL_RISK

Options:
- Full suite: $FULL_SUITE
- Run ID: $RUN_ID (minted at STEP 2 entry per testing.md's run_id format {ISO-8601}_{7-char-sha}, ':' replaced with '-' for paths)

IMPORTANT — UI Test Screenshot Verification:
1. Classify each test file as UI or non-UI by scanning imports
   (see your UI Test Detection rules). If visual-tests.yml exists
   in the project root, use its patterns instead of import scanning.
2. For UI tests: execute the Per-Test Screenshot Orchestration loop —
   run one test at a time, capture screenshot, verify screenshot
   (baseline first, then text hint, then generic AI review),
   record verdict with verdict_source: 'screenshot'.
   Screenshot verification is MANDATORY and ALWAYS ON for UI tests.
3. For non-UI tests: run batch execution with exit-code verdicts,
   verdict_source: 'exit_code'.

Screenshot storage: test-evidence/{run_id}/screenshots/
  {test_name}.{pass|fail}.png

Use the project's test runner (detect from CLAUDE.md, pyproject.toml,
package.json, or build.gradle). Run targeted tests first unless
risk >= HIGH or --full-suite specified.

Return: verdict (PASSED/FAILED), test counts, failure details,
ui_test_count, screenshot manifest, per-test verdict_source.")
```

After `tester-agent` returns, COMPUTE two verdict dimensions from its per-test
results (the agent returns a single overall verdict + per-test `verdict_source`
entries; `ui_verdict`/`code_verdict` are DERIVED here, not returned fields):

| Derived Verdict | Computed From | Authoritative For |
|---------|--------|-------------------|
| `ui_verdict` | Worst per-test result with `verdict_source: "screenshot"` | UI tests |
| `code_verdict` | Worst per-test result with `verdict_source: "exit_code"` | Non-UI tests |

Then route LINEARLY — one unambiguous flow on BOTH pass and fail results:

1. Record the agent's screenshot manifest in `test-evidence/{run_id}/manifest.json`
2. ALWAYS proceed to STEP 2.5, then STEP 3 — the single verdict-assembly point
   (silent-degradation gate + override/flag union; routes to STEP 4 on PASS,
   reports on FAIL). Never jump from STEP 2 directly to STEP 4.

---

## STEP 2.5: Visual Proof Review

**For UI tests:** This step is MANDATORY and ALWAYS runs. It serves as a
confirmation pass — the tester-agent already verified each screenshot inline,
and this step batch-reviews the verdicts for consistency and catches edge cases.
`--capture-proof` / `--no-capture-proof` flags do NOT affect UI test screenshots.

**For non-UI tests:** Skip this step if `--capture-proof` is not enabled or
`--no-capture-proof` was passed. When enabled for non-UI tests, it provides
supplementary visual evidence (not authoritative).

### Sub-steps (detailed in `references/visual-proof-review.md`)

1. **2.5.1 Read Manifest** — parse `test-evidence/{run_id}/manifest.json`; skip gracefully if absent or zero screenshots (non-UI project)
2. **2.5.2 Review All Screenshots** — 100% review rate; multimodal Read each screenshot, evaluate against 8-point criteria, classify per UI/non-UI verdict-source tables
2b. **2.5.2b Substance check (shape-vs-substance)** — judge the DATA, not just the layout: placeholder/demo/seeded content rendering cleanly (fake entity names like Alpha/Beta/Test/Acme, future dates, suspiciously round hardcoded metric splits, "for MVP" fallback values) is an OVERRIDE (FAILED), never a pass — a page can render perfectly while serving fabricated data, and shape-only review is exactly what let four such incidents ship on one recorded production site. Where a rendered value is claimed to come from live data, spot-check that it plausibly joins to a source-of-truth row (see the output-plausibility-verification rule); for a dedicated pre-ship sweep run /mock-data-hunter
3. **2.5.3 Write Visual Review Results** — emit `test-evidence/{run_id}/visual-review.json` with overrides + flags; `result: FAILED` if ANY overrides exist
4. **2.5.4 Gate Impact** — FAILED overrides add to STEP 3's main failure list; PASSED proceeds normally

**Gate signal:** STEP 3 reads `visual-review.json` to incorporate overrides into its failure union. Visual review is the authoritative screenshot-signal; exit code is secondary.

See `references/visual-proof-review.md` for the full bash snippets, the 8-point
evaluation criteria, the UI/non-UI verdict classification tables, the complete
`visual-review.json` schema with override/flag examples, and STEP 3 gate-impact rules.

---

## STEP 3: Evaluate Results

Runs on EVERY path (pass and fail) after STEP 2.5 — the single verdict-assembly
point: silent-degradation gate + visual-review override/flag union. Routes to
STEP 4 on PASS; reports on FAIL.

### Verdict Logic by Test Type

| Test Type | Primary Verdict Source | Secondary Signal |
|-----------|----------------------|------------------|
| UI test | Screenshot verification (from tester-agent) | Exit code (logged, not authoritative) |
| Non-UI test | Exit code | Screenshot (if captured, supplementary only) |

### Verdict Combinations for UI Tests

| Exit Code | Screenshot Verdict | Final Result | Rationale |
|-----------|-------------------|--------------|-----------|
| PASSED | PASSED | **PASSED** | Both agree — confident pass |
| PASSED | FAILED | **FAILED** | Screenshot is authoritative — visual defect detected |
| FAILED | PASSED | **FAILED** + FLAG | Still failed (exit code indicates code issue), but flag for review — possible assertion bug or timing issue |
| FAILED | FAILED | **FAILED** | Both agree — confirmed failure |

### Decision Flow

1. **Silent-degradation gate (MANDATORY for UI tests):**
   Before declaring PASSED, verify that UI tests actually underwent screenshot
   verification. Compute: `ui_tests_mapped = count(test_files where UI framework imported)`.
   If `ui_tests_mapped > 0` AND `summary.ui_tests_screenshot_verified < ui_tests_mapped`,
   this is a silent-degradation event — tester-agent fell back to exit-code-only
   verification for UI tests. Gate outcome:
   - **Default (strict):** set `result: FAILED` with
     `category: "UI_VERIFICATION_DEGRADED"` and list the unverified tests in
     `failures[]`. Log: "BLOCKED: {N} UI tests mapped, only {M} screenshot-verified.
     Either provision tester-agent with MCP / verify-screenshots, or explicitly
     pass --allow-degraded-ui to proceed."
   - **With `--allow-degraded-ui`:** set `result: PASSED` but add a WARN to
     `warnings[]` with the list of unverified UI tests.
2. **All tests pass** (UI screenshot verdicts + non-UI exit codes, no visual
   overrides, AND silent-degradation gate satisfied) → proceed to STEP 4 (quality gates)
3. **Any test fails:**
   - Classify each failure using the test output AND verdict_source (category, file, message)
   - Check for pre-existing failures using git-stash verification (see below)
   - Report FAILED with detailed failure list including verdict_source per test
   - Do NOT attempt fixes — fixing belongs in `/fix-loop` upstream

### Pre-Existing Failure Detection

For each failing test, verify whether it's caused by our changes. **Bare
invocation (uncommitted changes)** — stash check. **`--range` (committed
changes)** — the stash check is SKIPPED: `git stash` stashes nothing on a clean
tree, so "clean state" would equal our state and a genuine regression would be
misread as pre-existing; re-run the failing test at `<base>` instead:

```bash
# bare:    git stash && <test_runner> <failing_test> && git stash pop
# --range: git worktree add /tmp/av-base <base> && (cd /tmp/av-base && <test_runner> <failing_test>); git worktree remove --force /tmp/av-base
```

"Clean state" below = the `<base>` run (range mode) or the stashed run (bare mode):

| Clean state | Our changes | Verdict | Action |
|-------------|-------------|---------|--------|
| FAILS | FAILS | Pre-existing | Note it, do not block |
| PASSES | FAILS | Our change caused it | BLOCK — report in failures |
| PASSES | PASSES | Flaky | Log, re-run to confirm |
| FAILS | PASSES | Incidental fix | Note as bonus |

---

## STEP 4: Quality Gate (if tests pass)

After all tests pass, run quality checks on changed code:

1. **Coverage diff** — verify new/changed code has ≥80% test coverage
2. **Complexity check** — no new function exceeds cyclomatic complexity 10
3. **Duplication scan** — no new code blocks duplicate existing code
4. If any quality check fails → report as QUALITY_GATE warning (non-blocking unless `--strict-quality`)

Reference: delegates to `/code-quality-gate` skill for detailed analysis.

## STEP 4A: Contract Verification (if API changed)

If changed files include API routes, endpoints, schemas, or Pydantic models:

1. Run contract tests to verify consumer-provider compatibility
2. Check if API response shapes match existing contracts
3. If contract test fails → report as CONTRACT_BREAK (blocking)

Reference: delegates to `/contract-test` skill if Pact is configured.

## STEP 4B: Performance Baseline (if perf-sensitive code changed)

If changed files match perf-sensitive paths (request handlers, database queries, serialization):

1. Run targeted performance benchmarks if baseline exists
2. Compare against baseline — flag >10% regression
3. If regression detected → report as PERF_REGRESSION warning

Reference: delegates to `/perf-test` skill if k6/Lighthouse is configured.

---

## STEP 5: Report

```
Auto-Verify: [PASSED / FAILED]
  Changed files: N
  Tests run: M
  Passed: P | Failed: F
  Visual review: N screenshots, K overrides
  Quality gate: PASSED/WARNED/SKIPPED
  Contract check: PASSED/FAILED/SKIPPED
  Perf baseline: PASSED/REGRESSED/SKIPPED
```

## STEP 6: Structured Output

Write machine-readable results to `test-results/auto-verify.json`:

```json
{
  "skill": "auto-verify",
  "timestamp": "<ISO-8601>",
  "result": "PASSED|FAILED",
  "summary": {
    "total": "<tests_run>",
    "passed": "<passed_count>",
    "failed": "<failed_count>",
    "skipped": "<skipped_count>",
    "flaky": "<flaky_count>",
    "ui_tests": "<ui_test_count>",
    "ui_tests_screenshot_verified": "<count verified via screenshot>",
    "non_ui_tests": "<non_ui_test_count>"
  },
  "change_scope": {
    "source_files": "<count from regression-test>",
    "test_files": "<count>",
    "overall_risk": "<CRITICAL|HIGH|MEDIUM|LOW>",
    "coverage_gaps": ["<files with no mapped tests>"]
  },
  "quality_gate": "PASSED|WARNED|FAILED|SKIPPED",
  "contract_check": "PASSED|FAILED|SKIPPED",
  "perf_baseline": "PASSED|REGRESSED|SKIPPED",
  "visual_review": {
    "enabled": true,
    "screenshots_reviewed": 50,
    "overrides": 1,
    "flags": 1,
    "result": "PASSED|FAILED",
    "evidence_dir": "test-evidence/{run_id}/"
  },
  "failures": [
    {
      "test": "test_name",
      "verdict_source": "screenshot|exit_code",
      "category": "VISUAL_DEFECT|ASSERTION_FAILURE|...",
      "file": "tests/test_file.py:42",
      "message": "description",
      "confidence": "HIGH|MEDIUM|LOW"
    }
  ],
  "warnings": [],
  "duration_ms": "<elapsed>"
}
```

**For UI tests:** `visual_review` is ALWAYS populated (mandatory). The `failures`
array includes `verdict_source: "screenshot"` for each UI test failure.

**For non-UI tests:** if `--capture-proof` was not enabled, emit
`"visual_review": {"enabled": false}`.

Create `test-results/` directory if it doesn't exist. This JSON is consumed by stage gates — see `testing.md` for the full schema.

**Standalone cleanup:** When running outside the pipeline (no Pipeline ID),
delete stale `test-results/auto-verify.json` before starting to prevent the
stage gate aggregator from reading results from a previous run.

---

## CRITICAL RULES

- MUST NOT apply fixes — fixing belongs in `/fix-loop`. — Why: mixing verification and fixing in one skill creates circular dependencies and unclear verdicts.
- MUST produce `test-results/auto-verify.json` on every run, even when BLOCKED or zero tests found. — Why: downstream stage gates read this file; missing file = pipeline hang.
- MUST use `result` as the canonical gate field name — never `status`, `verdict`, or `outcome`. — Why: all pipeline skills parse `result` by convention; renaming breaks the aggregator.
- MUST distinguish UI test verdicts (screenshot-authoritative) from non-UI (exit-code-authoritative). — Why: UI tests can pass exit code but fail visually (empty table, broken layout).
- MUST NOT proceed past Step 0 if upstream fix-loop reported FAILED or `flaky_detected: true`. — Why: verifying known-broken code wastes compute and produces misleading results.
- MUST route STEP 2 → 2.5 → 3 on BOTH pass and fail results — STEP 3 is the single verdict-assembly point and MUST NOT be bypassed on the pass path. — Why: skipping STEP 3 on "all passed" skips exactly the silent-degradation gate that guards a PASSED declaration.
- MUST report pre-existing failures separately from regression failures in the output. — Why: blocking on pre-existing failures prevents any new work from passing verification.
- MUST degrade gracefully if `/regression-test` or `tester-agent` are missing — use fallbacks, not hard failures. — Why: not all projects have these installed; hard failure makes the skill unusable in simpler setups.
- MUST fail the silent-degradation gate when UI tests are mapped but screenshot verification was skipped, unless `--allow-degraded-ui` was explicitly passed. — Why: a silent fallback to exit-code-only verification for UI tests reintroduces exactly the "green tests, broken UI" failure mode the dual-signal architecture exists to prevent.
- MUST scope the test runner to the **changed sub-package** in a multi-stack monorepo (run that package's runner from its dir; aggregate union-of-failures) — never detect at the repo root. — Why: a `backend/`-only change in a backend(pytest)+frontend(vitest) repo whose root `package.json` test is `playwright test` would run the wrong suite and produce a false verdict.
- MUST NOT report a clean `PASSED` for a **code-producing change that executed 0 tests** under `--strict-gates` — emit `FAILED` with category `NO_TESTS_FOR_CHANGE` instead. — Why: a runner like `node --test` exits 0 on an empty suite, so "exit 0" with zero tests is a vacuous green that lets `/development-loop` commit unverified code while claiming "verified" (shape-vs-substance, `output-plausibility-verification.md`). A docs/config-only change with 0 tests legitimately stays PASSED.
