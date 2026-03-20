# Pre-Merge Checklist Details

## 1.1 Identify the Branch and PR

```bash
# If given a branch name, find the associated PR
BRANCH="${ARGUMENTS:-$(git branch --show-current)}"
PR_NUMBER=$(gh pr list --head "$BRANCH" --json number --jq '.[0].number')

# If given a PR number directly
# PR_NUMBER="$ARGUMENTS"
# BRANCH=$(gh pr view "$PR_NUMBER" --json headRefName --jq '.headRefName')

echo "Branch: $BRANCH"
echo "PR: #$PR_NUMBER"
```

## 1.2 Review Decision Check

Verify that the PR has been approved and no outstanding "request changes" reviews remain.

```bash
# Check overall review decision
gh pr view "$PR_NUMBER" --json reviewDecision --jq '.reviewDecision'
# Expected: "APPROVED"

# Check for any "CHANGES_REQUESTED" reviews that have not been dismissed
gh pr view "$PR_NUMBER" --json reviews --jq '
  .reviews
  | map(select(.state == "CHANGES_REQUESTED"))
  | length
'
# Expected: 0
```

If `reviewDecision` is not `APPROVED` or there are outstanding change requests:

```
BLOCKED: PR #<number> has not been approved.
- Review decision: <decision>
- Outstanding change requests: <count>

Action: Resolve all review threads and obtain approval before merging.
```

## 1.3 CI Status Check

```bash
# Check all CI checks
gh pr checks "$PR_NUMBER"

# Programmatic check — count failures
gh pr checks "$PR_NUMBER" --json name,state --jq '
  map(select(.state != "SUCCESS" and .state != "SKIPPED"))
  | length
'
# Expected: 0
```

If any checks are failing:

```
BLOCKED: CI checks are not passing.
Failing checks:
- <check-name>: <state>

Action: Fix failing checks before merging. Run the failing tests locally to diagnose.
```

## 1.4 Merge Conflict Check

```bash
# Check for merge conflicts
gh pr view "$PR_NUMBER" --json mergeable --jq '.mergeable'
# Expected: "MERGEABLE"

# Also verify locally
git fetch origin
BASE_BRANCH=$(gh pr view "$PR_NUMBER" --json baseRefName --jq '.baseRefName')
git checkout "$BRANCH"
git merge-tree $(git merge-base HEAD "origin/$BASE_BRANCH") HEAD "origin/$BASE_BRANCH"
```

If conflicts exist:

```
BLOCKED: Branch has merge conflicts with <base-branch>.
Conflicting files:
- <file1>
- <file2>

Action: Rebase onto <base-branch> and resolve conflicts:
  git checkout <branch>
  git fetch origin
  git rebase origin/<base-branch>
  # Resolve conflicts, then: git rebase --continue
  git push --force-with-lease
```

## 1.5 Branch Freshness Check

Ensure the branch is rebased on the latest base branch to avoid merging stale code.

```bash
# Check how many commits behind the base branch
BEHIND=$(git rev-list --count "HEAD..origin/$BASE_BRANCH")
echo "Commits behind $BASE_BRANCH: $BEHIND"
```

If the branch is behind:

```
WARNING: Branch is <N> commits behind <base-branch>.

Action: Rebase before merging:
  git fetch origin
  git rebase origin/<base-branch>
  git push --force-with-lease
```

## 1.6 Review Thread Resolution Check

```bash
# Check for unresolved review threads
gh api repos/:owner/:repo/pulls/$PR_NUMBER/comments --jq '
  map(select(.resolved == false or .resolved == null))
  | length
'
# Expected: 0
```
