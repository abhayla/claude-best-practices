# 3.3 Branch Strategies

### 3.3 Branch Strategies

| Pattern | Branch Naming | When to Use |
|---------|--------------|-------------|
| **Feature worktree** | `feature/<name>` based off `main` | New feature development |
| **Hotfix worktree** | `hotfix/<name>` based off `main` or latest tag | Production fixes |
| **Research worktree** | `research/<name>` based off `main` | Throwaway exploration |
| **Agent worktree** | `agent/<task-id>-<description>` based off current branch | Parallel subagent dispatch |
| **Review worktree** | No new branch — check out existing PR branch | Code review |

```bash
