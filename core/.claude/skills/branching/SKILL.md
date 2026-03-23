---
name: branching
description: >
  Manage the full branch lifecycle from creation through merge and cleanup. Creates feature
  branches with naming conventions, handles pre-merge checklists, commit cleanup, changelog
  generation, and post-merge verification. Use when starting a feature branch, finalizing
  a PR, or cleaning up after merge.
triggers:
  - /branching
  - /branch
  - /new-branch
  - /finish-branch
  - /merge-branch
  - /finalize
allowed-tools: "Bash Read Write Edit Grep Glob"
argument-hint: "'create <feature-name>' | 'finish <branch-name or PR-number>'"
version: "1.0.1"
type: workflow
---

# Branching — Full Branch Lifecycle

Manage the complete branch lifecycle: create feature branches with conventions, and finish
them with pre-merge checks, merge, verification, and cleanup.

**Command:** $ARGUMENTS

---

## STEP 0: Branch Creation

If the command starts with `create`, `new`, or `start`, create a new feature branch.

### 0.1 Verify Clean Working Tree

```bash
# Ensure no uncommitted changes
if [ -n "$(git status --porcelain)" ]; then
  echo "ERROR: Working tree has uncommitted changes."
  echo "Action: Commit or stash changes before creating a new branch."
  git status --short
  exit 1
fi

# Ensure we're on the latest base branch
git checkout main 2>/dev/null || git checkout master
git pull origin $(git branch --show-current)
```

### 0.4 Set Upstream

```bash
git push -u origin "$BRANCH_NAME"
echo "Upstream set: origin/$BRANCH_NAME"
```

## STEP 1: Pre-Merge Checklist

Before merging anything, verify every gate. Block the merge if ANY check fails.

Checks: review approval, CI status, merge conflicts, branch freshness, review thread resolution.

**Read:** `references/pre-merge-checklist.md` for all gate check commands and expected outputs.

---

## STEP 2: Commit History Cleanup

Clean up the commit history before merging — squash fixup/review-response commits while
keeping meaningful feature commits separate.

**Read:** `references/commit-history-cleanup.md` for squash strategies, autosquash usage, and skip conditions.

---

## STEP 3: Changelog Generation

Auto-generate a changelog entry from PR metadata (title, labels, category).

**Read:** `references/changelog-generation.md` for PR parsing, category detection, and entry formatting.

---

## STEP 4: Worktree Cleanup

If the branch was developed in a git worktree, clean it up before merging.

### 4.1 Detect Worktree Usage

```bash
# Check if the current directory is a linked worktree
if [ -f .git ]; then
  # .git is a file (not a directory) in linked worktrees
  WORKTREE_PATH=$(pwd)
  MAIN_REPO=$(git rev-parse --git-common-dir | sed 's|/\.git$||')
  IS_WORKTREE=true
  echo "Current directory is a linked worktree: $WORKTREE_PATH"
  echo "Main repository: $MAIN_REPO"
else
  IS_WORKTREE=false
  echo "Not in a linked worktree — skipping worktree cleanup."
fi

# Also check if there are any worktrees associated with this branch
git worktree list | grep "$BRANCH" && echo "Found worktree for branch $BRANCH"
```

### 4.5 Verify Worktree State

```bash
# List remaining worktrees — should not include the cleaned-up branch
git worktree list
```

---

## STEP 5: Perform the Merge

Execute the actual merge operation with rollback plan documented as a PR comment.

**Read:** `references/merge-execution.md` for rollback plan posting, merge strategies, and commit capture.

---

## STEP 6: Post-Merge Verification

After the merge lands on the base branch, verify tests, build, and key metrics.

**Read:** `references/post-merge-verification.md` for test runner detection, build verification, and metrics comparison.

---

## STEP 7: Branch Cleanup

After successful post-merge verification, remove all traces of the feature branch.

### 7.1 Delete Local Branch

```bash
git branch -d "$BRANCH" 2>/dev/null || echo "Local branch already deleted or not found."
```

### 7.2 Delete Remote Branch

```bash
git push origin --delete "$BRANCH" 2>/dev/null || echo "Remote branch already deleted."
```

### 7.3 Prune Stale References

```bash
git fetch --prune
```

### 7.4 Verify Cleanup

```bash
# Confirm the branch is gone locally and remotely
git branch --list "$BRANCH"
git ls-remote --heads origin "$BRANCH"
echo "Branch cleanup complete."
```

---

## STEP 8: Cross-PR Dependency Resolution

After the merge, check if this PR was blocking other work and unblock it.

**Read:** `references/cross-pr-dependencies.md` for linked issue closure, dependent PR detection, and notification.

---

## STEP 9: Release Tagging

> **Reference:** See [references/release-tagging.md](references/release-tagging.md) for full details.

---

## STEP 10: Deployment Awareness

> **Reference:** See [references/deployment-awareness.md](references/deployment-awareness.md) for full details.

---

## MUST DO

- Always run the full pre-merge checklist before merging — never skip checks even if "it looks fine"
- Always document the rollback plan as a PR comment before merging — not after
- Always verify post-merge by running tests and build on the updated base branch
- Always clean up both local and remote branches after a successful merge
- Always use `--force-with-lease` instead of `--force` when pushing rebased branches — it prevents overwriting someone else's work
- Always close linked issues after merge if GitHub did not auto-close them
- Always use `git branch -d` (lowercase d) for deletion — it refuses to delete unmerged branches, which is a safety net
- Always notify dependent PRs when their blocker is resolved

## MUST NOT DO

- MUST NOT merge a PR that has outstanding "changes requested" reviews — get them resolved or dismissed first
- MUST NOT merge when CI checks are failing — fix the checks, do not bypass them
- MUST NOT use `git push --force` — use `--force-with-lease` instead to prevent overwriting concurrent pushes
- MUST NOT skip post-merge verification — a green CI on the PR does not guarantee green on the base branch after merge
- MUST NOT leave orphaned branches — they accumulate and make the branch list unusable
- MUST NOT delete a branch with `git branch -D` (uppercase D) unless you have explicitly confirmed the unmerged work can be discarded
- MUST NOT create a release tag without verifying that tests pass on the tagged commit
- MUST NOT ignore deployment failures after merge — either fix forward or revert immediately
