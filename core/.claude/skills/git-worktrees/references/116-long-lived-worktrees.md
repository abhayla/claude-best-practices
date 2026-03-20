# 11.6 Long-Lived Worktrees

### 11.6 Long-Lived Worktrees

**Problem:** A worktree created weeks ago drifts far from `main`, making eventual merge
painful.

**Fix:** Periodically rebase long-lived worktree branches onto `main`:

```bash
cd ../project-wt/long-lived-feature
git fetch origin main
git rebase origin/main
```

If a worktree has been idle for more than a week, evaluate whether the work should be
merged, discarded, or explicitly continued.

---

