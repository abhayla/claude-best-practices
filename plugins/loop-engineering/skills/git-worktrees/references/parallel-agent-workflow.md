# Parallel Agent Workflow (End-to-End)

This ties together worktrees with the subagent-driven-dev skill for a complete
parallel workflow.

## 7.1 Pre-Work

```bash
# Ensure the base branch is clean and pre-work is committed
git status  # Should be clean
git log --oneline -1  # Should show pre-work commit
```

## 7.2 Dispatch Phase

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

## 7.3 Monitoring Phase

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

## 7.4 Merge Phase

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

## 7.5 Cleanup Phase

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
