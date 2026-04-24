# Lessons Learned

<!-- Claude appends entries here after corrections or surprising outcomes. -->
<!-- Review at session start to avoid repeating mistakes. -->
<!-- Format: date, what went wrong, what to do instead. -->

## 2026-04-22 — Aggregator "union of failures" rule needs a superset check

**Surfaced during:** Phase H of the testing-pipeline overhaul, `test_flaky_scenario_surfaces_quarantined_issue` in `scripts/tests/test_pipeline_e2e.py`.

**What I got wrong:** In `scripts/pipeline_aggregator.py`, the verdict check
was `if failures or screenshot_failures:` — meaning a stage that reported
`result: FAILED` but provided an empty `failures[]` array (e.g., a conductor
that moved a test to `known_issues` without producing an individual failure
entry) was counted as PASSED. Top-level FAILED status was effectively
invisible to the aggregator.

**What to do instead:** The "union of failures" rule is a SUPERSET —
stage-level FAILED counts regardless of per-failure detail. The aggregator
MUST also check `any(r["result"] == "FAILED" for r in results)` and fail
the pipeline when any stage reports FAILED, even if its `failures[]` is
empty. Generalizable rule: for any aggregator that unions typed evidence,
always include a stage-level failure check as a safety net — don't trust
that every FAILED skill populates its evidence array.

**Pinned by:** `test_stage_failed_with_empty_failures_still_fails` in
`scripts/tests/test_pipeline_aggregator.py`.

## 2026-04-22 — Pinned-content tests break on consolidation; update homes, don't skip

**Surfaced during:** Phase A of the testing-pipeline overhaul. The test
`test_skill_md_version_is_3_0_0` in `test_e2e_visual_run_playwright_only.py`
asserted the old skill version and broke when the skill was consolidated
into v4.0.0. Similarly `test_pipeline_verdict_schema_in_orchestrator`
asserted the schema was in `test-pipeline-agent.md` but the schema moved
to `testing-pipeline-master-agent.md` when aggregation was centralized.

**What I did right:** Updated both tests to target the new homes
(e2e-conductor-agent for the skill content, testing-pipeline-master-agent
for the verdict schema) rather than deleting them or marking them skipped.
The tests now carry their original intent forward.

**Generalizable rule:** When content is moved between files during a
consolidation, pinned-content tests are valuable regression nets — migrate
the assertions to the new authoritative location. Deleting them loses the
regression surface; skipping them masks drift.

## 2026-04-24 — Registry hash field was dead data; wire enforcement or drop the field

**Surfaced during:** Tech-debt cleanup after REQ-S004 (analyzer v2.3.0). A
todo.md review flagged that `registry/patterns.json` had a stale hash for
`test-failure-analyzer-agent`. Checking the full registry revealed **228
of ~237 patterns** had drifted hashes — the column had been effectively
cosmetic for a long time because `validate_registry()` only checked that
the `hash` field **existed**, not that it **matched** the file.

**What I got wrong initially:** Recommended fixing only the analyzer's hash.
That would have left 227 other stale hashes and accomplished nothing —
the column still would not have been trustworthy for future gating. The
honest fix was either (a) regenerate all + add enforcement, or (b) drop
the field entirely.

**What to do instead:** When fixing a single instance of a broader quality
signal, first measure whether the signal is drift-enforced. If not, either
wire enforcement alongside the fix, or admit the field is decorative and
stop maintaining it. Regenerating one value without enforcement is
busy-work — the whole column keeps rotting.

**Resolution:** `validate_registry()` now compares each entry's `hash`
against `hash_pattern(<on-disk file>)` and `test_no_drift_in_shipped_registry`
pins the invariant. The `resolve_pattern_file()` helper handles hub-only
skills living at `.claude/skills/<name>/SKILL.md` (fallback) alongside
canonical `core/.claude/` paths, and skips `config`-type patterns that
aren't file-hashable.

**Also worth flagging** (surfaced but not actioned here): downstream
projects whose `.claude/config/test-pipeline.yml` lacks an `auto_heal:`
block will now hit the REQ-S004 fail-safe fallback — WARN logs +
`ISSUE_ONLY` defaults. Pick this up in the next `sync-to-projects` pass
so downstream maintainers add the block.
