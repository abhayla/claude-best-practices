---
name: serialize-fixes
description: >
  Apply a list of unified-diff files sequentially to the working tree using the
  three-phase atomic protocol (git apply --check → git apply → git commit).
  Use when `/test-pipeline` (skill-at-T0, spec v2.2) has collected per-test
  diffs from parallel fixer agents at STEP 6 TRIAGE Fan-out 3 and needs to land
  them on a shared branch without conflicts. On `git apply --check` conflict:
  discard the stale diff and label the Issue. On any failure between apply
  and commit: `git reset --hard HEAD` to clean the working tree (mandatory).
type: workflow
allowed-tools: "Bash Read"
argument-hint: "<diffs-glob-or-list> [--autosquash]"
version: "1.1.0"
---

# Serialize Fixes — Atomic Sequential Diff Application

Applies a batch of fixer-produced diffs to the working tree, one at a time,
with `git apply --check` as a safety dry-run before each real apply. Used by
`/test-pipeline` (skill-at-T0) at STEP 6 TRIAGE Fan-out 3 to land parallel
fix attempts on a shared branch without race conditions.

**Request:** $ARGUMENTS — one of:
- A glob pattern: `test-results/fixes/*.diff`
- A comma-separated list: `test-results/fixes/1234.diff,test-results/fixes/1235.diff`

> Spec reference: `docs/specs/test-pipeline-three-lane-spec.md` v1.6 §3.9.3

---

## STEP 0: Resolve diff list

Expand glob or split list into an ordered array `$DIFFS`. Order is the natural
sort order of the filenames (typically by issue number ascending).

For each diff, also resolve the corresponding issue number from the filename:
`test-results/fixes/{issue_number}.diff` → `$issue_num`.

Verify each diff file exists and is non-empty. If any is missing or empty:
log `SKIPPED: missing or empty diff file` and continue with remaining.

---

## STEP 1: Process each diff (three-phase atomic protocol)

For each `$diff` in `$DIFFS`:

### Phase A: Dry-run check (NEVER dirties working tree)

```bash
if ! git apply --check "$diff" 2>/dev/null; then
    echo "CONFLICT: $diff — discarding stale diff (will recompute next iteration)"
    gh issue edit "$issue_num" --add-label pipeline-fix-conflict 2>/dev/null || true
    rm "$diff"   # explicit discard so re-dispatch computes fresh diff against new file state
    record_in_state "$issue_num" "stale_diff_discarded"
    continue   # next diff
fi
```

### Phase B: Real apply (only if Phase A passed)

```bash
if ! git apply "$diff"; then
    # Should not happen given --check passed; defensive cleanup
    git reset --hard HEAD   # MANDATORY: clean working tree on any failure between apply and commit
    gh issue edit "$issue_num" --add-label pipeline-fix-failed 2>/dev/null || true
    record_in_state "$issue_num" "apply_failed_after_check"
    continue
fi
```

### Phase C: Commit

```bash
test_id=$(extract_test_id_from_diff "$diff" || echo "unknown")
if ! git add -A && git commit -m "fix(test-pipeline): heal $test_id (#$issue_num)"; then
    # Commit failure (e.g., pre-commit hook rejected) — clean up
    git reset --hard HEAD   # MANDATORY
    gh issue edit "$issue_num" --add-label pipeline-fix-failed 2>/dev/null || true
    record_in_state "$issue_num" "commit_failed"
    continue
fi

commit_sha=$(git rev-parse --short HEAD)
record_in_state "$issue_num" "applied" "$commit_sha"
```

---

## STEP 1.5: Optional autosquash (REQ-S005)

When `--autosquash` is present in `$ARGUMENTS` AND `commits_made > 1`, consolidate the fix commits via interactive rebase with autosquash.

```bash
# Identify the commit BEFORE the first fix commit (the merge base of the fix batch)
FIRST_FIX_SHA=$(echo "$applied_commits" | head -1)
PRE_FIX_PARENT=$(git rev-parse "${FIRST_FIX_SHA}~1")

# Mark all fix commits as fixup of the first one (so they squash into it)
# Use git rebase --autosquash with --interactive=false-equivalent (--keep-base + autosquash)
GIT_SEQUENCE_EDITOR=: git rebase -i --autosquash "$PRE_FIX_PARENT" 2>&1 || {
    # On rebase failure, abort — original history preserved
    git rebase --abort
    echo "WARN: autosquash failed; original fix commits preserved"
    return autosquash_result="FAILED"
}

return autosquash_result="SUCCESS" with consolidated_commit_sha=$(git rev-parse --short HEAD)
```

**Safety:**
- Only runs when `commits_made > 1` (no point squashing a single commit)
- Uses `GIT_SEQUENCE_EDITOR=:` to make the rebase non-interactive (accepts the auto-generated todo list as-is)
- On failure: `git rebase --abort` restores the pre-rebase state; original commits preserved
- Each original fix commit message MUST be in conventional `fix(test-pipeline): heal {test_id} (#{issue_num})` format for autosquash to recognize them as fixup candidates of each other (or use explicit `fixup!` prefix)

## STEP 2: Return aggregated contract

After all diffs processed (and optional autosquash), return:

```json
{
  "applied": [
    {"issue_number": 1234, "commit_sha": "abc1234", "diff_path": "test-results/fixes/1234.diff"},
    ...
  ],
  "conflicted": [
    {"issue_number": 1235, "diff_path": "test-results/fixes/1235.diff", "action": "stale_diff_discarded"},
    ...
  ],
  "failed": [
    {"issue_number": 1236, "diff_path": "test-results/fixes/1236.diff", "action": "commit_failed"},
    ...
  ],
  "total_processed": <N>,
  "commits_made": <count of applied>,
  "autosquash_result": "SKIPPED|SUCCESS|FAILED",
  "consolidated_commit_sha": "<short SHA if autosquash SUCCESS, else null>"
}
```

---

## NON-NEGOTIABLE

1. **ALWAYS run `git apply --check` before `git apply`.** Never apply a diff without the dry-run first. The check is what prevents partial-apply working-tree corruption.
2. **ALWAYS `git reset --hard HEAD` on any failure between apply and commit.** Never leave a dirty working tree. Subsequent `git apply` calls would corrupt against unstaged changes from the failed previous apply.
3. **NEVER retain stale diffs on conflict.** `rm` the diff file so the next iteration of the fix loop computes a fresh diff against the new file state. Retaining stale diffs causes repeated false-conflict cycles.
4. **Process diffs in order; do NOT parallelize within this skill.** Parallel git apply calls race on the working tree. The CONCEPT of fixer parallelism happens during diff GENERATION (parallel fixer agents); diff APPLICATION is serialized here.
5. **`gh issue edit` failures are non-fatal.** If GitHub is temporarily unreachable, log and continue. The diff application is the critical path; label updates are best-effort metadata.

## CRITICAL RULES

- MUST NOT skip Phase A (dry-run check) — that's the safety primitive
- MUST NOT skip the `git reset --hard HEAD` cleanup on Phase B/C failures
- MUST NOT process diffs in parallel within a single invocation
- MUST `rm` stale-conflicted diffs (closes spec §3.9.3 G8 — fresh diff next iteration)
- MUST emit aggregate `commits_made` count for parent T2B's progress reporting
