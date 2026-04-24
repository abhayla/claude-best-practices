# Test Pipeline Downstream Verification — Plan

## 1. Meta

| Field | Value |
|---|---|
| Created | 2026-04-24 |
| Testbed | `D:\Abhay\VibeCoding\v2-pipeline-testbed` |
| Hub | `D:\Abhay\VibeCoding\claude-best-practices` (read-only from testbed) |
| Execution agent | Testbed-side Claude Code (separate session, fully autonomous) |
| Monitoring agent | Hub-side Claude Code (reads `test-plan-progress.md`) |
| Coverage scope | 2-lane (functional + UI). API lane deferred to Phase 7 unless Phase 1-6 all PASS and budget remains. |
| Budget | 3 hours wall-clock total |
| GitHub target | Real remote on `v2-pipeline-testbed` repo. Created in Phase 0.5 if missing. |

Spec under test: `docs/specs/test-pipeline-three-lane-spec.md` — §6 Success Criteria table numbers are referenced per-phase as `§6 #N`.

## 2. Prerequisites

Before Phase 0 starts, the following MUST be true. Testbed Claude verifies in Phase 0.0 (preflight):

- [ ] `node --version` → v18 or higher
- [ ] `npm --version` → resolvable
- [ ] `gh --version` → resolvable AND `gh auth status` exits 0
- [ ] Hub repo exists at the hub path AND `git -C <hub> status` works
- [ ] Testbed is a git repo (if not: `git init` and commit current files as baseline)
- [ ] Claude Code in testbed session has `/test-pipeline` skill loaded

If any fail, halt with `TEST_RUN_HALTED — PREREQ_FAILED: <which>`.

## 3. Progress Artifact Format

All runtime status lives in `<testbed>/test-plan-progress.md`, append-only. Per-phase evidence in `<testbed>/test-plan-runs/phase-{N}/`.

### Header (written once, at start of run)

```
# Test Run — {ISO-8601 UTC timestamp}

- run_id: {ISO-8601 compact, e.g. 20260424T1030Z}
- hub_commit: {git -C <hub> rev-parse HEAD}
- testbed_head: {git rev-parse HEAD}
- testbed_branch: {git rev-parse --abbrev-ref HEAD}
- gh_user: {gh api user --jq .login}
- node_version: {node --version}
- budget_minutes: 180
- issue_label: pipeline-test-run-{YYYY-MM-DD}
- started_at: {ISO-8601 UTC}
```

### Per-phase entry (append after each phase terminates)

```
## Phase {N}[.{sub}]: {name} — {ISO-8601 UTC}

- status: {STARTED | PASSED | FAILED | BLOCKED | SKIPPED}
- elapsed_seconds: {int}
- summary: {one-line human verdict}
- evidence_dir: test-plan-runs/phase-{N}/
- pass_criteria_met: {comma-separated list of criteria IDs, e.g. "P1a,P1b,P1c"}
- pass_criteria_failed: {same format, empty list if none}
- notes: {optional, free-form, ≤3 lines}
```

### Per-phase evidence directory

`test-plan-runs/phase-{N}/` contains at minimum:

- `commands.log` — stdout + stderr of every non-trivial command
- `verdict.md` — Markdown rationale: what was expected, what happened, pass/fail reasoning
- Copies of pipeline state files produced (`.pipeline/`, `.workflows/testing-pipeline/`, `test-results/`, `test-evidence/`)
- For Issue-creation phases: `gh-issues-before.json`, `gh-issues-after.json` snapshots

### Termination block (appended once, at end of run)

Successful completion:

```
## TEST RUN COMPLETE — {ISO-8601 UTC}

- total_elapsed_seconds: {int}
- passed: {count}
- failed: {count}
- blocked: {count}
- skipped: {count}
- overall: {PASS | FAIL | PARTIAL}
- issues_created: {count}
- issues_closed_at_end: {count}
- artifacts_root: test-plan-runs/
```

Early halt:

```
## TEST RUN HALTED — {ISO-8601 UTC} — {reason}

- reason_detail: {free-form}
- last_phase_attempted: {phase id}
- artifacts_root: test-plan-runs/
```

Reasons include: `BUDGET_EXHAUSTED`, `PREREQ_FAILED`, `CATASTROPHIC_ERROR`.

## 4. Autonomy Contract

1. **No user checkpoints.** Never ask a clarification question. Decide using the rules in this plan.
2. **Budget enforcement.** Track wall-clock from "started_at". Check after each phase. On cap breach, halt.
3. **Decision rules on failures:**
   - Setup/prereq failure → halt (`PREREQ_FAILED`, `CATASTROPHIC_ERROR`).
   - Phase verification failure → record evidence, mark PHASE as FAILED, continue to next independent phase.
   - Phase blocked on environment (auth, network) → mark BLOCKED, skip phases whose `depends_on` includes this, continue with the rest.
4. **Destructive authority (allowed):**
   - Commit inside the testbed repo (any branch you create).
   - Push `main` of the testbed to its own `origin` (for commit-SHA dedup testing, Phase 4).
   - `gh repo create`, `gh issue create`, `gh issue close`, `gh issue list`, `gh label create`.
   - Archive prior `test-plan-runs/` to `test-plan-runs/_archive/<timestamp>/`.
5. **Destructive authority (forbidden):**
   - Write to anything under `D:\Abhay\VibeCoding\claude-best-practices\` — that path is read-only.
   - Push to any remote that is not the testbed's own `origin`.
   - `gh auth logout` — use `GH_TOKEN=""` env-var override to simulate auth failure in Phase 5.
   - Modify `.claude/` config that you didn't provision via Phase 0 sync.
6. **Pre-flight cleanup.** On start, if testbed has uncommitted changes, commit them with message `chore: pre-pipeline-run checkpoint` and proceed. Rule 6 (ask-first-on-dirty-tree) does NOT apply during this autonomous run — the checkpoint commit is the approved substitute.
7. **Idempotent re-runs.** On start, if `test-plan-progress.md` exists from a prior run, move the whole `test-plan-runs/` directory and that file to `test-plan-runs/_archive/<prior-run_id>/` before starting fresh.
8. **Termination discipline.** After writing TERMINATE block, do not perform additional actions. Hub-side Claude monitors asynchronously — do not reach out.

## 5. Phase Catalog

### Phase 0: Re-provision from hub

**Goal:** Pull latest hub patterns (REQ-S004, C003, drift-check, prompt-logger, etc. shipped 2026-04-23 → 2026-04-24).

**Depends on:** Phase 0.0 preflight pass.

**Setup:**
1. Archive prior run artifacts (per §4 rule 7).
2. Snapshot current `.claude/sync-manifest.json` to evidence dir.

**Run:**
```bash
cd D:/Abhay/VibeCoding/claude-best-practices
PYTHONPATH=. python scripts/recommend.py \
  --local D:/Abhay/VibeCoding/v2-pipeline-testbed \
  --provision 2>&1 | tee <evidence>/commands.log
```

**Verify:**
- `.claude/sync-manifest.json` in testbed has a newer `last_sync` timestamp than archived copy.
- `.claude/agents/test-failure-analyzer-agent.md` frontmatter shows `version: 2.3.0` (REQ-S004).
- `.claude/config/test-pipeline.yml` contains `dispatch_weights:` and `max_lane_minutes:` keys (REQ-S007/S008 scaffolds).
- `.claude/hooks/prompt-logger.sh` exists (today's ship).

**Pass criteria:**
- P0a: sync-manifest timestamp advanced
- P0b: analyzer at v2.3.0
- P0c: REQ-S007/S008 scaffold keys present
- P0d: `git status` in testbed clean OR diff is only `.claude/` + `CLAUDE.md` (expected re-provision churn)

**On fail:** halt with `PREREQ_FAILED: hub provisioning did not complete`.

---

### Phase 0.5: Ensure GitHub remote exists

**Goal:** Testbed has a live GitHub remote so `github-issue-manager-agent` can create Issues.

**Depends on:** Phase 0 PASSED.

**Run:**
```bash
if ! git -C <testbed> remote get-url origin >/dev/null 2>&1; then
  cd <testbed>
  gh repo create "$(gh api user --jq .login)/v2-pipeline-testbed" \
    --private \
    --source=. \
    --remote=origin \
    --push 2>&1 | tee <evidence>/commands.log
fi
gh label create "pipeline-test-run-$(date -u +%Y-%m-%d)" \
  --color "FFD700" \
  --description "Auto-generated test-run label; safe to bulk-close" \
  --force 2>&1 | tee -a <evidence>/commands.log
```

**Pass criteria:**
- P05a: `git remote get-url origin` resolves
- P05b: `gh repo view` on the remote succeeds
- P05c: test-run label exists (idempotent `--force`)

**On fail:** halt with `PREREQ_FAILED: cannot establish GitHub remote`.

---

### Phase 1: Smoke — `DEMO_SCENARIO=pass`

**Goal:** End-to-end pipeline against a green scenario produces three-lane verdicts per test (§6 #1).

**Depends on:** Phase 0 PASSED (Phase 0.5 optional — Issue creation not exercised here).

**Run (inside Claude Code):**
Issue the slash command `/test-pipeline` with natural-language context:

> Run the full three-lane pipeline against the Playwright suite. `DEMO_SCENARIO=pass` for this run (`npx playwright test` with that env var). Report per-test verdicts.

Capture: `test-results/per-test-report.md`, `test-results/*.jsonl`, whole `.workflows/testing-pipeline/` directory.

**Pass criteria:**
- P1a: Exit state reports pipeline verdict PASS for all 7 spec files
- P1b: `per-test-report.md` shows `required_lanes`, `applicable_lanes`, and a per-lane verdict for every test
- P1c: `functional.jsonl` + `ui.jsonl` both exist; `api.jsonl` does NOT exist OR is empty (no API tests in suite — expected)
- P1d: No GitHub Issues created during this phase

**On fail:** continue to Phase 2 with FAILED marker.

---

### Phase 2: Single-lane failures — scenario matrix

**Goal:** Each failure scenario triggers the correct lane owner, category classification, and `recommended_action` from `auto_heal:` matrix (REQ-S004 live check).

**Depends on:** Phase 1 PASSED.

**Scenario table:**

| Sub | DEMO_SCENARIO | Expected category | Expected action |
|---|---|---|---|
| 2a | broken-locator | SELECTOR | AUTO_HEAL |
| 2b | timing | TIMING | AUTO_HEAL |
| 2c | visual-change | EXPECTED_CHANGE | NEEDS_REVIEW |
| 2d | logic | LOGIC_BUG | ISSUE_ONLY |
| 2e | flaky | FLAKY | QUARANTINE |
| 2f | infra | INFRASTRUCTURE | ENV_RESET |

**Run each sub-phase:** invoke `/test-pipeline` with the scenario env var set. Archive pipeline state between runs.

**Pass criteria per sub (Pk where k = 2a..2f):**
- Analyzer emits the expected `category`
- `recommended_action` matches the `auto_heal:` matrix value for that category
- `classification_source` is `regex` (short-circuit hit) for a/b/c/d/f; any value for e (flaky detection uses heuristics)
- For 2a/2b: auto-heal commit appears in `git log` after the run (commit_mode: direct)
- For 2c: pipeline exits `NEEDS_REVIEW`, no auto-fix commit
- For 2d: exactly ONE Issue created in the testbed's GitHub with the test-run label
- For 2e: test moved to `known_issues`; no fix commit; no Issue unless flake budget exceeded
- For 2f: single retry attempted, either recovers (PASS) or escalates to ISSUE

**On fail per sub:** record evidence, continue to next sub.

---

### Phase 3: Dual-lane consolidated Issue

**Goal:** A test that fails in two lanes for the same root cause produces ONE consolidated Issue, not two (§6 #2).

**Depends on:** Phase 2 completed (any status).

**Setup:** Author a synthetic failing spec that both:
1. Fails the functional lane's assertion
2. Fails the UI visual snapshot

Place it at `tests/dual-lane-synthetic.spec.ts`. Commit.

**Run:** `/test-pipeline` — expect both lanes to report FAILED for this test.

**Pass criteria:**
- P3a: Exactly ONE new Issue created in the test-run label
- P3b: Issue body contains findings from BOTH lanes (search for two lane markers in body)
- P3c: Issue title includes the test name from the synthetic spec
- P3d: `dedup_hash` is computed from `(test_id, category, failing_commit_sha_short)` — log the hash from pipeline state, not just Issue body

**On fail:** record evidence; cleanup by deleting synthetic spec.

---

### Phase 4: Dedup correctness

**Goal:** Same test + same category at SAME commit dedups to one Issue; at a DIFFERENT commit creates a new Issue (§6 #3, #4).

**Depends on:** Phase 3 PASSED (dual-lane Issue exists to dedupe against). If Phase 3 FAILED, create a fresh single-lane failure instead.

**Run:**
1. **4a (same-commit re-run):** without any commits between, invoke `/test-pipeline` again against the same scenario. Snapshot Issue count before and after.
2. **4b (different-commit re-run):** make a trivial commit to `server.js` (e.g., whitespace change, commit message: `chore: trivial change for dedup test`). Re-run pipeline. Snapshot Issue count.

**Pass criteria:**
- P4a-1: Issue count unchanged after same-commit re-run (±0)
- P4a-2: Existing Issue has a new comment or updated timestamp (evidence of "seen again" signal)
- P4b-1: Issue count increased by 1 after different-commit re-run
- P4b-2: New Issue has a different `dedup_hash` in its body from the prior Issue (commit SHA rotated into hash)

**On fail:** record evidence; continue.

---

### Phase 5: Degraded-path contracts

**Goal:** Pipeline halts cleanly on missing GitHub auth + per-test 3-iteration cap escalates without exhausting global budget (§6 #5, #6).

**Depends on:** none (independent; can run after Phase 0.5 even if Phase 1-4 fail).

#### Phase 5a: GITHUB_NOT_CONNECTED

**Run:**
```bash
GH_TOKEN="" /test-pipeline  # forces preflight to fail
```

**Pass criteria:**
- P5a-1: Exit code 2
- P5a-2: Pipeline state file contains `BLOCKED` contract with reason `GITHUB_NOT_CONNECTED`
- P5a-3: No partial Issues created (snapshot before/after match)
- P5a-4: `.workflows/testing-pipeline/` state file preserved (not cleaned)

#### Phase 5b: Per-test 3-iteration cap

**Setup:** Modify `tests/logic.spec.ts` to be always-failing (e.g., `expect(1).toBe(2)`). Commit with message `test: always-failing for budget test`.

**Run:** `/test-pipeline` and let healer loop run to cap.

**Pass criteria:**
- P5b-1: Healer made exactly 3 fix attempts on the test (count `fix_attempt_*` events in state)
- P5b-2: After cap hit, failure escalated to Issue with `pipeline-fix-failed` label
- P5b-3: Global retry budget counter (from T2B state) shows less than 15 remaining dispatches — i.e., per-test cap hit BEFORE global cap

**Cleanup:** Revert the always-failing test (`git revert HEAD`).

---

### Phase 6: Recent-ship feature regressions

**Goal:** Verify features landed 2026-04-23 → 2026-04-24 actually work in a downstream project.

**Depends on:** Phase 3 PASSED (need existing Issues to test `--only-issues`).

#### Phase 6a: REQ-S001 — `--only-issues`

**Run:** Close all but ONE of the Issues created in earlier phases. Invoke `/test-pipeline --only-issues <that-issue-number>`.

**Pass criteria:**
- P6a-1: Pipeline targeted only the test corresponding to that Issue
- P6a-2: Per-test-report has exactly 1 entry (not all 7 scenarios)

#### Phase 6b: REQ-S002 — `--update-baselines`

**Run:** Introduce a benign visual diff (modify `app/dashboard.html` header color). Invoke `/test-pipeline --update-baselines`.

**Pass criteria:**
- P6b-1: New baseline snapshots committed to `tests/visual.spec.ts-snapshots/`
- P6b-2: Visual test now PASSES on subsequent run without baseline flag

#### Phase 6c: REQ-S004 — `auto_heal:` config override

**Run:** Edit testbed's `.claude/config/test-pipeline.yml` — set `auto_heal.SELECTOR: ISSUE_ONLY`. Run `DEMO_SCENARIO=broken-locator /test-pipeline`.

**Pass criteria:**
- P6c-1: Analyzer emits `recommended_action: ISSUE_ONLY` (not AUTO_HEAL) for SELECTOR
- P6c-2: No auto-fix commit in git log; Issue created instead
- P6c-3: Restore default config after test

#### Phase 6d: REQ-C003 — Single-PR fix batching

**Run:** Trigger 2+ auto-healable failures in one pipeline run (e.g., concurrent broken-locator and timing). Enable `--fix-batch-mode` (if CLI) or equivalent config.

**Pass criteria:**
- P6d-1: Exactly ONE PR created on testbed remote containing both fixes (not two separate commits to main)
- P6d-2: PR body lists both Issues it closes

#### Phase 6e: REQ-C002 — Slack notification label

**Run:** Trigger a `pipeline-fix-failed` condition (re-use Phase 5b's always-failing scenario).

**Pass criteria:**
- P6e-1: Issue created with `pipeline-fix-failed` label
- P6e-2: Issue body contains the agent's full escalation report (not truncated)

---

### Phase 7 (DEFERRED): API lane extension

**Only runs if:** Phase 1-6 all PASSED AND remaining budget ≥ 45 minutes.

**Setup:** Extend `app/server.js` with a tiny API (`/api/health`, `/api/items`). Add `tests/api/` directory with contract tests. Add `vitest` or `node --test` runner for API unit layer.

**Covers:** §6 #18 (overlapping path accumulate semantics), §6 #28 (SCHEMA_MISMATCH, STATUS_CODE_DRIFT, CONTRACT_BROKEN, NEEDS_CONTRACT_VALIDATION categories).

**Pass criteria:** each of the 4 new API failure categories produces an Issue.

If Phase 7 is skipped (budget or prior fails), mark as SKIPPED with reason in progress file.

## 6. Run Termination

After Phase 6 (or Phase 7 if it ran) concludes, regardless of status:

### Cleanup

1. Close all Issues with the test-run label:
   ```bash
   gh issue list --label "pipeline-test-run-$(date -u +%Y-%m-%d)" --state open --json number --jq '.[].number' | \
     xargs -I {} gh issue close {} --comment "Auto-closed at end of test run"
   ```
2. Write a final `test-plan-runs/_summary.md` aggregating all phases' verdicts.
3. Do NOT delete evidence. Archived state lives under `test-plan-runs/` permanently.

### Write termination block

Per §3 format. Overall verdict:

- `PASS` = all non-deferred phases PASSED
- `PARTIAL` = ≥1 phase FAILED or BLOCKED, no CATASTROPHIC_ERROR
- `FAIL` = Phase 0 or 0.5 FAILED, OR ≥50% of Phase 1-6 sub-phases FAILED

### Final action

Write `test-plan-progress.md` termination block, then stop. Do NOT await further input.

## 7. Monitoring Contract (hub-side)

Hub Claude reads the following files, in order of cheapest-to-read:

1. `v2-pipeline-testbed/test-plan-progress.md` — authoritative status
2. `v2-pipeline-testbed/test-plan-runs/_summary.md` — only exists post-termination
3. `v2-pipeline-testbed/test-plan-runs/phase-{N}/verdict.md` — per-phase rationale on demand

Check cadence: on user request, or when user triggers `/loop 900s` with the monitoring prompt. Hub Claude does NOT modify any testbed files.

## 8. Known Limitations

- Phase 7 deferred: no API lane exercised in this testbed without additional scaffolding.
- `test-pipeline` invocation assumes the user-facing skill is exactly `/test-pipeline`. If the master slash command differs, testbed Claude should substitute `/testing-pipeline-workflow`.
- Real GitHub Issue creation means rate-limit risk on very-fast re-runs. Pipeline already has dedup — not expected to be a problem in a 3-hour budget.
- `auto-verify` in v4.0.0 has a silent-degradation gate — if it trips during Phase 1-2, expect a `--allow-degraded-ui` advisory in the output. This is informational, not a failure.
