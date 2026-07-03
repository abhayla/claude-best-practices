# Worktree Patterns

## 10.1 Feature Branch per Worktree

The most common pattern — one worktree per feature branch for parallel development:

```bash
# Developer works on three features simultaneously
git worktree add ../project-wt/feature-auth     -b feature/auth     main
git worktree add ../project-wt/feature-billing   -b feature/billing   main
git worktree add ../project-wt/feature-dashboard -b feature/dashboard main

# Each worktree is a full development environment
# Switch between them by changing directories, not branches
cd ../project-wt/feature-auth       # Work on auth
cd ../project-wt/feature-billing    # Switch to billing (no stash/commit needed)
cd ../project-wt/feature-dashboard  # Switch to dashboard
```

## 10.2 Research Worktree (Read-Only Exploration)

Create a disposable worktree for exploring code without risking changes to the main
working directory:

```bash
# Create a research worktree at a specific commit or branch
git worktree add ../project-wt/research-caching -b research/caching main

# Explore freely — make experimental changes, add debug logging, etc.
cd ../project-wt/research-caching
# ... explore, prototype, experiment ...

# When done, extract findings and discard the worktree
git worktree remove --force ../project-wt/research-caching
git branch -D research/caching
```

This pattern is useful for subagents doing research — they can modify files freely in
the research worktree without affecting the main development environment.

## 10.3 Hotfix Worktree

When a critical bug needs fixing while feature development is in progress:

```bash
# Current state: deep into feature work on feature/auth branch
# Urgent: production crash needs a hotfix

# Create a hotfix worktree from the latest release
git worktree add ../project-wt/hotfix-crash -b hotfix/crash-fix v2.3.1

# Fix the bug in the hotfix worktree
cd ../project-wt/hotfix-crash
# ... make the fix ...
git add -A && git commit -m "fix: prevent null pointer crash on login"

# Push and create PR from the hotfix worktree
git push -u origin hotfix/crash-fix

# Return to feature work — no branch switching, no stash needed
cd /path/to/main/repo  # Still on feature/auth with all work intact

# Clean up after hotfix is merged
git worktree remove ../project-wt/hotfix-crash
git branch -d hotfix/crash-fix
```

## 10.4 Review Worktree

Check out a PR for review without leaving your current branch:

```bash
# Fetch the PR branch
git fetch origin pull/123/head:pr-123

# Create a worktree for review
git worktree add ../project-wt/review-pr-123 pr-123

# Review in the worktree
cd ../project-wt/review-pr-123
npm test  # Run tests
# ... review code ...

# Clean up
git worktree remove ../project-wt/review-pr-123
git branch -d pr-123
```

## 10.5 CI/Test Isolation Worktree

Run tests on a stable branch while continuing to develop:

```bash
# Create a worktree pointing to main for test runs
git worktree add ../project-wt/test-runner main

# In one terminal: run the full test suite against main
cd ../project-wt/test-runner && npm test

# In another terminal: continue developing on the feature branch
cd /path/to/main/repo && code src/new-feature.ts
```
