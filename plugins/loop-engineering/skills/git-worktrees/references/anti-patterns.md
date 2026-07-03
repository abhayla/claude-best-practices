# Anti-Patterns

## 11.1 Too Many Worktrees

**Problem:** Creating 10+ worktrees causes disk bloat, cognitive overhead, and increases
the chance of stale worktrees accumulating.

**Limit:** Keep a maximum of 5 active worktrees at any time. If you need more parallelism,
merge completed worktrees before creating new ones.

```bash
# Check how many worktrees exist
git worktree list | wc -l

# If more than 5, merge and clean up before creating more
```

## 11.3 Conflicting Edits Across Worktrees

**Problem:** Two worktrees based off the same branch, both modifying `src/config.ts`.
When merging, one will conflict with the other.

**Fix:** Apply the ownership rule from `/subagent-driven-dev` — each file is owned by
exactly one worktree at a time. If two tasks need to modify the same file, they MUST
be sequential, not parallel.

## 11.4 Working in the `.git/worktrees/` Directory

**Problem:** Manually editing files in `.git/worktrees/` corrupts worktree metadata.

**Fix:** Never touch `.git/worktrees/` directly. Use `git worktree` commands for all
management operations.

## 11.5 Creating Worktrees Inside the Repo

**Problem:** Creating a worktree as a subdirectory of the main repo (e.g., `./worktrees/feature`)
causes gitignore confusion and can accidentally include worktree files in commits.

**Fix:** Always create worktrees in a sibling directory:

```bash
# WRONG — inside the repo
git worktree add ./worktrees/feature -b feature/x

# RIGHT — sibling directory
git worktree add ../project-wt/feature -b feature/x
```
