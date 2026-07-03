# Manual Worktree Management

## 5.1 Listing Worktrees

```bash
# List all worktrees
git worktree list

# Example output:
# /home/user/project                   abc1234 [main]
# /home/user/project-wt/feature-auth   def5678 [feature/auth]
# /home/user/project-wt/hotfix-crash   ghi9012 [hotfix/crash-fix]
```

## 5.2 Inspecting a Worktree

```bash
# Check which branch a worktree is on
cd ../project-wt/feature-auth && git branch --show-current

# Check the status of work in a worktree
cd ../project-wt/feature-auth && git status

# View recent commits in a worktree
cd ../project-wt/feature-auth && git log --oneline -5
```

## 5.3 Moving a Worktree

```bash
# Move a worktree to a different directory
git worktree move ../project-wt/feature-auth ../project-wt/feature-authentication
```

## 5.4 Removing a Worktree

```bash
# Remove a worktree (directory must be clean — no uncommitted changes)
git worktree remove ../project-wt/feature-auth

# Force-remove a worktree with uncommitted changes (destructive)
git worktree remove --force ../project-wt/feature-auth
```

## 5.5 Pruning Stale Worktrees

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
