# 6.1 Choosing a Merge Strategy

### 6.1 Choosing a Merge Strategy

After work in a worktree is complete, merge the worktree's branch back into the target
branch. Choose based on the situation:

| Strategy | When to Use | Command |
|----------|-------------|---------|
| **Merge commit** | Feature branches with multiple commits — preserves history | `git merge feature/auth` |
| **Squash merge** | Agent worktrees with messy intermediate commits | `git merge --squash agent/task42-validation` |
| **Rebase** | Clean linear history preferred, few commits | `git rebase main` (from feature branch) |
| **Cherry-pick** | Only some commits from the worktree are wanted | `git cherry-pick abc1234 def5678` |

