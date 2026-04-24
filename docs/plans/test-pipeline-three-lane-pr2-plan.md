# PR2 Implementation Plan: Three-Lane Test Pipeline (Issue Creation + Auto-Fix Loop)

> **⚠️ SUPERSEDED (2026-04-24).** This plan implemented the T2B
> (`failure-triage-agent`) subgraph under the 4-tier dispatch model.
> Phase 3.1 of the subagent-dispatch-platform-limit remediation has
> dissolved T2B into the `/test-pipeline` skill-at-T0 body (spec v2.2
> STEP 6 TRIAGE). The PR2 design is preserved only as a historical
> record of the issue-creation + auto-fix semantics; those semantics
> carry forward into spec v2.2 by REQ ID. Do NOT execute this plan
> against the current agent set — the dispatch topology will silently
> inline instead of fanning out.

**Source spec:** `docs/specs/test-pipeline-three-lane-spec.md` v1.6 (SUPERSEDED
— see `docs/specs/test-pipeline-three-lane-spec-v2.md` v2.2 for the canonical design)
**Scope:** PR2 only — Issue creation system + T2B body activation + auto-fix loop + T1 atomic switchover (retired in Phase 3.1; see v2.2 STEP 6 TRIAGE)
**Depends on:** PR1 (`feat/test-pipeline-three-lane-pr1`) merged to main

---

## Context

PR1 shipped the lane infrastructure (functional + API parallel, UI post-functional, JOIN gate). PR2 completes the three-lane test pipeline by adding **autonomous Issue creation** and **parallel auto-fix**:

1. New `github-issue-manager-agent` (T3) creates one consolidated GitHub Issue per failed test (all 3 lanes' findings in one Issue body)
2. New `/create-github-issue` skill — universal `gh` CLI wrapper with hard-fail preflight (no silent skip on missing GitHub access)
3. Activate `failure-triage-agent` (T2B) body — analyzer fan-out → issue-manager fan-out → fixer fan-out → serialize → escalation
4. Extend `test-healer-agent` with `commit_mode` parameter for diff-only behavior (preserves backward compat)
5. Extend `/fix-issue` with `--diff-only` flag
6. New `/serialize-fixes` skill — atomic `git apply --check` first, then apply, with `git reset --hard HEAD` cleanup on failure
7. New `/escalation-report` skill — generates `test-results/escalation-report.md` on budget exhaustion
8. Extend `test-failure-analyzer-agent` for multi-lane awareness + cross-lane root-cause detection
9. **Atomic switchover in T1**: in the SAME commit, DELETE T1's inline Issue-creation step + ACTIVATE T2B's full body (no window with double Issue creation)
10. **Pre-merge migration script**: close all open `pipeline-failure` Issues from PR1 window with explanatory comment (closes Reviewer Gap N4 cross-PR-boundary dedup misses)

After PR2: PR1 features + autonomous Issue creation + parallel auto-fix with `git apply --check` safety + escalation report + final full-suite collateral-regression check.

---

## Critical Files Reference

### Files to CREATE (5 new)

| Path | Purpose | Approx LOC |
|---|---|---|
| `core/.claude/agents/github-issue-manager-agent.md` | T3 agent — wraps `/create-github-issue` per spec §3.7 | 80 |
| `core/.claude/skills/create-github-issue/SKILL.md` | Universal skill — preflight + `gh issue create` + sha256 dedup with 3-field hash | 150 |
| `core/.claude/skills/serialize-fixes/SKILL.md` | T2B helper — atomic diff apply with `--check` first, `git reset --hard HEAD` cleanup | 100 |
| `core/.claude/skills/escalation-report/SKILL.md` | T2B helper — generate `test-results/escalation-report.md` on budget exhaustion | 60 |
| `scripts/pr2_premerge_migration.py` | Pre-merge migration script — closes PR1-format `pipeline-failure` Issues before PR2 ships | 80 |

### Files to MODIFY (5 — additive + 1 atomic switchover)

| Path | Change Summary |
|---|---|
| `core/.claude/agents/testing-pipeline-master-agent.md` (T1) | **ATOMIC switchover (must be in PR2's first commit):** DELETE inline Issue-creation step entirely (closes Reviewer Gap 4); replace with delegation to T2A → T2B chain; the 4 PR1-temporary category handlers go away with the deletion |
| `core/.claude/agents/failure-triage-agent.md` (T2B) | **Activate full body** — replace PR1 NO_OP_PR1_SKELETON behavior with the 5-responsibility triage subgraph: analyzer fan-out → issue-manager fan-out + fan-in coordination → fixer fan-out (batched at `max_concurrent_fixers: 5`) → `/serialize-fixes` invocation → `/escalation-report` invocation |
| `core/.claude/agents/test-failure-analyzer-agent.md` (T3) | Multi-lane awareness — accept three lanes' failure data; cross-lane root cause detection per spec §3.5; return `recommended_action` field |
| `core/.claude/agents/test-healer-agent.md` (T3) | Accept optional `commit_mode` and `issue_number` in dispatch context. When `commit_mode=diff_only`, invoke `/fix-issue --diff-only` and write to `test-results/fixes/{issue_num}.diff` |
| `core/.claude/skills/fix-issue/SKILL.md` | Add `--diff-only` flag — when present, run analyze → plan → implement → STOP. Do not invoke `/post-fix-pipeline`. Write proposed changes as unified diff to `test-results/fixes/{issue_number}.diff`. Backward-compat: default behavior unchanged |
| `core/.claude/agents/test-pipeline-agent.md` (T2A) | Update STEP 6 (TRIAGE DISPATCH) — instead of receiving NO_OP_PR1_SKELETON, expect full triage results. Update return contract structure |

### Existing functions/patterns to REUSE

| Where | What to Reuse |
|---|---|
| PR1's `core/.claude/agents/github-issue-manager-agent.md` skeleton | This was a NEW file in PR1 (`failure-triage-agent.md`); same pattern — start with frontmatter + NON-NEGOTIABLE block per fugazi pattern |
| PR1's T1 inline Issue-creation step (about to be deleted) | Lift the body template + label conventions into the new `/create-github-issue` skill |
| PR1's existing `gh issue create` invocation pattern + sha256 dedup logic | New skill is the centralization of this pattern (single source of truth) |
| `/fix-issue` existing logic (analyze → plan → implement → `/post-fix-pipeline`) | Add `--diff-only` flag that gates the final `/post-fix-pipeline` call, leaves earlier steps unchanged |
| `core/.claude/agents/test-pipeline-agent.md` STEP 6 from PR1 | Update to read T2B's new structured result instead of `NO_OP_PR1_SKELETON` |
| `core/.claude/config/test-pipeline.yml` `auto_heal:` block (already declared in PR1 for forward-compat) | Activate — T2B reads this to decide AUTO_HEAL vs ISSUE_ONLY vs QUARANTINE per category |
| `core/.claude/config/test-pipeline.yml` `concurrency:` block (already declared in PR1) | Activate — T2B enforces `max_concurrent_fixers: 5` and `max_total_dispatches: 100` |

---

## Atomic Plans (28 tasks across 14 groups)

PR2 is larger than PR1 — more new resources, more agent extensions, atomic switchover.

---

### Atomic Plan 1: New skill `/create-github-issue`

#### Task 1: Create `/create-github-issue` skill

**Requirement:** REQ-M007, REQ-M008, REQ-M010, REQ-M011, REQ-M012
**Files:** `core/.claude/skills/create-github-issue/SKILL.md` (create)
**Code:** Universal skill with the body template per spec §3.7 + preflight checks (gh installed, gh auth status, git remote is github.com, token has WRITE/ADMIN). Hard-fail with structured `GITHUB_NOT_CONNECTED` contract on any preflight miss. Uses unified 3-field dedup hash `(test_id + category + failing_commit_sha_short)` per spec §3.7.
**Verify:**
```bash
test -f core/.claude/skills/create-github-issue/SKILL.md
PYTHONPATH=. python scripts/workflow_quality_gate_validate_patterns.py --score core/.claude/skills/create-github-issue/SKILL.md
```
**Estimate:** O: 20m | E: 35m | P: 60m
**Depends on:** None
**Rollback:** `rm -rf core/.claude/skills/create-github-issue/`

#### Task 2: Eval scenarios for `/create-github-issue` (≥5 per REQ-M033)

**Requirement:** REQ-M033
**Files:** `core/.claude/skills/create-github-issue/evals/scenarios/*.json` (5 scenarios — wait, scenarios are for AGENTS not skills per /agent-evaluator scope. Actually applies to GitHub-Issue-Manager-Agent in Plan 2)
**Note:** Skip — eval scenarios are for the agent that wraps this skill, not the skill itself.

---

### Atomic Plan 2: New agent `github-issue-manager-agent`

#### Task 3: Create `github-issue-manager-agent`

**Requirement:** REQ-M008
**Files:** `core/.claude/agents/github-issue-manager-agent.md` (create)
**Code:** Per spec §3.7. T3 agent, `tools: "Bash Read Skill"`, NON-NEGOTIABLE block (hard-fail GITHUB_NOT_CONNECTED, one-Issue-per-failed-test, honor dedup, no agent dispatch).
**Verify:** `test -f core/.claude/agents/github-issue-manager-agent.md && grep -q 'NON-NEGOTIABLE' core/.claude/agents/github-issue-manager-agent.md`
**Estimate:** O: 5m | E: 10m | P: 20m
**Depends on:** Task 1 (skill must exist for agent to invoke)
**Rollback:** `rm core/.claude/agents/github-issue-manager-agent.md`

#### Task 4: Eval scenarios for `github-issue-manager-agent` (≥5)

**Requirement:** REQ-M033
**Files:** `core/.claude/agents/github-issue-manager-agent/evals/scenarios/*.json` (≥5)
**Code:** Scenarios per spec §4 EVALS schema:
- `successful-create.json` — clean preflight, new Issue created, return contract has issue_number
- `dedup-hit-comments-existing.json` — preflight OK, sha256 hash matches existing Issue → comment instead, return `deduped: true`
- `preflight-gh-not-installed.json` — `command -v gh` fails → return GITHUB_NOT_CONNECTED contract
- `preflight-gh-not-authenticated.json` — `gh auth status` fails → return GITHUB_NOT_CONNECTED
- `preflight-not-github-remote.json` — origin URL has no github.com → return GITHUB_NOT_CONNECTED
**Verify:** `find core/.claude/agents/github-issue-manager-agent/evals/scenarios -name '*.json' | wc -l` returns ≥5
**Estimate:** O: 15m | E: 25m | P: 45m
**Depends on:** Task 3
**Rollback:** `rm -rf core/.claude/agents/github-issue-manager-agent/evals/`

---

### Atomic Plan 3: New skill `/serialize-fixes`

#### Task 5: Create `/serialize-fixes` skill

**Requirement:** REQ-M015, REQ-M018
**Files:** `core/.claude/skills/serialize-fixes/SKILL.md` (create)
**Code:** Per spec §3.9.3 algorithm: phase 1 `git apply --check` (dry-run), phase 2 `git apply` only if check passes, phase 3 `git commit`. On any failure between apply and commit: `git reset --hard HEAD` (mandatory). On `git apply --check` conflict: discard the diff (`rm`), label Issue `pipeline-fix-conflict`, schedule re-dispatch with fresh diff next iteration. Four NON-NEGOTIABLE rules per spec §3.9.3.
**Verify:** `test -f core/.claude/skills/serialize-fixes/SKILL.md && grep -q 'git apply --check' core/.claude/skills/serialize-fixes/SKILL.md && grep -q 'git reset --hard HEAD' core/.claude/skills/serialize-fixes/SKILL.md`
**Estimate:** O: 15m | E: 25m | P: 45m
**Depends on:** None
**Rollback:** `rm -rf core/.claude/skills/serialize-fixes/`

---

### Atomic Plan 4: New skill `/escalation-report`

#### Task 6: Create `/escalation-report` skill

**Requirement:** REQ-M020, REQ-M023
**Files:** `core/.claude/skills/escalation-report/SKILL.md` (create)
**Code:** Per spec §3.11. Reads run_id, list of resolved/closed Issues, list of unresolved Issues with `pipeline-fix-failed` label. Generates Markdown report at `test-results/escalation-report.md` per spec template.
**Verify:** `test -f core/.claude/skills/escalation-report/SKILL.md`
**Estimate:** O: 10m | E: 15m | P: 30m
**Depends on:** None
**Rollback:** `rm -rf core/.claude/skills/escalation-report/`

---

### Atomic Plan 5: Extend `/fix-issue` skill with `--diff-only` flag

#### Task 7: Add `--diff-only` flag to `/fix-issue`

**Requirement:** REQ-M014, REQ-M017
**Files:** `core/.claude/skills/fix-issue/SKILL.md` (modify)
**Code:** Add new flag handling per spec §3.9.1. When `--diff-only` present, skip `/post-fix-pipeline` invocation and write proposed changes to `test-results/fixes/{issue_number}.diff` instead. Default (no flag) behavior unchanged for backward compat with development-loop callers.
**Verify:** `grep -q 'diff-only' core/.claude/skills/fix-issue/SKILL.md`
**Estimate:** O: 10m | E: 15m | P: 30m
**Depends on:** None
**Rollback:** `git checkout HEAD -- core/.claude/skills/fix-issue/SKILL.md`

#### Task 8: Backward-compat test for `/fix-issue` without flag

**Requirement:** REQ-M032 + spec success criterion #14
**Files:** `scripts/tests/test_pipeline_three_lane_pr2.py` (create — append to existing or new)
**Code:** Test that invoking `/fix-issue` without `--diff-only` still produces a commit (existing behavior preserved).
**Verify:** `PYTHONPATH=. python -m pytest scripts/tests/test_pipeline_three_lane_pr2.py::test_fix_issue_no_flag_commits_directly -v`
**Estimate:** O: 10m | E: 15m | P: 30m
**Depends on:** Task 7
**Rollback:** Drop the test function

---

### Atomic Plan 6: Extend `test-healer-agent` for `commit_mode`

#### Task 9: Add `commit_mode` + `issue_number` dispatch params to `test-healer-agent`

**Requirement:** REQ-M013, REQ-M016
**Files:** `core/.claude/agents/test-healer-agent.md` (modify)
**Code:** Per spec §3.9.2 — accept optional `commit_mode: direct | diff_only` and `issue_number` in dispatch context. When `commit_mode=diff_only`: invoke `/fix-issue --diff-only` with the issue_number, write diff to `test-results/fixes/{issue_num}.diff`, do NOT commit. When `commit_mode=direct` (default): existing behavior preserved.
**Verify:** `grep -q 'commit_mode' core/.claude/agents/test-healer-agent.md && grep -q 'diff_only' core/.claude/agents/test-healer-agent.md`
**Estimate:** O: 10m | E: 15m | P: 30m
**Depends on:** Task 7 (--diff-only flag must exist on the underlying skill)
**Rollback:** `git checkout HEAD -- core/.claude/agents/test-healer-agent.md`

#### Task 10: Eval scenarios for `test-healer-agent` `commit_mode`

**Requirement:** REQ-M033
**Files:** `core/.claude/agents/test-healer-agent/evals/scenarios/*.json` (≥5)
**Code:** Scenarios:
- `commit-mode-direct-default.json` — no commit_mode in context → falls back to direct (commits)
- `commit-mode-diff-only-writes-diff.json` — commit_mode=diff_only → writes to test-results/fixes/{N}.diff, no commit
- `issue-number-propagated-to-fix-issue.json` — verify /fix-issue invoked with --diff-only and correct issue_number
- `commit-mode-direct-explicit.json` — commit_mode=direct explicitly → commits like default
- `backward-compat-no-issue-number.json` — no issue_number → defaults to existing healer behavior (legacy /fix-loop callsite)
**Verify:** `find core/.claude/agents/test-healer-agent/evals/scenarios -name '*.json' | wc -l` returns ≥5
**Estimate:** O: 15m | E: 25m | P: 40m
**Depends on:** Task 9
**Rollback:** `rm -rf core/.claude/agents/test-healer-agent/evals/`

---

### Atomic Plan 7: Extend `test-failure-analyzer-agent` for multi-lane

#### Task 11: Add multi-lane awareness + cross-lane root cause detection

**Requirement:** REQ-M006 (full body), spec §3.5
**Files:** `core/.claude/agents/test-failure-analyzer-agent.md` (modify)
**Code:** Per spec §3.5. Accept three lanes' failure data in dispatch context. Apply existing 18 regex pre-classification rules first. Then LLM classification considering combined signals (e.g., functional + API both fail with "schema mismatch" → SCHEMA_MISMATCH). Return new `recommended_action` field (AUTO_HEAL | ISSUE_ONLY | QUARANTINE | RETRY_INFRA). Backward compat: single-lane data still produces same classification as before.
**Verify:** `grep -q 'recommended_action\|cross-lane\|multi-lane' core/.claude/agents/test-failure-analyzer-agent.md`
**Estimate:** O: 20m | E: 30m | P: 60m
**Depends on:** None
**Rollback:** `git checkout HEAD -- core/.claude/agents/test-failure-analyzer-agent.md`

#### Task 12: Eval scenarios for analyzer multi-lane

**Requirement:** REQ-M033
**Files:** `core/.claude/agents/test-failure-analyzer-agent/evals/scenarios/*.json` (≥5)
**Code:** Scenarios:
- `regex-pre-classification-short-circuits-llm.json` — locator error string → BROKEN_LOCATOR via regex, skip LLM
- `multi-lane-functional-plus-api-schema-mismatch.json` — both lanes fail with schema error → single SCHEMA_MISMATCH category
- `confidence-threshold-gating.json` — confidence below 0.85 → ISSUE_ONLY recommended_action
- `needs-contract-validation-emitted-when-no-contract-tooling.json` — API lane fails with no contract files → NEEDS_CONTRACT_VALIDATION
- `backward-compat-single-lane-data.json` — only one lane's data → same classification as before
**Verify:** `find core/.claude/agents/test-failure-analyzer-agent/evals/scenarios -name '*.json' | wc -l` returns ≥5
**Estimate:** O: 15m | E: 25m | P: 40m
**Depends on:** Task 11
**Rollback:** `rm -rf core/.claude/agents/test-failure-analyzer-agent/evals/`

---

### Atomic Plan 8: T2B body activation (failure-triage-agent full)

#### Task 13: Activate `failure-triage-agent` full body

**Requirement:** REQ-M006 (full activation), REQ-M013 (Issue-manager fan-in coordination), REQ-M014 (batched fan-out)
**Files:** `core/.claude/agents/failure-triage-agent.md` (modify — replace PR1 NO_OP_PR1_SKELETON behavior)
**Code:** Per spec §3.5. Replace skeleton with full 5-step body:
1. Analyzer fan-out (per failed test, batched at max_concurrent_analyzers)
2. Issue-manager fan-out + fan-in coordination (abort-on-first-blocked partial-failure policy per spec §3.7.1)
3. Fixer fan-out (only AUTO_HEAL category Issues, batched at max_concurrent_fixers=5)
4. `/serialize-fixes` invocation with collected diff paths
5. `/escalation-report` invocation on budget exhaustion
- Update NON-NEGOTIABLE from PR1 skeleton form to full PR2 form per spec §3.5
- Bump version 0.1.0 → 1.0.0
**Verify:**
```bash
grep -q '## Core Responsibilities' core/.claude/agents/failure-triage-agent.md
PYTHONPATH=. python -c "
from scripts.workflow_quality_gate_validate_patterns import count_responsibilities
from pathlib import Path
count = count_responsibilities(Path('core/.claude/agents/failure-triage-agent.md'))
assert count == 5, f'expected 5 responsibilities, got {count}'
print(f'OK: {count} responsibilities (matches allowlist)')
"
```
**Estimate:** O: 30m | E: 60m | P: 120m
**Depends on:** Tasks 3, 5, 6, 7, 9, 11 (all sub-components must exist)
**Rollback:** `git checkout HEAD -- core/.claude/agents/failure-triage-agent.md`

#### Task 14: Eval scenarios for full T2B (≥5)

**Requirement:** REQ-M033
**Files:** `core/.claude/agents/failure-triage-agent/evals/scenarios/*.json` — REPLACE the 5 PR1-skeleton scenarios with PR2-full scenarios
**Code:** New scenarios:
- `all-auto-heal-batch-succeeds.json` — 3 failed tests all AUTO_HEAL → fixers dispatched, diffs serialized, Issues closed
- `one-issue-only-skips-fixer.json` — 2 AUTO_HEAL + 1 LOGIC_BUG (ISSUE_ONLY) → only 2 fixers dispatched, LOGIC_BUG Issue stays open
- `github-not-connected-aborts-entire-triage.json` — first issue-manager preflight fails → abort all remaining triage
- `dispatch-budget-exhaustion.json` — synthetic 101+ dispatches → BLOCKED: DISPATCH_BUDGET_EXCEEDED contract
- `cross-lane-shared-root-cause-single-issue.json` — same test fails in functional + API → analyzer returns single SCHEMA_MISMATCH category → one consolidated Issue
- `batch-of-12-fans-out-as-3-batches.json` — 12 failures with max_concurrent_fixers=5 → verify chunking
**Verify:** `find core/.claude/agents/failure-triage-agent/evals/scenarios -name '*.json' | wc -l` returns ≥5
**Estimate:** O: 30m | E: 50m | P: 90m
**Depends on:** Task 13
**Rollback:** `git checkout HEAD -- core/.claude/agents/failure-triage-agent/evals/`

---

### Atomic Plan 9: T2A return-contract update for full T2B

#### Task 15: Update T2A STEP 6 to expect full T2B contract

**Requirement:** REQ-M006 (T2A receives full triage result, not no-op)
**Files:** `core/.claude/agents/test-pipeline-agent.md` (modify STEP 6 + STEP 7 contract)
**Code:** STEP 6: instead of `expect NO_OP_PR1_SKELETON`, expect structured triage result with `issues_created`, `fixes_applied`, `fixes_pending`. STEP 7: bubble-up contract to T1 includes the triage outcome (not the raw failure set anymore — Issues are already created by T2B).
**Verify:** `grep -q 'issues_created\|fixes_applied' core/.claude/agents/test-pipeline-agent.md`
**Estimate:** O: 10m | E: 15m | P: 30m
**Depends on:** Task 13 (T2B body must exist with the new return contract)
**Rollback:** `git checkout HEAD -- core/.claude/agents/test-pipeline-agent.md`

---

### Atomic Plan 10: T1 Atomic Switchover (CRITICAL — must be in same commit as Task 13)

#### Task 16: DELETE T1's inline Issue-creation step

**Requirement:** REQ-M011 (PR2 atomic switchover), spec §8 PR2 boundary
**Files:** `core/.claude/agents/testing-pipeline-master-agent.md` (modify — DELETE the entire `## STEP: GitHub Issue Creation` section + the 4 PR1-temporary category handlers)
**Code:** Remove the entire inline step. Replace with a one-line pointer: `> Issue creation in PR2 flows through T2A → T2B → github-issue-manager-agent. T1 reads triage results from T2A's return contract.`
**Verify:**
```bash
# Section deleted
! grep -q '^## STEP: GitHub Issue Creation' core/.claude/agents/testing-pipeline-master-agent.md
# 4 PR1-temporary categories no longer in T1 body (now handled by T2B)
! grep -q 'SCHEMA_MISMATCH\|STATUS_CODE_DRIFT' core/.claude/agents/testing-pipeline-master-agent.md
# Pointer present
grep -q 'github-issue-manager-agent' core/.claude/agents/testing-pipeline-master-agent.md
```
**CRITICAL:** This task MUST be in the SAME COMMIT as Task 13 (T2B activation). Otherwise there's a window where Issues are double-created (T1 inline + T2B both active) OR no Issues are created (T1 deleted but T2B still skeleton). Spec §8 mandates atomic switchover.
**Estimate:** O: 10m | E: 15m | P: 30m
**Depends on:** Task 13 (T2B must be active)
**Rollback:** `git checkout HEAD -- core/.claude/agents/testing-pipeline-master-agent.md` (also reverts Task 13 if same commit — that's the point)

---

### Atomic Plan 11: Pre-merge migration script

#### Task 17: Create `scripts/pr2_premerge_migration.py`

**Requirement:** REQ-M011 (hash transition), spec §8 PR2 deployment checkbox, success criterion #31
**Files:** `scripts/pr2_premerge_migration.py` (create)
**Code:** Per spec §8 PR2 implementation order. One-shot script:
- `gh issue list --label pipeline-failure --state open --created-after <30 days ago>`
- For each: `gh issue close <N> --comment "Closing pre-PR2 Issue. If this failure recurs after PR2 deploys, a new Issue will be created with the v2 dedup format. Manual cross-link if needed."`
- Output: count of Issues closed
**Verify:** `python scripts/pr2_premerge_migration.py --dry-run` (must support dry-run mode)
**Estimate:** O: 15m | E: 25m | P: 45m
**Depends on:** None (script is standalone — runs once at PR2 merge time)
**Rollback:** `rm scripts/pr2_premerge_migration.py`

#### Task 18: Document migration script as PR2 merge gate

**Requirement:** Spec §8 PR2 deployment checkbox
**Files:** `docs/specs/test-pipeline-three-lane-spec.md` (modify §8 PR2 — add explicit step)
**Code:** Add to PR2 merge checklist: "Before merging PR2: run `python scripts/pr2_premerge_migration.py` to close PR1-format Issues. Verify zero open `pipeline-failure` Issues remain."
**Verify:** `grep -q 'pr2_premerge_migration' docs/specs/test-pipeline-three-lane-spec.md`
**Estimate:** O: 5m | E: 8m | P: 15m
**Depends on:** Task 17
**Rollback:** `git checkout HEAD -- docs/specs/test-pipeline-three-lane-spec.md`

---

### Atomic Plan 12: New PR2 test file

#### Task 19: Create `scripts/tests/test_pipeline_three_lane_pr2.py`

**Requirement:** Spec §6 success criteria #3, 6-13, 15-17, 20, 22-24, 26, 31
**Files:** `scripts/tests/test_pipeline_three_lane_pr2.py` (create)
**Code:** New pytest file covering PR2 scope:
- `test_create_github_issue_skill_exists()`
- `test_github_issue_manager_agent_exists()`
- `test_serialize_fixes_skill_exists()`
- `test_escalation_report_skill_exists()`
- `test_fix_issue_diff_only_flag_documented()`
- `test_test_healer_agent_commit_mode_documented()`
- `test_failure_triage_agent_full_body_replaces_skeleton()` — assert NO_OP_PR1_SKELETON no longer present
- `test_t1_inline_issue_creation_deleted()` — grep T1 for absence of `## STEP: GitHub Issue Creation`
- `test_t1_pr1_temporary_categories_removed()` — grep T1 for absence of SCHEMA_MISMATCH etc. handlers
- `test_dedup_hash_includes_failing_commit_sha_short()` — validate `/create-github-issue` body uses 3-field hash
- `test_dispatch_budget_exhaustion_returns_BLOCKED_contract()` — synthetic 101+ dispatches
- `test_wall_clock_budget_exhaustion_returns_BLOCKED()` — synthetic timestamp injection
- `test_max_concurrent_fixers_chunks_at_5()` — 12 failures → 3 batches
- `test_atomic_diff_apply_runs_check_first()` — validate `/serialize-fixes` body
- `test_partial_diff_failure_triggers_git_reset()` — validate `git reset --hard HEAD` mandate
- `test_stale_diff_discarded_on_conflict()` — `rm` on conflict
- `test_pr2_premerge_migration_dry_run()` — script runs without error
- `test_backward_compat_fix_loop_still_commits_directly()` — `commit_mode` default=direct preserved
**Verify:** `PYTHONPATH=. python -m pytest scripts/tests/test_pipeline_three_lane_pr2.py -v` — all pass
**Estimate:** O: 60m | E: 90m | P: 150m
**Depends on:** Tasks 1, 3, 5, 6, 7, 9, 11, 13, 15, 16, 17 (all PR2 components must exist)
**Rollback:** `rm scripts/tests/test_pipeline_three_lane_pr2.py`

---

### Atomic Plan 13: Registry + agent-evaluator runs

#### Task 20: Update `registry/patterns.json` with new entries + activate failure-triage-agent

**Requirement:** REQ-M036 (registry consistency)
**Files:** `registry/patterns.json` (modify)
**Code:** Add 4 new entries (`github-issue-manager-agent`, `create-github-issue`, `serialize-fixes`, `escalation-report`). Update `failure-triage-agent` version 0.1.0 → 1.0.0. Update existing entries' versions for any agents whose body content changed substantially (test-healer-agent, test-failure-analyzer-agent, test-pipeline-agent).
**Verify:** `python -c "import json; d=json.load(open('registry/patterns.json', encoding='utf-8')); assert 'github-issue-manager-agent' in d and 'create-github-issue' in d and 'serialize-fixes' in d and 'escalation-report' in d; assert d['failure-triage-agent']['version'] == '1.0.0'"`
**Estimate:** O: 10m | E: 15m | P: 25m
**Depends on:** Tasks 1, 3, 5, 6, 13 (files must exist for hash computation)
**Rollback:** `git checkout HEAD -- registry/patterns.json`

#### Task 21: Run `/agent-evaluator` against ALL PR2 modified/new agents

**Requirement:** REQ-M033 pre-merge gate
**Files:** None (verification only)
**Code:**
```bash
for agent in github-issue-manager-agent failure-triage-agent test-healer-agent test-failure-analyzer-agent; do
    /agent-evaluator core/.claude/agents/$agent.md
done
# Assert all aggregate verdicts = PASS, avg score ≥4
```
**Verify:** All evaluated agents pass with avg score ≥4
**Estimate:** O: 15m | E: 30m | P: 60m
**Depends on:** Tasks 4, 10, 12, 14 (eval scenarios must exist)
**Rollback:** N/A

---

### Atomic Plan 14: Final integration + CI

#### Task 22: Run all 4 CI gates locally

**Requirement:** Spec §6 success criterion #16
**Files:** None
**Code:**
```bash
PYTHONPATH=. python scripts/dedup_check.py --validate-all
PYTHONPATH=. python scripts/dedup_check.py --secret-scan
PYTHONPATH=. python scripts/workflow_quality_gate_validate_patterns.py
PYTHONPATH=. python -m pytest scripts/tests/ -v
```
**Verify:** All 4 exit 0
**Estimate:** O: 5m | E: 15m | P: 45m
**Depends on:** All previous (Tasks 1-21)
**Rollback:** N/A

#### Task 23: Run synthetic end-to-end smoke against extended playwright-demo fixture

**Requirement:** Spec §6 success criteria #1-2, #28
**Files:** None (verification only)
**Code:** Manual `/test-pipeline` invocation against `scripts/tests/fixtures/playwright-demo/`. Verify:
- All 6 categories produce GitHub Issues (4 new from PR1 + LOGIC_BUG + VISUAL_REGRESSION)
- One consolidated Issue per failed test (not one per lane)
- Hash dedup works on re-run (same SHA → same Issue)
- Different SHA → new Issue (refactor visibility)
- AUTO_HEAL categories trigger fixer dispatch
- ISSUE_ONLY categories don't trigger fixer
**Verify:** `gh issue list --label pipeline-failure --state open` shows expected Issues
**Estimate:** O: 30m | E: 60m | P: 120m
**Depends on:** Task 22
**Rollback:** Close generated test Issues with `gh issue close`

#### Task 24: Verify rollback procedure works

**Requirement:** REQ-S010 (acknowledged trade-off — manual procedure documented)
**Files:** None (verification only)
**Code:** Per spec §3.15 TRADE-OFF-4 manual rollback procedure:
- (1) `git revert <PR2-commit-sha>`
- (2) Close all `pipeline-failure` Issues created in past 24h with rollback comment
- (3) `rm -rf .workflows/testing-pipeline/sub/` (NOT `git rm` — gitignored)
- (4) Verify T1's old Issue-creation step is restored and works
**Verify:** Manual smoke after revert
**Estimate:** O: 15m | E: 25m | P: 45m
**Depends on:** Task 22, 23
**Rollback:** Re-apply PR2 commit (the revert IS the rollback test)

#### Task 25: Open PR2 with description linking to spec + PR1 + PR2 plan

**Requirement:** Spec §8 PR2 implementation order final step
**Files:** None (PR description only)
**Code:** Use `gh pr create` with description that:
- Links to spec v1.6 (`docs/specs/test-pipeline-three-lane-spec.md`)
- Links to PR1 (#12)
- Links to this PR2 plan (`docs/plans/test-pipeline-three-lane-pr2-plan.md`)
- Links to all 5 reviewer-pass artifacts
- Includes pre-merge migration script reminder
- Test plan covers success criteria #3, 6-13, 15-17, 20, 22-24, 26, 31
**Verify:** PR opened with `gh pr view <N>`
**Estimate:** O: 10m | E: 15m | P: 30m
**Depends on:** Tasks 22, 23
**Rollback:** `gh pr close <N>`

---

## Dependency Graph

```
Critical path (≈ 4-6 hrs sequential):
  Task 1 (skill) ──┐
  Task 5 (skill) ──┼─→ Task 13 (T2B body activation) ──┬─→ Task 15 (T2A update) ──┐
  Task 6 (skill) ──┤                                    │                          ├─→ Task 19 (tests) ─→ Task 22 (CI) ─→ Task 23 (smoke)
  Task 7 (flag) ──→ Task 9 (healer) ──┘                Task 16 (T1 ATOMIC DELETE) ┘
  Task 11 (analyzer) ─────────────────────────────────────→ ↑ (must be in same commit as Task 13)

Parallelizable side branches:
  Task 3 (issue-mgr agent) ← Task 1
  Task 4 (issue-mgr evals) ← Task 3
  Task 8 (fix-issue test) ← Task 7
  Task 10 (healer evals) ← Task 9
  Task 12 (analyzer evals) ← Task 11
  Task 14 (T2B evals) ← Task 13
  Task 17 (migration script) — independent
  Task 18 (spec doc update) ← Task 17
  Task 20 (registry) ← Tasks 1, 3, 5, 6, 13
  Task 21 (eval runs) ← Tasks 4, 10, 12, 14
```

### PERT Time Budget (Critical Path)

| Task | Optimistic | Expected | Pessimistic | PERT |
|---|---|---|---|---|
| Task 1 (skill) | 20 | 35 | 60 | 36.7 |
| Task 13 (T2B) | 30 | 60 | 120 | 65 |
| Task 16 (T1 delete) | 10 | 15 | 30 | 16.7 |
| Task 15 (T2A update) | 10 | 15 | 30 | 16.7 |
| Task 19 (tests) | 60 | 90 | 150 | 95 |
| Task 22 (CI) | 5 | 15 | 45 | 18.3 |
| Task 23 (smoke) | 30 | 60 | 120 | 65 |
| **Sum** | | | | **~313m** |
| **+ 20% buffer** | | | | **~376m (6hr 16min)** |

Parallelizable: ~30% (independent skills, evals, registry, migration script).

---

## Risk Mitigations

### RISK-1: T2B body activation is the highest-risk file change (replacing 5 placeholders with 5 fully-specified responsibilities)
**Mitigation:** Execute Task 13 in a fresh subagent context (atomic plan boundary). Read PR1 skeleton FULLY before replacement. Preserve frontmatter version bump 0.1.0 → 1.0.0. Branch backup `git branch t2b-activation-backup` before Task 13.

### RISK-2: Task 13 + Task 16 must be in the SAME commit (atomic switchover)
**Mitigation:** Stage both changes with `git add` + commit with single message `feat(testing-pipeline)!: PR2 atomic switchover (T2B body activation + T1 inline deletion)`. Add a pre-commit verification: validator runs on staged files, fails if T1 still has inline step OR T2B still has NO_OP_PR1_SKELETON.

### RISK-3: PR1→PR2 dedup hash transition produces duplicate Issues mid-deployment
**Mitigation:** Mandatory pre-merge migration script (Task 17) runs BEFORE PR2 ships. Verify zero open `pipeline-failure` Issues with PR1 hash format (2-field) before merge. Documented in Task 18.

### RISK-4: `/serialize-fixes` `git apply --check` not supported in older git versions
**Mitigation:** `git apply --check` available since git 1.7 (2010). Hub already requires modern git for other operations. Add version check at skill start: `git --version | grep -E '^git version (1\.7|1\.8|1\.9|2\.|3\.)'` else BLOCKED.

### RISK-5: Backward compat regression for standalone `/fix-loop` callers (tester-agent, e2e-conductor-agent)
**Mitigation:** Task 8 explicitly tests `/fix-issue` without `--diff-only` still commits directly. Existing `/fix-loop` test must continue to pass per success criterion #14.

---

## Verification Plan (End-to-End)

After all tasks complete:

```bash
# 1. Configuration validity (PR1 still passes)
python -c "import yaml; yaml.safe_load(open('core/.claude/config/test-pipeline.yml'))"
python -c "import yaml; yaml.safe_load(open('core/.claude/config/orchestrator-responsibility-allowlist.yml'))"

# 2. Pattern validation (all 4 CI gates)
PYTHONPATH=. python scripts/dedup_check.py --validate-all
PYTHONPATH=. python scripts/dedup_check.py --secret-scan
PYTHONPATH=. python scripts/workflow_quality_gate_validate_patterns.py
PYTHONPATH=. python -m pytest scripts/tests/ -v

# 3. PR1 + PR2 test files (combined)
PYTHONPATH=. python -m pytest scripts/tests/test_pipeline_three_lane.py scripts/tests/test_pipeline_three_lane_pr2.py -v

# 4. Agent evaluations (gate per REQ-M033)
for agent in github-issue-manager-agent failure-triage-agent test-healer-agent test-failure-analyzer-agent; do
    /agent-evaluator core/.claude/agents/$agent.md
done

# 5. End-to-end smoke against extended playwright-demo
# (Manual /test-pipeline invocation; verify all 6 failure categories produce Issues)

# 6. Atomic switchover verification
# Verify Task 13 + Task 16 are in the SAME commit:
git log --pretty=format:'%H %s' | head -3
git show HEAD --stat | grep -E '(failure-triage-agent|testing-pipeline-master-agent)'

# 7. Pre-merge migration dry-run
python scripts/pr2_premerge_migration.py --dry-run

# 8. Rollback procedure smoke (Task 24)
# Manual: git revert + close Issues + rm -rf sub/
```

Success criteria from spec §6 verified by this plan: #3, 6, 7, 8, 8b, 9, 10, 11, 12, 13, 14, 15, 16, 17, 20, 22, 23, 24, 26, 27, 30, 31.

---

## Pre-Merge Checklist

Before opening PR2 for review:

- [ ] All 25 tasks completed and verified
- [ ] Task 13 + Task 16 confirmed in SAME commit (atomic switchover)
- [ ] Pre-merge migration script run (`python scripts/pr2_premerge_migration.py`) — verified zero open `pipeline-failure` Issues with PR1 hash format
- [ ] All 4 CI gates pass locally
- [ ] All eval scenarios pass with avg ≥4
- [ ] Rollback procedure documented and verified manually
- [ ] PR description links spec v1.6 + PR1 (#12) + this plan + 5 reviewer-pass artifacts

---

## Out of Scope (Future PRs)

Items in the spec's COULD HAVE / SHOULD HAVE tiers for future iteration:

- REQ-S001: `--only-issues N,M,...` flag to re-run pipeline against specific Issues
- REQ-S002: `--update-baselines` flag for `BASELINE_DRIFT_INTENTIONAL` auto-heal
- REQ-S005: Post-pipeline `git rebase -i --autosquash` to consolidate fix commits
- REQ-S006: UI lane starts on `functional.ui-tests-complete.flag` checkpoint (optimization)
- REQ-S007: Weighted dispatch counter (TRADE-OFF-1 — revisit if production data justifies)
- REQ-S008: Per-phase wall-clock timeouts (TRADE-OFF-2 — revisit if slow-CI users report starvation)
- REQ-S009: Merge-aware dedup hash (TRADE-OFF-3 — revisit if squash-merge churn dominates triage)
- REQ-S010: Feature-flag-based switchover (TRADE-OFF-4 — revisit if PR2 rollback needed in first month)
- REQ-C001: Worktree-per-fixer (escape hatch for frequent same-file conflicts)
- REQ-C002: Slack notification on `pipeline-fix-failed` Issue creation
- REQ-C003: Fixer batches into a single PR (vs one commit per fix)
- REQ-C004: Auto-assign reviewer on `pipeline-fix-failed` Issues based on CODEOWNERS

---

## Next Steps After Plan Approval

1. **Verify PR1 is merged to main** (PR2 depends on PR1's lane infrastructure)
2. **Verify cp1252 fix PR is merged** (PR #13 — separate independent fix)
3. **Create branch:** `git checkout -b feat/test-pipeline-three-lane-pr2`
4. **Execute atomic plans 1-14 in dependency order** (~4-6 hours sequential, ~3-4 hours with parallelism)
5. **Run pre-merge migration script** before opening PR2
6. **Open PR2** with description linking spec + PR1 + this plan + reviewer-pass artifacts
7. **CI gates pass** → request review → merge

After PR2 lands, the three-lane test pipeline is feature-complete per spec v1.6.
