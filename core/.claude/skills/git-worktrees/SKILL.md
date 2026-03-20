---
name: git-worktrees
description: >
  Manage git worktrees for isolated parallel development. Provides a decision framework
  for when to use worktrees vs. regular branches, creation patterns, Claude Code's built-in
  isolation parameter, parallel agent workflows, merge strategies, cleanup procedures, and
  common pitfalls. Complements subagent-driven-dev by providing the file-system isolation
  mechanism that prevents conflicts across parallel workstreams.
triggers:
  - /worktree
  - /git-worktree
  - worktree
  - git worktree
  - parallel worktrees
  - isolated development
  - worktree isolation
allowed-tools: "Bash Read Write Edit Grep Glob Agent"
argument-hint: "<task requiring isolated parallel development or worktree management>"
version: "1.0.0"
type: workflow
---

# Git Worktrees — Isolated Parallel Development

Use git worktrees to run multiple development streams in parallel without branch-switching
overhead or file conflict risk.

**Task:** $ARGUMENTS

---

## STEP 1: Understand Git Worktrees


**Read:** `references/understand-git-worktrees.md` for detailed step 1: understand git worktrees reference material.

## STEP 2: Decide When to Use Worktrees


**Read:** `references/decide-when-to-use-worktrees.md` for detailed step 2: decide when to use worktrees reference material.

## STEP 3: Create Worktrees

### 3.1 Basic Creation

```bash
# Create a worktree with a new branch
git worktree add ../project-worktrees/feature-auth -b feature/auth

# Create a worktree from an existing branch
git worktree add ../project-worktrees/feature-auth feature/auth

# Create a worktree from a specific commit (detached HEAD)
git worktree add ../project-worktrees/investigate-bug abc1234
```

### 3.2 Naming Conventions

Use a consistent naming scheme for worktree directories:

```
# Pattern: <repo-name>-worktrees/<purpose>-<identifier>
../myproject-worktrees/feature-user-auth
../myproject-worktrees/hotfix-crash-login
../myproject-worktrees/research-caching-strategy
../myproject-worktrees/agent-1-validation
../myproject-worktrees/agent-2-api-endpoints
```

Rules:
- Place all worktrees in a sibling directory named `<repo>-worktrees/` — keeps the parent directory clean
- Use lowercase with hyphens — matches git branch naming conventions
- Prefix with purpose: `feature-`, `hotfix-`, `research-`, `agent-N-`
- MUST NOT create worktrees inside the main repository directory — this causes path confusion and gitignore issues

# Feature worktree: branch from main
git worktree add ../project-wt/feature-auth -b feature/auth main

# Hotfix worktree: branch from the latest release tag
git worktree add ../project-wt/hotfix-crash -b hotfix/crash-fix v2.3.1

# Research worktree: branch from current HEAD
git worktree add ../project-wt/research-caching -b research/caching-strategy

# Agent worktree: branch from current working branch
git worktree add ../project-wt/agent-1-validation -b agent/task42-validation HEAD
```

### 3.4 Post-Creation Setup

After creating a worktree, it may need environment setup:

```bash
# Navigate to the worktree
cd ../project-wt/feature-auth

# Install dependencies (worktrees share source but not node_modules, venvs, etc.)
npm install          # Node.js
pip install -r requirements.txt  # Python
./gradlew build      # Gradle

# Verify the worktree is functional
git status
git log --oneline -3
```

Each worktree has its own working directory, so dependencies installed locally
(e.g., `node_modules/`, `.venv/`) are per-worktree. This is intentional — it prevents
version conflicts between branches with different dependency trees.

---

## STEP 4: Claude Code's Built-in Worktree Isolation

### 4.1 The `isolation: "worktree"` Parameter

Claude Code's `Agent()` tool supports an `isolation` parameter that automatically creates
a git worktree for the subagent, runs the agent inside it, and manages lifecycle:

```
Agent("
## Objective
Implement user authentication middleware

## Files to Modify
- src/middleware/auth.ts
- tests/middleware/auth.test.ts

### 4.3 Dispatching Multiple Isolated Agents

```
# Dispatch three agents, each in their own worktree
Agent("
## Objective: Implement user validation
## Files: src/validators/user.ts, tests/validators/user.test.ts
## Verification: npm test -- --grep 'user validator'
", isolation="worktree")

Agent("
## Objective: Implement order validation
## Files: src/validators/order.ts, tests/validators/order.test.ts
## Verification: npm test -- --grep 'order validator'
", isolation="worktree")

Agent("
## Objective: Implement product validation
## Files: src/validators/product.ts, tests/validators/product.test.ts
## Verification: npm test -- --grep 'product validator'
", isolation="worktree")
```

Each agent gets its own worktree. Even if all three agents need to read `src/config.ts`,
there is no conflict because each has a separate copy on disk.

### 4.4 Retrieving Results from Isolated Agents

After isolated agents complete, their changes exist on separate branches. The orchestrator
must merge them:

```bash
# List branches created by isolated agents
git branch --list 'agent/*'

# Review changes from each agent
git log main..agent/task42-user-validation --oneline
git diff main...agent/task42-user-validation

# Merge or rebase (see Step 6 for strategies)
```

---

## STEP 5: Manual Worktree Management

### 5.1 Listing Worktrees

```bash
# List all worktrees
git worktree list

# Example output:
# /home/user/project                   abc1234 [main]
# /home/user/project-wt/feature-auth   def5678 [feature/auth]
# /home/user/project-wt/hotfix-crash   ghi9012 [hotfix/crash-fix]
```

### 5.2 Inspecting a Worktree

```bash
# Check which branch a worktree is on
cd ../project-wt/feature-auth && git branch --show-current

# Check the status of work in a worktree
cd ../project-wt/feature-auth && git status

# View recent commits in a worktree
cd ../project-wt/feature-auth && git log --oneline -5
```

### 5.3 Moving a Worktree

```bash
# Move a worktree to a different directory
git worktree move ../project-wt/feature-auth ../project-wt/feature-authentication
```

### 5.4 Removing a Worktree

```bash
# Remove a worktree (directory must be clean — no uncommitted changes)
git worktree remove ../project-wt/feature-auth

# Force-remove a worktree with uncommitted changes (destructive)
git worktree remove --force ../project-wt/feature-auth
```

### 5.5 Pruning Stale Worktrees

When a worktree directory is deleted manually (e.g., `rm -rf`), git still tracks it.
Prune cleans up these stale references:

```bash
# Show stale worktree references
git worktree list

# Prune stale references
git worktree prune

# Prune with verbose output
git worktree prune --verbose
```

---

## STEP 6: Merge Strategies

### 6.2 Merging Agent Worktree Branches

For parallel agent workflows, squash merge is usually best — each agent's work becomes
a single clean commit on the target branch:

```bash
# From the main worktree, on the target branch
git merge --squash agent/task42-user-validation
git commit -m "feat: add user input validation

Implemented by isolated agent: validators, error messages, and tests."

git merge --squash agent/task42-order-validation
git commit -m "feat: add order input validation

Implemented by isolated agent: validators, business rules, and tests."
```

### 6.3 Handling Merge Conflicts

When merging multiple worktree branches that modified related (but not identical) code:

```bash
# Attempt the merge
git merge agent/task42-order-validation

# If conflicts arise:
# 1. Identify conflicting files
git diff --name-only --diff-filter=U

# 2. Review each conflict
git diff <conflicting-file>

# 3. Resolve conflicts manually
# Edit the files to resolve <<<<<<< / >>>>>>> markers

# 4. Mark as resolved and commit
git add <resolved-files>
git commit -m "feat: add order validation (resolved merge conflict with user validation)"
```

# Merge in dependency order
git merge --squash agent/models       && npm test
git merge --squash agent/api-endpoints && npm test
git merge --squash agent/tests         && npm test
```

---

## STEP 7: Parallel Agent Workflow (End-to-End)

This step ties together worktrees with the subagent-driven-dev skill for a complete
parallel workflow.

# Ensure the base branch is clean and pre-work is committed
git status  # Should be clean
git log --oneline -1  # Should show pre-work commit
```

### 7.2 Dispatch Phase

Create worktrees and dispatch agents:

```bash
# Option A: Manual worktree creation + regular agents
git worktree add ../project-wt/agent-1-auth -b agent/auth HEAD
git worktree add ../project-wt/agent-2-billing -b agent/billing HEAD

# Then dispatch agents pointing to their worktree directories
Agent("
## Objective: Implement auth middleware
## Working Directory: ../project-wt/agent-1-auth
## Files to Modify: src/middleware/auth.ts, tests/auth.test.ts
## Verification: cd ../project-wt/agent-1-auth && npm test
")

Agent("
## Objective: Implement billing service
## Working Directory: ../project-wt/agent-2-billing
## Files to Modify: src/services/billing.ts, tests/billing.test.ts
## Verification: cd ../project-wt/agent-2-billing && npm test
")
```

```
# Option B: Use Claude Code's built-in isolation (preferred — simpler)
Agent("Implement auth middleware ...", isolation="worktree")
Agent("Implement billing service ...", isolation="worktree")
```

### 7.3 Monitoring Phase

Track progress across worktrees:

```bash
# Check status of all worktrees
git worktree list

# Check each worktree's branch for new commits
git log main..agent/auth --oneline
git log main..agent/billing --oneline

# Check for uncommitted changes in worktrees
cd ../project-wt/agent-1-auth && git status
cd ../project-wt/agent-2-billing && git status
```

### 7.4 Merge Phase

After all agents complete successfully:

```bash
# Return to main worktree
cd /path/to/main/repo

# Merge each agent's work
git merge --squash agent/auth
git commit -m "feat: add auth middleware"

git merge --squash agent/billing
git commit -m "feat: add billing service"

# Run full test suite
npm test
```

### 7.5 Cleanup Phase

```bash
# Remove worktrees
git worktree remove ../project-wt/agent-1-auth
git worktree remove ../project-wt/agent-2-billing

# Delete the agent branches (they have been merged)
git branch -d agent/auth
git branch -d agent/billing

# Prune any stale worktree references
git worktree prune
```

---

## STEP 8: Cleanup and Hygiene

### 8.1 When to Clean Up

Clean up worktrees immediately after their branch has been merged. Do not leave worktrees
around "just in case" — they consume disk space and cause confusion.

```bash
# After successful merge:
git worktree remove ../project-wt/feature-auth
git branch -d feature/auth  # Delete the branch if fully merged
```

### 8.2 Cleaning Up All Worktrees

After a parallel workflow completes:

```bash
# List all worktrees
git worktree list

# Remove each non-main worktree
git worktree list --porcelain | grep '^worktree ' | grep -v "$(git rev-parse --show-toplevel)" | \
  sed 's/^worktree //' | while read wt; do
    git worktree remove "$wt"
  done

# Prune stale references
git worktree prune

# Delete merged agent branches
git branch --list 'agent/*' | xargs git branch -d
```

### 8.3 Handling Unmerged Worktrees

If a worktree has work that was never merged:

```bash
# Check for unmerged commits
git log main..agent/abandoned-task --oneline

# If the work is valuable, merge it first
git merge --squash agent/abandoned-task
git commit -m "feat: salvage work from abandoned agent task"

# If the work should be discarded
git worktree remove --force ../project-wt/abandoned-task
git branch -D agent/abandoned-task  # Force-delete unmerged branch
```

### 8.4 Periodic Maintenance

Run these commands periodically to keep the worktree state clean:

```bash
# Prune stale worktree references
git worktree prune

# List remaining worktrees (should only show the main worktree during idle periods)
git worktree list

# Check for leftover agent branches
git branch --list 'agent/*'
git branch --list 'research/*'
```

---

## STEP 9: Common Pitfalls


**Read:** `references/common-pitfalls.md` for detailed step 9: common pitfalls reference material.

# Git still thinks the worktree exists
git worktree list  # Shows the deleted worktree

# Clean up the stale reference
git worktree prune
```

**Fix:** Always use `git worktree remove` instead of `rm -rf`. If already deleted,
run `git worktree prune`.

### 9.6 Large Repos and Disk Space

Each worktree creates a full copy of the working directory (but shares the object store).
For repos with large generated files or build artifacts:

```bash
# Check worktree disk usage
du -sh ../project-wt/*/

# Add build artifacts to .gitignore if not already
# Each worktree will have its own copy of untracked files
```

**Fix:** Add build outputs and generated files to `.gitignore`. Consider using
`--no-checkout` for worktrees that only need specific files:

```bash
git worktree add --no-checkout ../project-wt/minimal-worktree -b temp-branch
cd ../project-wt/minimal-worktree
git checkout HEAD -- src/specific-module/  # Checkout only what is needed
```

---

## STEP 10: Patterns

### 10.1 Feature Branch per Worktree

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

### 10.2 Research Worktree (Read-Only Exploration)

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

### 10.3 Hotfix Worktree

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

### 10.4 Review Worktree

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

### 10.5 CI/Test Isolation Worktree

Run tests on a stable branch while continuing to develop:

```bash
# Create a worktree pointing to main for test runs
git worktree add ../project-wt/test-runner main

# In one terminal: run the full test suite against main
cd ../project-wt/test-runner && npm test

# In another terminal: continue developing on the feature branch
cd /path/to/main/repo && code src/new-feature.ts
```

---

## STEP 11: Anti-Patterns

### 11.1 Too Many Worktrees

**Problem:** Creating 10+ worktrees causes disk bloat, cognitive overhead, and increases
the chance of stale worktrees accumulating.

**Limit:** Keep a maximum of 5 active worktrees at any time. If you need more parallelism,
merge completed worktrees before creating new ones.

```bash
# Check how many worktrees exist
git worktree list | wc -l

# If more than 5, merge and clean up before creating more
```

### 11.3 Conflicting Edits Across Worktrees

**Problem:** Two worktrees based off the same branch, both modifying `src/config.ts`.
When merging, one will conflict with the other.

**Fix:** Apply the ownership rule from `/subagent-driven-dev` — each file is owned by
exactly one worktree at a time. If two tasks need to modify the same file, they MUST
be sequential, not parallel.

### 11.4 Working in the `.git/worktrees/` Directory

**Problem:** Manually editing files in `.git/worktrees/` corrupts worktree metadata.

**Fix:** Never touch `.git/worktrees/` directly. Use `git worktree` commands for all
management operations.

### 11.5 Creating Worktrees Inside the Repo

**Problem:** Creating a worktree as a subdirectory of the main repo (e.g., `./worktrees/feature`)
causes gitignore confusion and can accidentally include worktree files in commits.

**Fix:** Always create worktrees in a sibling directory:

```bash
# WRONG — inside the repo
git worktree add ./worktrees/feature -b feature/x

# RIGHT — sibling directory
git worktree add ../project-wt/feature -b feature/x
```

## MUST DO

- Always use `git worktree remove` instead of `rm -rf` for cleanup — manual deletion leaves stale references
- Always commit or stash changes in a worktree before removing it — `remove` fails on dirty worktrees by design
- Always clean up worktrees immediately after their branch is merged — do not leave them around
- Always run `git worktree prune` after manual directory deletions to clean up stale references
- Always place worktrees in a sibling directory (`../project-wt/`) — never inside the main repo
- Always use the `isolation: "worktree"` parameter when dispatching 3+ parallel agents that may touch related files
- Always merge worktree branches in dependency order and run tests after each merge
- Always delete merged agent branches after cleanup to keep the branch list clean

## MUST NOT DO

- MUST NOT create worktrees inside the repository directory — use a sibling directory to avoid gitignore issues
- MUST NOT have more than 5 active worktrees at once — merge and clean up before creating more
- MUST NOT use worktrees in repos with submodules unless you have verified compatibility — use separate clones instead
- MUST NOT run `git gc` or `git prune` while agents are active in worktrees — these operations acquire repo-level locks
- MUST NOT manually edit files in `.git/worktrees/` — use `git worktree` commands for all management
- MUST NOT leave worktrees around after their branches are merged — they waste disk space and cause confusion
- MUST NOT check out the same branch in multiple worktrees — git prevents this for good reason; create separate branches
- MUST NOT skip the merge verification step — run the full test suite after merging each worktree branch
