---
name: branching
description: >
  Full branch lifecycle management — from creation through merge and cleanup. Creates feature
  branches with naming conventions, and handles the "last mile" after code review: pre-merge
  checklist, commit cleanup, changelog generation, merge execution, post-merge verification,
  branch/worktree cleanup, rollback plans, cross-PR dependencies, and release tagging.
triggers:
  - /branching
  - /branch
  - /new-branch
  - /finish-branch
  - /merge-branch
  - /finalize
allowed-tools: "Bash Read Write Edit Grep Glob"
argument-hint: "'create <feature-name>' | 'finish <branch-name or PR-number>'"
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

### 0.2 Determine Branch Name

Apply naming conventions based on the task type:

| Task Type | Prefix | Example |
|-----------|--------|---------|
| New feature | `feat/` | `feat/user-registration` |
| Bug fix | `fix/` | `fix/login-crash-empty-email` |
| Refactoring | `refactor/` | `refactor/extract-auth-service` |
| Documentation | `docs/` | `docs/api-reference-update` |
| Chore/maintenance | `chore/` | `chore/upgrade-dependencies` |
| Hotfix (production) | `hotfix/` | `hotfix/payment-timeout` |

Rules for branch names:
- Lowercase, kebab-case
- Include ticket/issue number if available: `feat/PROJ-123-user-registration`
- Max 50 characters
- Descriptive but concise

### 0.3 Create the Branch

```bash
BRANCH_NAME="<prefix>/<descriptive-name>"
BASE_BRANCH=$(git branch --show-current)

git checkout -b "$BRANCH_NAME"
echo "Created branch: $BRANCH_NAME (from $BASE_BRANCH)"
```

### 0.4 Set Upstream

```bash
git push -u origin "$BRANCH_NAME"
echo "Upstream set: origin/$BRANCH_NAME"
```

### 0.5 Branch Creation Summary

```
Branch Created:
  Name:   <BRANCH_NAME>
  Base:   <BASE_BRANCH>
  Remote: origin/<BRANCH_NAME>

Next steps:
  - Start implementing with /implement or /executing-plans
  - When ready for review, use /request-code-review
  - When approved, use /branching finish <BRANCH_NAME>
```

If the command starts with `finish`, `merge`, or `finalize`, proceed to Step 1.

---

## STEP 1: Pre-Merge Checklist

Before merging anything, verify every gate. Block the merge if ANY check fails.

### 1.1 Identify the Branch and PR

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

### 1.2 Review Decision Check

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

### 1.3 CI Status Check

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

### 1.4 Merge Conflict Check

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

### 1.5 Branch Freshness Check

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

### 1.6 Review Thread Resolution Check

```bash
# Check for unresolved review threads
gh api repos/:owner/:repo/pulls/$PR_NUMBER/comments --jq '
  map(select(.resolved == false or .resolved == null))
  | length
'
# Expected: 0
```

### 1.7 Checklist Summary

After all checks pass, output:

```
Pre-Merge Checklist: PASSED
- Review decision:    APPROVED
- Change requests:    0 outstanding
- CI checks:          all passing
- Merge conflicts:    none
- Branch freshness:   up to date with <base-branch>
- Review threads:     all resolved

Ready to merge PR #<number> (<branch> -> <base-branch>).
```

---

## STEP 2: Commit History Cleanup

Clean up the commit history before merging. The goal is a readable history: meaningful
feature commits stay separate, fixup and review-response commits get squashed.

### 2.1 Analyze Commit History

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

### 2.2 Categorize Commits

Separate commits into two categories:

| Category | Pattern | Action |
|----------|---------|--------|
| **Keep** | `feat:`, `fix:`, `refactor:`, `perf:`, `docs:` | Preserve as individual commits |
| **Squash** | `address review`, `fix typo`, `fixup`, `wip`, `oops`, `nit` | Squash into the nearest preceding "keep" commit |

From the example above:

```
KEEP:   9d7e2a1 feat: add user registration endpoint
SQUASH: c8a3f1d address review: add test for boundary condition  -> into 9d7e2a1
KEEP:   b2d4e6f fix: handle edge case for empty email
KEEP:   1e5f8g9 feat: add input validation for user registration
SQUASH: a7c9d4e address review: rename variable per feedback     -> into 1e5f8g9
SQUASH: f3a1b2c fix typo in error message                        -> into 1e5f8g9
```

### 2.3 Perform the Squash

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

### 2.4 Generate Clean Commit Message

For the squashed commit, generate a message that summarizes the full PR:

```
<type>: <concise summary of the change>

<bullet points covering what was done>

- <change 1>
- <change 2>
- <change 3>

PR: #<PR-number>
Co-authored-by: <reviewers who contributed suggestions>
```

### 2.5 Force Push the Cleaned History

```bash
# Use --force-with-lease for safety (fails if someone else pushed)
git push --force-with-lease origin "$BRANCH"
```

### 2.6 Skip Conditions

Skip commit cleanup entirely if:
- The PR has only 1 commit (nothing to squash)
- The repository uses squash-merge on GitHub (cleanup happens automatically)
- The team explicitly prefers merge commits with full history

```bash
# Check if the repo uses squash merge by default
gh api repos/:owner/:repo --jq '.allow_squash_merge, .allow_merge_commit, .allow_rebase_merge'
```

---

## STEP 3: Changelog Generation

Auto-generate a changelog entry from the PR metadata.

### 3.1 Parse PR Information

```bash
# Extract PR metadata
PR_TITLE=$(gh pr view "$PR_NUMBER" --json title --jq '.title')
PR_BODY=$(gh pr view "$PR_NUMBER" --json body --jq '.body')
PR_LABELS=$(gh pr view "$PR_NUMBER" --json labels --jq '[.labels[].name] | join(",")')
PR_URL=$(gh pr view "$PR_NUMBER" --json url --jq '.url')
PR_AUTHOR=$(gh pr view "$PR_NUMBER" --json author --jq '.author.login')
```

### 3.2 Categorize the Change

Map the PR to a Keep a Changelog category based on the PR title prefix and labels:

| PR Title Prefix / Label | Changelog Category |
|--------------------------|-------------------|
| `feat:`, `feature`, `enhancement` | Added |
| `fix:`, `bug`, `bugfix` | Fixed |
| `refactor:`, `perf:`, `improvement` | Changed |
| `deprecate:` | Deprecated |
| `remove:`, `breaking` | Removed |
| `security:`, `vulnerability` | Security |

```bash
# Determine category from PR title
if echo "$PR_TITLE" | grep -qi '^feat'; then
  CATEGORY="Added"
elif echo "$PR_TITLE" | grep -qi '^fix'; then
  CATEGORY="Fixed"
elif echo "$PR_TITLE" | grep -qi '^refactor\|^perf\|^improve'; then
  CATEGORY="Changed"
elif echo "$PR_TITLE" | grep -qi '^remove\|^breaking\|BREAKING'; then
  CATEGORY="Removed"
elif echo "$PR_TITLE" | grep -qi '^security'; then
  CATEGORY="Security"
else
  CATEGORY="Changed"
fi
```

### 3.3 Generate the Entry

```bash
# Format: - <description> ([#<number>](<url>))
CHANGELOG_ENTRY="- ${PR_TITLE#*: } ([#${PR_NUMBER}](${PR_URL}))"
echo "$CHANGELOG_ENTRY"
```

Example output:

```
- Add user registration with input validation ([#142](https://github.com/org/repo/pull/142))
```

### 3.4 Insert into CHANGELOG.md

If a `CHANGELOG.md` exists, insert the entry under the appropriate section. If the
`[Unreleased]` section does not have the right category, create it.

```bash
if [ -f CHANGELOG.md ]; then
  # Check if [Unreleased] section exists
  if grep -q '## \[Unreleased\]' CHANGELOG.md; then
    # Check if the category subsection exists under [Unreleased]
    if grep -A 50 '## \[Unreleased\]' CHANGELOG.md | grep -q "### $CATEGORY"; then
      # Insert after the category header
      sed -i "/### $CATEGORY/a\\$CHANGELOG_ENTRY" CHANGELOG.md
    else
      # Add the category section under [Unreleased]
      sed -i "/## \[Unreleased\]/a\\\n### $CATEGORY\n$CHANGELOG_ENTRY" CHANGELOG.md
    fi
  else
    # Add [Unreleased] section at the top (after the title)
    sed -i "1a\\\n## [Unreleased]\n\n### $CATEGORY\n$CHANGELOG_ENTRY" CHANGELOG.md
  fi

  echo "Changelog updated with entry under [$CATEGORY]"
  git add CHANGELOG.md
  git commit -m "docs: add changelog entry for PR #$PR_NUMBER"
else
  echo "No CHANGELOG.md found — skipping changelog generation."
  echo "To start a changelog, create CHANGELOG.md following https://keepachangelog.com"
fi
```

### 3.5 Changelog Entry Examples

```markdown
## [Unreleased]

### Added
- Add user registration with input validation ([#142](https://github.com/org/repo/pull/142))
- Add email verification flow ([#138](https://github.com/org/repo/pull/138))

### Fixed
- Fix crash on login when email is null ([#140](https://github.com/org/repo/pull/140))

### Changed
- Improve database query performance for user lookups ([#139](https://github.com/org/repo/pull/139))
```

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

### 4.2 Ensure Work is Committed

```bash
if [ "$IS_WORKTREE" = true ]; then
  # Check for uncommitted changes
  if [ -n "$(git status --porcelain)" ]; then
    echo "ERROR: Worktree has uncommitted changes. Commit or stash before cleanup."
    git status --short
    exit 1
  fi
fi
```

### 4.3 Clean Up Worktree-Specific Files

```bash
if [ "$IS_WORKTREE" = true ]; then
  # Remove worktree-specific env files that should not persist
  WORKTREE_ENV_FILES=(.env.local .env.development.local node_modules/.cache)
  for f in "${WORKTREE_ENV_FILES[@]}"; do
    if [ -e "$WORKTREE_PATH/$f" ]; then
      echo "Removing worktree-specific file: $f"
      rm -rf "$WORKTREE_PATH/$f"
    fi
  done
fi
```

### 4.4 Navigate to Main Repo and Remove Worktree

```bash
if [ "$IS_WORKTREE" = true ]; then
  # Switch to the main repository before removing the worktree
  cd "$MAIN_REPO"

  # Remove the worktree
  git worktree remove "$WORKTREE_PATH"
  echo "Worktree removed: $WORKTREE_PATH"

  # Prune stale worktree references
  git worktree prune
  echo "Stale worktree references pruned."

  # Verify the worktree directory is gone
  if [ -d "$WORKTREE_PATH" ]; then
    echo "WARNING: Worktree directory still exists at $WORKTREE_PATH"
    echo "Manual cleanup may be needed."
  else
    echo "Worktree directory confirmed removed."
  fi
fi
```

### 4.5 Verify Worktree State

```bash
# List remaining worktrees — should not include the cleaned-up branch
git worktree list
```

---

## STEP 5: Perform the Merge

Execute the actual merge operation.

### 5.1 Document the Rollback Plan (Pre-Merge)

Before merging, record the rollback information as a PR comment so it is permanently
attached to the PR for future reference.

```bash
# Capture the current HEAD of the base branch (pre-merge state)
PRE_MERGE_SHA=$(git rev-parse "origin/$BASE_BRANCH")

# Post the rollback plan as a PR comment
gh pr comment "$PR_NUMBER" --body "$(cat <<EOF
## Rollback Plan

**Pre-merge SHA:** \`$PRE_MERGE_SHA\`

### If rollback is needed:

\`\`\`bash
# Revert the merge commit (replace <merge-sha> with the actual merge commit hash)
git checkout $BASE_BRANCH
git pull origin $BASE_BRANCH
git revert -m 1 <merge-sha>
git push origin $BASE_BRANCH
\`\`\`

### Additional rollback steps:
- [ ] Database migrations to revert: _(list if applicable)_
- [ ] Config changes to undo: _(list if applicable)_
- [ ] Feature flags to disable: _(list if applicable)_
- [ ] Cache invalidation needed: _(yes/no)_

---
_Generated by /branching_
EOF
)"
```

### 5.2 Execute the Merge

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

### 5.3 Capture the Merge Commit

```bash
# Wait briefly for GitHub to process the merge
sleep 2

# Get the merge commit SHA
MERGE_SHA=$(gh pr view "$PR_NUMBER" --json mergeCommit --jq '.mergeCommit.oid')
echo "Merge commit: $MERGE_SHA"

# Update the rollback plan comment with the actual merge SHA
gh pr comment "$PR_NUMBER" --body "$(cat <<EOF
## Merge Complete

**Merge commit:** \`$MERGE_SHA\`

### Revert command (if needed):
\`\`\`bash
git checkout $BASE_BRANCH && git pull
git revert -m 1 $MERGE_SHA
git push origin $BASE_BRANCH
\`\`\`
EOF
)"
```

---

## STEP 6: Post-Merge Verification

After the merge lands on the base branch, verify that everything is healthy.

### 6.1 Update Local Base Branch

```bash
git checkout "$BASE_BRANCH"
git pull origin "$BASE_BRANCH"
echo "Local $BASE_BRANCH updated to $(git rev-parse --short HEAD)"
```

### 6.2 Run the Full Test Suite

```bash
# Detect the test runner and run tests
if [ -f package.json ]; then
  npm test
elif [ -f pytest.ini ] || [ -f pyproject.toml ] || [ -f setup.cfg ]; then
  python -m pytest
elif [ -f build.gradle ] || [ -f build.gradle.kts ]; then
  ./gradlew test
elif [ -f Cargo.toml ]; then
  cargo test
elif [ -f go.mod ]; then
  go test ./...
elif [ -f Makefile ] && grep -q '^test:' Makefile; then
  make test
else
  echo "WARNING: Could not detect test runner. Run tests manually."
fi
```

### 6.3 Run the Build

```bash
# Detect the build system and run build
if [ -f package.json ]; then
  npm run build 2>/dev/null || echo "No build script defined — skipping."
elif [ -f build.gradle ] || [ -f build.gradle.kts ]; then
  ./gradlew build
elif [ -f Cargo.toml ]; then
  cargo build
elif [ -f go.mod ]; then
  go build ./...
elif [ -f Makefile ] && grep -q '^build:' Makefile; then
  make build
else
  echo "No build system detected — skipping build verification."
fi
```

### 6.4 Handle Verification Failures

If tests or build fail after the merge:

```
POST-MERGE FAILURE DETECTED

Failed step: <tests|build>
Error output:
<error details>

IMMEDIATE ACTIONS:
1. Do NOT panic — this is why we documented the rollback plan.
2. Investigate whether the failure is caused by the merge or pre-existing.
3. If caused by the merge, revert immediately:

   git revert -m 1 <MERGE_SHA>
   git push origin <BASE_BRANCH>

4. If pre-existing, file a separate issue and proceed.
```

### 6.5 Compare Key Metrics (Optional)

```bash
# If the project tracks bundle size
if [ -f package.json ] && grep -q '"size"' package.json; then
  npm run size 2>/dev/null
fi

# Count total tests (rough check for test count regression)
if [ -f package.json ]; then
  npm test 2>&1 | grep -E 'Tests?:|passed|failed' | tail -3
elif [ -f pytest.ini ] || [ -f pyproject.toml ]; then
  python -m pytest --co -q 2>/dev/null | tail -1
fi
```

### 6.6 Verification Report

```
Post-Merge Verification: PASSED
- Branch:     <base-branch> @ <short-sha>
- Tests:      <X> passed, 0 failed
- Build:      success
- Merge SHA:  <merge-sha>
- Regressions: none detected
```

---

## STEP 7: Branch Cleanup

After successful post-merge verification, remove all traces of the feature branch.

### 7.1 Delete Local Branch

```bash
# Delete the local branch (safe — refuses if not fully merged)
git branch -d "$BRANCH" 2>/dev/null || echo "Local branch already deleted or not found."
```

### 7.2 Delete Remote Branch

```bash
# Delete the remote branch (gh pr merge --delete-branch may have done this already)
git push origin --delete "$BRANCH" 2>/dev/null || echo "Remote branch already deleted."
```

### 7.3 Prune Stale References

```bash
# Remove stale remote-tracking references
git fetch --prune
```

### 7.4 Verify Cleanup

```bash
# Confirm the branch is gone locally
git branch --list "$BRANCH"
# Expected: empty output

# Confirm the branch is gone on remote
git ls-remote --heads origin "$BRANCH"
# Expected: empty output

echo "Branch cleanup complete."
```

---

## STEP 8: Cross-PR Dependency Resolution

After the merge, check if this PR was blocking other work and unblock it.

### 8.1 Check for Linked Issues

```bash
# Get issues that this PR closes
CLOSING_ISSUES=$(gh pr view "$PR_NUMBER" --json closingIssuesReferences --jq '
  [.closingIssuesReferences[].number] | join(" ")
')

if [ -n "$CLOSING_ISSUES" ]; then
  echo "This PR closes issues: $CLOSING_ISSUES"
  for ISSUE in $CLOSING_ISSUES; do
    # Verify the issue is closed
    STATE=$(gh issue view "$ISSUE" --json state --jq '.state')
    echo "  Issue #$ISSUE: $STATE"

    # If not auto-closed, close it manually
    if [ "$STATE" != "CLOSED" ]; then
      gh issue close "$ISSUE" -c "Closed by PR #$PR_NUMBER"
    fi
  done
else
  echo "No linked issues found."
fi
```

### 8.2 Check for Dependent PRs

```bash
# Search for PRs that mention this PR or its branch as a dependency
DEPENDENT_PRS=$(gh pr list --search "depends on #$PR_NUMBER OR blocked by #$PR_NUMBER" \
  --json number,title --jq '.[] | "#\(.number): \(.title)"')

if [ -n "$DEPENDENT_PRS" ]; then
  echo "Dependent PRs that may now be unblocked:"
  echo "$DEPENDENT_PRS"
  echo ""
  echo "Action: Review these PRs — they may be ready to merge now."
else
  echo "No dependent PRs found."
fi
```

### 8.3 Notify Dependent PRs

```bash
# Comment on dependent PRs to notify them that the blocker is resolved
if [ -n "$DEPENDENT_PRS" ]; then
  echo "$DEPENDENT_PRS" | while IFS= read -r line; do
    DEP_PR=$(echo "$line" | grep -oP '#\K\d+')
    gh pr comment "$DEP_PR" --body "Dependency resolved: PR #$PR_NUMBER has been merged. This PR may now be unblocked."
  done
fi
```

---

## STEP 9: Release Tagging

If this merge completes a milestone or the team follows release-on-merge practices,
handle version tagging.

### 9.1 Determine if a Release Tag is Needed

```bash
# Check if the PR has a release-related label
RELEASE_LABEL=$(gh pr view "$PR_NUMBER" --json labels --jq '
  [.labels[].name] | map(select(test("release|version|milestone"))) | first // empty
')

# Check if the project has existing tags
LATEST_TAG=$(git describe --tags --abbrev=0 2>/dev/null || echo "none")
echo "Latest tag: $LATEST_TAG"
echo "Release label: ${RELEASE_LABEL:-none}"
```

### 9.2 Suggest Semantic Version

Based on the type of changes in the PR, suggest the appropriate version bump:

| Change Type | Version Bump | Example |
|-------------|-------------|---------|
| Breaking changes (`BREAKING CHANGE`, `remove:`) | Major | v1.0.0 -> v2.0.0 |
| New features (`feat:`) | Minor | v1.0.0 -> v1.1.0 |
| Bug fixes, patches (`fix:`, `perf:`) | Patch | v1.0.0 -> v1.0.1 |

```bash
if [ "$LATEST_TAG" != "none" ]; then
  # Parse the current version
  MAJOR=$(echo "$LATEST_TAG" | sed 's/v//' | cut -d. -f1)
  MINOR=$(echo "$LATEST_TAG" | sed 's/v//' | cut -d. -f2)
  PATCH=$(echo "$LATEST_TAG" | sed 's/v//' | cut -d. -f3)

  # Determine bump type from PR title
  if echo "$PR_TITLE" | grep -qi 'BREAKING\|remove'; then
    NEW_TAG="v$((MAJOR + 1)).0.0"
    BUMP="major"
  elif echo "$PR_TITLE" | grep -qi '^feat'; then
    NEW_TAG="v${MAJOR}.$((MINOR + 1)).0"
    BUMP="minor"
  else
    NEW_TAG="v${MAJOR}.${MINOR}.$((PATCH + 1))"
    BUMP="patch"
  fi

  echo "Suggested version: $NEW_TAG ($BUMP bump from $LATEST_TAG)"
fi
```

### 9.3 Create and Push the Tag

Only proceed if the user confirms the release tag is appropriate.

```bash
# Create an annotated tag
git tag -a "$NEW_TAG" -m "Release $NEW_TAG

Changes in this release:
$(git log "$LATEST_TAG..HEAD" --oneline --no-decorate)
"

# Push the tag
git push origin "$NEW_TAG"
echo "Tag $NEW_TAG created and pushed."
```

### 9.4 Generate Release Notes

```bash
# Create a GitHub release with auto-generated notes
gh release create "$NEW_TAG" \
  --title "$NEW_TAG" \
  --generate-notes \
  --latest

echo "GitHub release created: $NEW_TAG"
```

---

## STEP 10: Deployment Awareness

If the project has continuous deployment configured, monitor the deployment after merge.

### 10.1 Detect CD Configuration

```bash
# Check for common CD configuration files
CD_DETECTED=false

if [ -f .github/workflows/deploy.yml ] || [ -f .github/workflows/cd.yml ]; then
  echo "GitHub Actions CD workflow detected."
  CD_DETECTED=true
fi

if [ -f vercel.json ] || [ -f netlify.toml ]; then
  echo "Platform-managed CD detected (Vercel/Netlify)."
  CD_DETECTED=true
fi

if [ -f Dockerfile ] && [ -f docker-compose.yml ]; then
  echo "Docker-based deployment detected."
  CD_DETECTED=true
fi

if [ -f fly.toml ] || [ -f render.yaml ] || [ -f railway.json ]; then
  echo "PaaS deployment detected."
  CD_DETECTED=true
fi

if [ "$CD_DETECTED" = false ]; then
  echo "No CD configuration detected — skipping deployment monitoring."
fi
```

### 10.2 Monitor Deployment Status

```bash
if [ "$CD_DETECTED" = true ]; then
  # Check if a deployment workflow was triggered
  echo "Checking for deployment workflow runs..."

  # Wait a moment for the workflow to trigger
  sleep 5

  # List recent workflow runs on the base branch
  gh run list --branch "$BASE_BRANCH" --limit 3 --json name,status,conclusion,databaseId \
    --jq '.[] | "\(.name): \(.status) (\(.conclusion // "in progress"))"'
fi
```

### 10.3 Watch for Deployment Failures

```bash
if [ "$CD_DETECTED" = true ]; then
  # Get the most recent deployment run
  DEPLOY_RUN_ID=$(gh run list --branch "$BASE_BRANCH" --limit 1 --json databaseId --jq '.[0].databaseId')

  if [ -n "$DEPLOY_RUN_ID" ]; then
    echo "Latest deployment run: $DEPLOY_RUN_ID"
    echo "Monitor with: gh run watch $DEPLOY_RUN_ID"
    echo ""
    echo "If deployment fails:"
    echo "  1. Check logs: gh run view $DEPLOY_RUN_ID --log-failed"
    echo "  2. Revert if needed: git revert -m 1 $MERGE_SHA && git push origin $BASE_BRANCH"
  fi
fi
```

### 10.4 Manual Deployment Commands

```bash
if [ "$CD_DETECTED" = false ]; then
  echo "If manual deployment is needed, common commands:"
  echo ""
  echo "  # Heroku"
  echo "  git push heroku $BASE_BRANCH:main"
  echo ""
  echo "  # AWS (via CLI)"
  echo "  aws deploy create-deployment --application-name <app> --deployment-group <group>"
  echo ""
  echo "  # Docker"
  echo "  docker build -t <image> . && docker push <image>"
  echo ""
  echo "  # SSH"
  echo "  ssh <server> 'cd /app && git pull && <restart-command>'"
fi
```

---

## STEP 11: Final Summary

Output a comprehensive summary of everything that was done.

### 11.1 Summary Template

```
=== Branch Finished ===

PR:            #<PR_NUMBER> — <PR_TITLE>
Branch:        <BRANCH> -> <BASE_BRANCH>
Merge commit:  <MERGE_SHA>
Method:        squash / merge / rebase

Pre-merge:
  - Review:    APPROVED
  - CI:        all checks passed
  - Conflicts: none

Commit cleanup:
  - <N> commits squashed into <M>
  - Fixup commits removed: <count>

Changelog:
  - Entry added under [<CATEGORY>] in CHANGELOG.md
  - Or: No CHANGELOG.md found — skipped

Worktree:
  - Cleaned up worktree at <path>
  - Or: No worktree — skipped

Post-merge verification:
  - Tests:  <X> passed, 0 failed
  - Build:  success

Branch cleanup:
  - Local branch deleted
  - Remote branch deleted
  - Stale references pruned

Cross-PR dependencies:
  - Closed issues: #<issue1>, #<issue2>
  - Unblocked PRs: #<pr1>, #<pr2>
  - Or: No dependencies found

Release:
  - Tagged: <NEW_TAG>
  - Or: No release tag needed

Deployment:
  - Auto-deploy triggered — monitor with: gh run watch <ID>
  - Or: No CD configured — manual deployment may be needed

Rollback (if needed):
  git revert -m 1 <MERGE_SHA> && git push origin <BASE_BRANCH>

=== Done ===
```

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
