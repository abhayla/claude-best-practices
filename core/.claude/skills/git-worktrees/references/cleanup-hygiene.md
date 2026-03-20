# Cleanup and Hygiene

## 8.1 When to Clean Up

Clean up worktrees immediately after their branch has been merged. Do not leave worktrees
around "just in case" — they consume disk space and cause confusion.

```bash
# After successful merge:
git worktree remove ../project-wt/feature-auth
git branch -d feature/auth  # Delete the branch if fully merged
```

## 8.2 Cleaning Up All Worktrees

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

## 8.3 Handling Unmerged Worktrees

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

## 8.4 Periodic Maintenance

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
