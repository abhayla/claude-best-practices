# 11.2 Forgetting Cleanup

### 11.2 Forgetting Cleanup

**Problem:** Worktrees left behind after their branches are merged waste disk space and
pollute `git worktree list` output, making it hard to find active worktrees.

**Fix:** Always pair worktree creation with a cleanup step. After every merge:

```bash
git worktree remove <path>
git branch -d <branch>
git worktree prune
```

