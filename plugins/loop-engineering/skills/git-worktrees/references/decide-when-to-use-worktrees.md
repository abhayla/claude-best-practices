# STEP 2: Decide When to Use Worktrees

### 2.1 Use Worktrees When

| Signal | Example |
|--------|---------|
| **Parallel agent tasks that touch overlapping files** | Two subagents both need to modify `src/config.ts` on different branches |
| **Long-running feature + urgent hotfix** | Working on a multi-day feature but need to ship a hotfix from `main` |
| **Comparative research** | Exploring two different approaches to the same problem side-by-side |
| **Review while developing** | Checking out a PR branch for review without disrupting current work |
| **Build/test isolation** | Running tests on `main` while developing on a feature branch |
| **Multiple subagents with `isolation: "worktree"`** | Claude Code automatically creates worktrees for each agent |

### 2.2 Do NOT Use Worktrees When

| Signal | Use Instead |
|--------|-------------|
| **Subagents touch completely different files** | Regular parallel agents in the same working directory — no isolation needed |
| **Single-file quick fix** | `git stash` → fix → `git stash pop` — faster than worktree setup |
| **Exploratory read-only research** | Subagent with read-only scope — no writes means no conflicts |
| **Sequential tasks** | Regular branch workflow — worktrees add unnecessary complexity |
| **Submodules in the repo** | Worktrees and submodules interact poorly — use separate clones instead |

### 2.3 Decision Checklist

Before creating worktrees, answer these questions:

1. **Do I need multiple branches checked out simultaneously?** If you can work sequentially, use regular branches.
2. **Will parallel agents modify files in the same directory?** If yes, worktrees provide the isolation needed.
3. **Does the task benefit from build-cache preservation?** If switching branches invalidates expensive build caches, worktrees help.
4. **Is the repo free of submodules?** If the repo uses submodules, worktrees may cause issues — test carefully or use clones.
5. **Am I willing to clean up worktrees after?** Worktrees left behind consume disk space and can cause confusion.

If the answer to question 1 is "no," skip worktrees — the overhead is not justified.

---

