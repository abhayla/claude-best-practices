# Commit History Cleanup

Clean up the commit history before merging. The goal is a readable history: meaningful
feature commits stay separate, fixup and review-response commits get squashed.

## 2.1 Analyze Commit History

```bash
# List all commits on the branch that are not on the base branch
git log "origin/$BASE_BRANCH..HEAD" --oneline --no-decorate
```

Example output:

```
f3a1b2c fix typo in error message
a7c9d4e address review: rename variable per feedback
1e5f8g9 feat: add input validation for user registration
b2d4e6f fix: handle edge case for empty email
c8a3f1d address review: add test for boundary condition
9d7e2a1 feat: add user registration endpoint
```

## 2.3 Perform the Squash

Use non-interactive rebase with fixup markers. Do NOT use `git rebase -i` (interactive mode
is not supported in automated workflows).

```bash
# Count commits to rebase
COMMIT_COUNT=$(git rev-list --count "origin/$BASE_BRANCH..HEAD")

# Mark fixup commits
git rebase --onto "origin/$BASE_BRANCH" "origin/$BASE_BRANCH" HEAD \
  --exec 'echo "Rebasing: $(git log --oneline -1)"'
```

For simple cases where all commits should be squashed into one:

```bash
# Soft reset to the merge base, then recommit
MERGE_BASE=$(git merge-base HEAD "origin/$BASE_BRANCH")
git reset --soft "$MERGE_BASE"
git commit -m "feat: add user registration with validation

- Add user registration endpoint with input validation
- Handle edge case for empty email
- Include boundary condition tests

PR #$PR_NUMBER"
```

For cases where some commits should remain separate:

```bash
# Use git rebase with autosquash
# First, rename fixup commits with the fixup! prefix
# Then rebase with --autosquash

# Step 1: Identify the fixup commits and their targets
# Step 2: Use git commit --fixup=<target-hash> to mark them
git commit --fixup=1e5f8g9 --allow-empty -m "fixup! feat: add input validation"

# Step 3: Rebase with autosquash
GIT_SEQUENCE_EDITOR=true git rebase --autosquash "origin/$BASE_BRANCH"
```

## 2.5 Force Push the Cleaned History

```bash
# Use --force-with-lease for safety (fails if someone else pushed)
git push --force-with-lease origin "$BRANCH"
```

## 2.6 Skip Conditions

Skip commit cleanup entirely if:
- The PR has only 1 commit (nothing to squash)
- The repository uses squash-merge on GitHub (cleanup happens automatically)
- The team explicitly prefers merge commits with full history

```bash
# Check if the repo uses squash merge by default
gh api repos/:owner/:repo --jq '.allow_squash_merge, .allow_merge_commit, .allow_rebase_merge'
```
