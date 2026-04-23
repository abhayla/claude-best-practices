---
name: pipeline-fix-pr
description: >
  Apply pipeline fixer diffs to a NEW branch and open a single PR with all
  fixes (instead of N commits on the current branch). Use when the team's
  git workflow requires PR review for any change. Wraps `/serialize-fixes`
  for the actual diff application; this skill adds branch creation, push,
  and `gh pr create`. Propagated from `/test-pipeline --fix-pr-mode` through
  T2A → T2B context. Does NOT auto-merge — always leaves the PR for human
  review (per `git-collaboration.md` rule "Review Before Merge").
type: workflow
allowed-tools: "Bash Read"
argument-hint: "<diffs-glob-or-list> [--base <branch>] [--no-push]"
version: "1.0.0"
---

# Pipeline Fix PR — Single-PR Fixer Batching (REQ-C003)

When the test-pipeline's T2B (`failure-triage-agent`) finishes producing fix
diffs and the user has opted into `--fix-pr-mode`, this skill takes over
from `/serialize-fixes` to land the fixes on a separate branch + open ONE PR
covering all fixes from the run. Cleaner PR diff than N commits on the
working branch; honors team's PR-required workflow.

**Request:** $ARGUMENTS — `<diffs-glob-or-list> [--base <branch>] [--no-push]`

> Spec reference: `docs/specs/test-pipeline-three-lane-spec.md` v1.6 §5 REQ-C003
> Project convention: `core/.claude/rules/git-collaboration.md` § "Review Before Merge"

---

## STEP 0: Preflight

Same gh-CLI preflight as `/create-github-issue` (gh installed + authenticated +
github.com remote + push permission). Hard-fail with structured BLOCKED contract
on any preflight miss.

If `--no-push` is set (dry-run mode), skip push + PR steps; just create local
branch + apply diffs locally.

---

## STEP 1: Parse arguments + capture context

Extract:
- `$DIFFS` — diff list (same format as /serialize-fixes)
- `$BASE` — base branch (default: current branch's upstream tracking, or `main`)
- `$NO_PUSH` — boolean (default false)
- `$RUN_ID` — pipeline run_id (from env or last `.workflows/testing-pipeline/sub/test-pipeline.json`)

Capture current branch as `$ORIGINAL_BRANCH` so we can return to it on failure.

---

## STEP 2: Create fix branch

```bash
FIX_BRANCH="pipeline-fixes/${RUN_ID}"
git checkout -b "$FIX_BRANCH" 2>/dev/null || {
    echo "WARN: branch $FIX_BRANCH exists; resetting"
    git checkout "$FIX_BRANCH"
    git reset --hard "$ORIGINAL_BRANCH"
}
```

---

## STEP 3: Apply diffs (delegate to /serialize-fixes)

```
Skill("serialize-fixes", args="$DIFFS")
```

Read its return contract for `applied`/`conflicted`/`failed` counts and per-issue commit SHAs.

**Behavior change vs main flow:** the commits land on `$FIX_BRANCH` instead of
the original branch. `/serialize-fixes`'s atomicity guarantees still apply
(`git apply --check` first, `git reset --hard HEAD` cleanup on partial failure,
discard stale diffs on conflict).

---

## STEP 4: Push branch + open PR (skipped if --no-push)

```bash
if [ "$NO_PUSH" != "true" ]; then
    git push -u origin "$FIX_BRANCH"

    PR_TITLE="fix(test-pipeline): heal $applied_count test failures from run $RUN_ID"
    PR_BODY=$(cat <<EOT
## Summary

Auto-generated PR from \`/test-pipeline --fix-pr-mode\` run \`${RUN_ID}\`.

Healed ${applied_count} test failure(s); ${conflicted_count} conflict(s); ${failed_count} commit failure(s).

## Per-Issue Outcomes

| Issue | Test | Status | Commit |
|---|---|---|---|
$(for issue in $applied_issues; do
    echo "| #${issue} | ${test_id} | applied | ${commit_sha} |"
done)
$(for issue in $conflicted_issues; do
    echo "| #${issue} | ${test_id} | CONFLICTED (stale diff discarded) | — |"
done)

## Test plan

- [ ] CI passes on this branch
- [ ] Each commit's fix is minimal and tested
- [ ] No unrelated changes
- [ ] Manual review of any \`pipeline-fix-conflict\` Issues — those need fresh fix attempts

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOT
)

    gh pr create \
        --base "$BASE" \
        --head "$FIX_BRANCH" \
        --title "$PR_TITLE" \
        --body "$PR_BODY" \
        --label "pipeline-auto-fix"
fi
```

**Never auto-merge.** PR stays open for human review per `git-collaboration.md`.

---

## STEP 5: Return to original branch + return contract

```bash
git checkout "$ORIGINAL_BRANCH"
```

Return:
```json
{
  "result": "PR_OPENED" | "BLOCKED" | "DRY_RUN",
  "fix_branch": "pipeline-fixes/<run_id>",
  "pr_url": "https://github.com/.../pull/<N>",
  "pr_number": <N>,
  "applied": <count>,
  "conflicted": <count>,
  "failed": <count>,
  "no_push_dry_run": <bool>
}
```

---

## NON-NEGOTIABLE

1. **Never auto-merge.** PR stays open for human review per `git-collaboration.md` § "Review Before Merge".
2. **Always return to original branch on completion or failure.** The user invoked from a working branch; do NOT leave them on the fix branch.
3. **Hard-fail on push permission missing.** If `gh repo view --json viewerPermission` is below WRITE, return BLOCKED contract — do NOT silently skip the PR step.
4. **Branch naming is `pipeline-fixes/{run_id}` — no exceptions.** Predictable naming lets cleanup and follow-up tooling find these branches.
5. **Reuse `/serialize-fixes` for actual diff application.** This skill is a wrapper for branch + PR plumbing; it MUST NOT reimplement the atomic diff-apply protocol.

## CRITICAL RULES

- MUST verify caller's working branch is clean before creating fix branch (uncommitted changes would corrupt the new branch's diff)
- MUST NOT push to a branch named like a protected branch (main, master, develop, release/*)
- MUST emit `pipeline-auto-fix` label on the PR for filtering / dashboard tooling
- MUST surface `/serialize-fixes`'s conflict/failure counts in the PR body so reviewers see what was attempted but didn't land
