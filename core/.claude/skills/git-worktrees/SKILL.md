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

**Read:** `references/understand-git-worktrees.md` for detailed explanation of what worktrees are and how they work.

## STEP 2: Decide When to Use Worktrees

**Read:** `references/decide-when-to-use-worktrees.md` for the decision framework on worktrees vs. regular branches.

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
../myproject-worktrees/agent-1-validation
```

Rules:
- Place all worktrees in a sibling directory named `<repo>-worktrees/` — keeps the parent directory clean
- Use lowercase with hyphens — matches git branch naming conventions
- Prefix with purpose: `feature-`, `hotfix-`, `research-`, `agent-N-`
- MUST NOT create worktrees inside the main repository directory

### 3.3 Branch Strategies

**Read:** `references/33-branch-strategies.md` for branch creation from different starting points.

### 3.4 Post-Creation Setup

After creating a worktree, it may need environment setup:

```bash
cd ../project-wt/feature-auth

# Install dependencies (worktrees share source but not node_modules, venvs, etc.)
npm install          # Node.js
pip install -r requirements.txt  # Python
./gradlew build      # Gradle

git status
git log --oneline -3
```

Each worktree has its own working directory, so dependencies installed locally
(e.g., `node_modules/`, `.venv/`) are per-worktree.

---

## STEP 4: Claude Code's Built-in Worktree Isolation

Claude Code's `Agent()` tool supports `isolation: "worktree"` to automatically create
a git worktree for subagents, run them inside it, and manage lifecycle.

**Read:** `references/claude-code-isolation.md` for the isolation parameter, dispatching multiple agents, and retrieving results.

**Read:** `references/42-when-to-use-isolation-worktree.md` for decision criteria.

---

## STEP 5: Manual Worktree Management

Listing, inspecting, moving, removing, and pruning worktrees.

**Read:** `references/manual-worktree-management.md` for all management commands.

---

## STEP 6: Merge Strategies

### 6.1 Choosing a Strategy

**Read:** `references/61-choosing-a-merge-strategy.md` for merge strategy selection.

### 6.2 Merging Agent Worktree Branches

For parallel agent workflows, squash merge is usually best:

```bash
git merge --squash agent/task42-user-validation
git commit -m "feat: add user input validation"

git merge --squash agent/task42-order-validation
git commit -m "feat: add order input validation"
```

### 6.3 Handling Merge Conflicts

```bash
git merge agent/task42-order-validation

# If conflicts arise:
git diff --name-only --diff-filter=U   # Identify conflicting files
git diff <conflicting-file>             # Review each conflict
# Edit files to resolve <<<<<<< / >>>>>>> markers
git add <resolved-files>
git commit -m "feat: add order validation (resolved merge conflict)"
```

### 6.4 Sequential Merge Order

**Read:** `references/64-sequential-merge-order.md` for dependency-ordered merging.

---

## STEP 7: Parallel Agent Workflow (End-to-End)

Complete workflow: planning, dispatch, monitoring, merge, and cleanup.

**Read:** `references/parallel-agent-workflow.md` for the full end-to-end workflow.

**Read:** `references/71-planning-phase.md` for planning phase details.

---

## STEP 8: Cleanup and Hygiene

Clean up worktrees immediately after their branch has been merged.

**Read:** `references/cleanup-hygiene.md` for cleanup commands, handling unmerged worktrees, and periodic maintenance.

---

## STEP 9: Common Pitfalls

**Read:** `references/common-pitfalls.md` for common issues and fixes.

Key pitfalls: deleting worktree directories manually (`rm -rf`) instead of using `git worktree remove`, and large repos with disk space concerns.

---

## STEP 10: Patterns

Common worktree usage patterns for different scenarios.

**Read:** `references/worktree-patterns.md` for feature branch, research, hotfix, review, and CI/test isolation patterns.

---

## STEP 11: Anti-Patterns

**Read:** `references/anti-patterns.md` for too-many-worktrees, conflicting edits, and other anti-patterns.

---

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
