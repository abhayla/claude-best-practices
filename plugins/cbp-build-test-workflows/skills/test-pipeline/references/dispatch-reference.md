# /test-pipeline — Dispatch Reference

Supplementary reference for the `/test-pipeline` skill-at-T0 orchestrator.
Keep the main SKILL.md body focused on the STEP-by-STEP workflow; look here
for the tables + conventions that support it.

---

## Recommended-action dispatch matrix (STEP 6 TRIAGE)

For each analyzed failure, the analyzer returns `recommended_action`.
Fan-outs 2 (issue-manager) and 3 (fixer) are gated by this value:

| Action | Fan-out 2 (issue-manager) | Fan-out 3 (fixer) | Notes |
|--------|---------------------------|-------------------|-------|
| `AUTO_HEAL` | ✅ dispatched | ✅ dispatched | Issue created AND fix attempted |
| `AUTO_HEAL_WITH_FLAG` | ✅ dispatched | ✅ ONLY if `--update-baselines` is set | For `BASELINE_DRIFT_INTENTIONAL` category |
| `ISSUE_ONLY` | ✅ dispatched | ⏭ skipped for this failure | Logged + tracked, no fix attempt |
| `QUARANTINE` | ✅ dispatched (with "quarantined" label) | ⏭ skipped | Mark as known-flaky; don't re-run |
| `RETRY_INFRA` | ⏭ skipped (transient infra issue) | ⏭ skipped | Re-dispatch the test in STEP 7 immediately |
| `ESCALATE` | ✅ dispatched (severity=critical) | ⏭ skipped | High-severity; requires human review, no auto-fix attempt |

The analyzer's `classification_source` field (`deterministic-regex` vs
`llm-classify`) is preserved in the issue body for auditability but does
NOT change the dispatch decision.

---

## Dispatch counter accounting

The `dispatches_used` counter increments on every `Agent()` call the
orchestrator issues. It does NOT increment for:

- Inline `Skill()` calls (they don't spawn subagent sessions)
- Tool calls within a single agent's session (Bash, Read, etc.)
- STEP 8 re-dispatches that target the same queue as STEP 7 **if** the
  visual-inspector's screenshots are still valid (optimization: can reuse
  screenshots in STEP 8 Wave 2, saving 1 dispatch)

When the STEP 8 screenshot-reuse optimization fires, emit
`WAVE2_REUSE_EVIDENCE` event with the reused screenshot manifest path so
counter-reconciliation is auditable.

**Worked example (testbed Run 1, 2026-04-24):** observed
`dispatches_used=4` when the naive count expected 5:
- scout (1) + functional (1) + visual-inspector (1) = 3
- STEP 8 re-ran Wave 1+2, but Wave 2 reused the existing screenshots
  → only 1 more dispatch (the functional lane re-run)
- Total: 4, not 5 ✅

---

## Run artifact path conventions

- All paths in `state.json` and `pipeline-verdict.json` use **forward
  slashes** (`/`) regardless of OS, for portability across Windows / macOS
  / Linux project clones.

- Test names in filenames use filesystem-safe sanitization: replace any of
  `: < > " / \ | ? *` with `_` (space preserved; `.` preserved).

- `run_id` format: `{UTC ISO-8601}_{7-char git sha}` with `:` replaced by
  `-` in the filesystem form (e.g., `2026-04-25T14-06-56Z_abc1234`).
  Non-filesystem consumers (verdict JSON schemas) MAY accept the `:`-form,
  but MUST normalize to the `-`-form before writing to disk.

- Lock file path: `.workflows/testing-pipeline/.lock` (hidden file). Owner
  is the T0 skill body; STEP 1 sub-step 1a creates, STEP 9 sub-step 2a
  releases. Deleted on pipeline completion regardless of result.

- Evidence retention: at STEP 1 INIT cleanup, keep the **3 most recent**
  `test-evidence/{run_id}/` directories; delete older ones. `test-results/`
  is wiped entirely at INIT.

---

## `--only-issues N,M,P` flag resolution

When `--only-issues N,M,P` is passed, STEP 1 INIT resolves each Issue
number to a test_id:

1. Fetch Issue title: `gh issue view N --json title -q .title`
2. Issues created by the pipeline follow the title template:
   `{category}: {test_id}` (per `/create-github-issue` skill)
3. Parse `test_id` from the title
4. Pass filtered test_id list to scout's classify prompt as
   `filter: [<test_ids>]`
5. Scout returns queues narrowed to those test_ids only

All downstream steps then operate on the filtered subset. Useful for:

- Re-running after manual triage
- Reproducing a specific failure cluster
- Running a partial pipeline without full suite overhead

If any listed Issue number doesn't resolve (404 or missing title pattern):
emit `ONLY_ISSUES_RESOLUTION_WARNING` event with the unresolved list;
proceed with whatever resolved — do not BLOCK.

---

## Event taxonomy (events.jsonl)

Dispatch-start events (emitted at the Agent() call, before waiting for return):

- `SCOUT_DISPATCH`
- `WAVE1_DISPATCH_FUNCTIONAL`, `WAVE1_DISPATCH_API`
- `WAVE2_DISPATCH`
- `TRIAGE_ANALYZER_CHUNK_<i>_DISPATCH`
- `TRIAGE_ISSUE_MANAGER_CHUNK_<i>_DISPATCH`
- `TRIAGE_FIXER_CHUNK_<i>_DISPATCH`
- `VERIFY_AFFECTED_ITERATION_<n>_DISPATCH`
- `FINAL_FULL_SUITE_DISPATCH`

Completion events (emitted on contract return):

- `SCOUT_DONE`, `WAVE1_DONE`, `WAVE2_DONE`
- `TRIAGE_ANALYZER_CHUNK_<i>_DONE`, etc.
- `VERIFY_AFFECTED_ITERATION_<n>_DONE`
- `FINAL_FULL_SUITE_DONE`

Gate/guard events:

- `WAVE1_TOPOLOGY` (parallel vs serial decision)
- `LANE_SKIP` (empty queue)
- `TRIAGE_BUDGET_CHECK` (per-chunk budget guard evaluation)
- `WAVE2_REUSE_EVIDENCE` (STEP 8 optimization)

State-transition events:

- `INIT`, `JOIN_DONE`, `PIPELINE_DONE`

Failure-signal events:

- `SCOUT_FAILED`, `WAVE1_PARTIAL_EXECUTION`
- `CONFIG_MISSING`, `CONFIG_SCHEMA_GATE_FAILED`, `PIPELINE_IN_PROGRESS`
- `BUDGET_EXHAUSTED_DISPATCHES`, `BUDGET_EXHAUSTED_WALL_CLOCK`
- `RECURRENT_REGRESSION`, `BLOCKED`

Lock lifecycle:

- `LOCK_ACQUIRED` (STEP 1 sub-step 1a)
- `LOCK_RELEASED` (STEP 9 sub-step 2a)
