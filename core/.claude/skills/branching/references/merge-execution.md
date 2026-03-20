# Merge Execution

## 5.1 Document the Rollback Plan (Pre-Merge)

Before merging, record the rollback information as a PR comment so it is permanently
attached to the PR for future reference.

```bash
# Capture the current HEAD of the base branch (pre-merge state)
PRE_MERGE_SHA=$(git rev-parse "origin/$BASE_BRANCH")

# Post the rollback plan as a PR comment
gh pr comment "$PR_NUMBER" --body "## Rollback Plan

**Pre-merge SHA:** \`$PRE_MERGE_SHA\`

### If rollback is needed:

\`\`\`bash
git checkout $BASE_BRANCH
git pull origin $BASE_BRANCH
git revert -m 1 <merge-sha>
git push origin $BASE_BRANCH
\`\`\`"
```

## 5.2 Execute the Merge

```bash
# Merge the PR using GitHub CLI
# Use squash merge for clean history (adjust based on team preference)
gh pr merge "$PR_NUMBER" --squash --delete-branch

# Alternative merge strategies:
# gh pr merge "$PR_NUMBER" --merge --delete-branch    # Merge commit
# gh pr merge "$PR_NUMBER" --rebase --delete-branch   # Rebase merge
```

If `gh pr merge` fails:

```bash
# Common failure: branch protection rules require specific merge method
# Check which methods are allowed
gh api repos/:owner/:repo --jq '{
  allow_squash_merge,
  allow_merge_commit,
  allow_rebase_merge
}'

# Retry with the allowed method
```

## 5.3 Capture the Merge Commit

```bash
# Wait briefly for GitHub to process the merge
sleep 2

# Get the merge commit SHA
MERGE_SHA=$(gh pr view "$PR_NUMBER" --json mergeCommit --jq '.mergeCommit.oid')
echo "Merge commit: $MERGE_SHA"
```
