---
name: merge-strategy
description: >
  Recommend the optimal Git merge strategy (squash, merge commit, or rebase) based on
  branch type and team conventions. Runs a pre-merge checklist, executes the merge with
  the chosen strategy, performs post-merge smoke tests, and handles branch cleanup.
triggers:
  - /merge-strategy
  - /merge-plan
  - merge strategy
  - which merge strategy
  - how should I merge
allowed-tools: "Bash Read Grep Glob"
argument-hint: "<branch-name or PR-number> [--strategy squash|merge|rebase|auto]"
version: "1.0.0"
type: workflow
---

# Merge Strategy

Determine the optimal merge strategy for a branch, execute a pre-merge checklist, perform
the merge, run post-merge smoke tests, and clean up.

**Target:** $ARGUMENTS

---

## STEP 1: Detect Branch Type

Identify the branch type from its name prefix to drive the strategy recommendation.

```bash
BRANCH="${ARGUMENTS:-$(git branch --show-current)}"
BASE_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")

echo "Branch: $BRANCH"
echo "Base: $BASE_BRANCH"
```

### 1.1 Branch Classification

| Pattern | Branch Type | Description |
|---------|------------|-------------|
| `feat/*`, `feature/*` | Feature | New functionality, isolated work |
| `release/*`, `releases/*` | Release | Stabilization before a version cut |
| `hotfix/*`, `fix/*` (targeting production) | Hotfix | Urgent production fix |
| `develop`, `dev`, `staging` | Long-lived | Shared integration branch |
| `chore/*`, `refactor/*`, `docs/*` | Maintenance | Housekeeping, non-functional changes |

```bash
case "$BRANCH" in
  feat/*|feature/*)   BRANCH_TYPE="feature" ;;
  release/*|releases/*) BRANCH_TYPE="release" ;;
  hotfix/*)           BRANCH_TYPE="hotfix" ;;
  develop|dev|staging) BRANCH_TYPE="long-lived" ;;
  fix/*)              BRANCH_TYPE="feature" ;;
  chore/*|refactor/*|docs/*) BRANCH_TYPE="maintenance" ;;
  *)                  BRANCH_TYPE="feature" ;;
esac
echo "Detected branch type: $BRANCH_TYPE"
```

---

## STEP 2: Recommend Merge Strategy

Select the merge strategy based on branch type. If the user passed `--strategy`, use that
override instead.

### 2.1 Strategy Matrix

| Branch Type | Strategy | Rationale |
|------------|----------|-----------|
| **Feature** | Squash merge | Collapses WIP/fixup commits into one clean commit on the base branch. Keeps history linear and readable. |
| **Release** | Merge commit | Preserves the full release branch history. The merge commit marks the exact point a release joined the mainline. |
| **Hotfix** | Merge commit | Preserves provenance of the urgent fix. The merge commit is a clear audit marker for incident review. |
| **Long-lived** | Rebase + merge commit | Rebase onto the target first to linearize, then merge with a commit to mark the integration point. |
| **Maintenance** | Squash merge | Same rationale as feature branches; housekeeping commits do not need individual history. |

```bash
case "$BRANCH_TYPE" in
  feature|maintenance)  STRATEGY="squash" ;;
  release)              STRATEGY="merge" ;;
  hotfix)               STRATEGY="merge" ;;
  long-lived)           STRATEGY="rebase-merge" ;;
  *)                    STRATEGY="squash" ;;
esac

echo "Recommended strategy: $STRATEGY"
```

### 2.2 Override Check

If the user explicitly passed `--strategy`, honor it over the automatic recommendation.
If the repository enforces a single merge method via branch protection, detect and respect that.

```bash
# Check which merge methods the repo allows
gh api repos/:owner/:repo --jq '{
  allow_squash_merge,
  allow_merge_commit,
  allow_rebase_merge
}' 2>/dev/null || echo "Could not query repo settings (local-only or no gh auth)."
```

---

## STEP 3: Pre-Merge Checklist

Block the merge if ANY check fails. Run all checks before reporting results.

### 3.1 Checks

| # | Check | Command | Pass Condition |
|---|-------|---------|---------------|
| 1 | CI green | `gh pr checks $PR_NUMBER` | All checks SUCCESS or SKIPPED |
| 2 | Reviews approved | `gh pr view $PR_NUMBER --json reviewDecision` | `APPROVED` |
| 3 | Conflicts resolved | `gh pr view $PR_NUMBER --json mergeable` | `MERGEABLE` |
| 4 | Branch up-to-date | `git rev-list --count HEAD..origin/$BASE_BRANCH` | 0 |
| 5 | No unresolved threads | `gh api .../pulls/$PR_NUMBER/comments` | 0 unresolved |

```bash
PR_NUMBER=$(gh pr list --head "$BRANCH" --json number --jq '.[0].number' 2>/dev/null)

PASS=true

# 1. CI green
FAILING=$(gh pr checks "$PR_NUMBER" --json state --jq '[.[] | select(.state != "SUCCESS" and .state != "SKIPPED")] | length' 2>/dev/null)
[ "${FAILING:-1}" -ne 0 ] && echo "FAIL: CI checks not passing ($FAILING failing)" && PASS=false

# 2. Reviews approved
DECISION=$(gh pr view "$PR_NUMBER" --json reviewDecision --jq '.reviewDecision' 2>/dev/null)
[ "$DECISION" != "APPROVED" ] && echo "FAIL: Review decision is $DECISION, not APPROVED" && PASS=false

# 3. Conflicts resolved
MERGEABLE=$(gh pr view "$PR_NUMBER" --json mergeable --jq '.mergeable' 2>/dev/null)
[ "$MERGEABLE" != "MERGEABLE" ] && echo "FAIL: Branch is not mergeable ($MERGEABLE)" && PASS=false

# 4. Branch up-to-date
git fetch origin "$BASE_BRANCH" --quiet
BEHIND=$(git rev-list --count "HEAD..origin/$BASE_BRANCH" 2>/dev/null)
[ "${BEHIND:-1}" -gt 0 ] && echo "WARN: Branch is $BEHIND commits behind $BASE_BRANCH — rebase recommended" && PASS=false

if [ "$PASS" = true ]; then
  echo "Pre-merge checklist: ALL PASSED"
else
  echo "Pre-merge checklist: BLOCKED — resolve failures above before merging"
fi
```

---

## STEP 4: Execute Merge

Perform the merge using the selected strategy. Record the merge commit SHA for post-merge steps.

```bash
case "$STRATEGY" in
  squash)
    gh pr merge "$PR_NUMBER" --squash --delete-branch
    ;;
  merge)
    gh pr merge "$PR_NUMBER" --merge --delete-branch
    ;;
  rebase-merge)
    # Rebase first, then merge commit
    git fetch origin "$BASE_BRANCH"
    git rebase "origin/$BASE_BRANCH"
    git push --force-with-lease origin "$BRANCH"
    gh pr merge "$PR_NUMBER" --merge --delete-branch
    ;;
esac

MERGE_SHA=$(gh pr view "$PR_NUMBER" --json mergeCommit --jq '.mergeCommit.oid' 2>/dev/null)
echo "Merged with strategy: $STRATEGY"
echo "Merge SHA: $MERGE_SHA"
```

---

## STEP 5: Post-Merge Smoke Tests

Verify the base branch is healthy after the merge lands.

### 5.1 Update Local Base Branch

```bash
git checkout "$BASE_BRANCH"
git pull origin "$BASE_BRANCH"
```

### 5.2 Run Smoke Tests on Main

```bash
# Detect test runner and execute
if [ -f package.json ]; then
  npm test
elif [ -f pytest.ini ] || [ -f pyproject.toml ] || [ -f setup.cfg ]; then
  python -m pytest --tb=short -q
elif [ -f build.gradle ] || [ -f build.gradle.kts ]; then
  ./gradlew test
elif [ -f Cargo.toml ]; then
  cargo test
elif [ -f go.mod ]; then
  go test ./...
else
  echo "WARNING: No test runner detected. Run smoke tests manually."
fi
```

### 5.3 Verify Deployment Pipeline Triggered

```bash
# Check if a deployment or CI workflow fired on the base branch
sleep 3
gh run list --branch "$BASE_BRANCH" --limit 3 --json name,status,conclusion \
  --jq '.[] | "\(.name): \(.status) (\(.conclusion // "in progress"))"' 2>/dev/null \
  || echo "No workflow runs detected (or gh not configured)."
```

### 5.4 Notify Team

```bash
# Comment on the PR with the post-merge status
gh pr comment "$PR_NUMBER" --body "Post-merge smoke tests passed on $BASE_BRANCH. Merge SHA: \`$MERGE_SHA\`." 2>/dev/null
```

### 5.5 Handle Failures

If smoke tests fail after the merge:

```
POST-MERGE FAILURE
  1. Check if the failure is caused by this merge or pre-existing.
  2. If caused by this merge, revert immediately:
       git revert -m 1 <MERGE_SHA>
       git push origin <BASE_BRANCH>
  3. If pre-existing, file a separate issue and proceed.
```

---

## STEP 6: Branch Cleanup

Remove all traces of the merged branch.

```bash
# Delete local branch
git branch -d "$BRANCH" 2>/dev/null || echo "Local branch already removed."

# Delete remote branch (gh pr merge --delete-branch may have done this)
git push origin --delete "$BRANCH" 2>/dev/null || echo "Remote branch already removed."

# Prune stale remote-tracking references
git fetch --prune

# Update related issues — close any linked issues that did not auto-close
CLOSING_ISSUES=$(gh pr view "$PR_NUMBER" --json closingIssuesReferences --jq '[.closingIssuesReferences[].number] | join(" ")' 2>/dev/null)
if [ -n "$CLOSING_ISSUES" ]; then
  for ISSUE in $CLOSING_ISSUES; do
    STATE=$(gh issue view "$ISSUE" --json state --jq '.state' 2>/dev/null)
    if [ "$STATE" != "CLOSED" ]; then
      gh issue close "$ISSUE" -c "Closed by PR #$PR_NUMBER"
    fi
  done
  echo "Linked issues closed: $CLOSING_ISSUES"
fi

echo "Cleanup complete."
```

---

## Summary Template

```
=== Merge Strategy Report ===

Branch:     <BRANCH> -> <BASE_BRANCH>
Type:       <BRANCH_TYPE>
Strategy:   <STRATEGY>
PR:         #<PR_NUMBER>
Merge SHA:  <MERGE_SHA>

Pre-merge checklist:  PASSED
Smoke tests:          PASSED
Deployment pipeline:  triggered / not configured
Branch cleanup:       done
Linked issues closed: #<issue1>, #<issue2> / none

Rollback (if needed):
  git revert -m 1 <MERGE_SHA> && git push origin <BASE_BRANCH>

=== Done ===
```

---

## MUST DO

- Always run the full pre-merge checklist before executing the merge — never skip checks
- Always select the strategy from the matrix unless the user provides an explicit override
- Always run smoke tests on the base branch after the merge lands — a green PR does not guarantee green on main
- Always verify the deployment pipeline triggered (if CD is configured) and report its status
- Always delete both local and remote branches after a successful merge
- Always close linked issues that did not auto-close after the merge
- Always use `--force-with-lease` instead of `--force` when pushing rebased branches
- Always use `git branch -d` (lowercase) for local deletion — it refuses to delete unmerged work

## MUST NOT DO

- MUST NOT merge when any pre-merge check is failing — fix the check first, do not bypass
- MUST NOT use a squash merge for release or hotfix branches — their history must be preserved for audit
- MUST NOT skip post-merge smoke tests — failures caught here prevent broken deployments
- MUST NOT leave orphaned remote branches after merge — they accumulate and obscure active work
- MUST NOT use `git push --force` — use `--force-with-lease` to prevent overwriting concurrent pushes
- MUST NOT auto-select a strategy for an unrecognized branch pattern without telling the user which default was chosen
- MUST NOT ignore post-merge test failures — either fix forward or revert immediately
- MUST NOT delete a branch with `git branch -D` (uppercase) unless unmerged work has been explicitly confirmed disposable
