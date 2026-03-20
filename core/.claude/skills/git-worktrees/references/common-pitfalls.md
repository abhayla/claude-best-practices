# STEP 9: Common Pitfalls

### 9.1 Shared `index.lock`

Each worktree has its own index, but certain git operations (e.g., `git gc`, `git prune`)
acquire a repository-level lock. If two worktrees run these simultaneously:

```
fatal: Unable to create '/path/to/repo/.git/index.lock': File exists.
```

**Fix:** Avoid running `git gc`, `git prune`, or `git repack` while agents are active in
worktrees. Schedule maintenance for idle periods.

### 9.2 Submodules

Git worktrees and submodules have known interaction issues:

- Submodule state is shared across worktrees — checking out a different submodule commit
  in one worktree affects all others
- `.gitmodules` changes in one worktree can confuse other worktrees

**Fix:** If the repo uses submodules, use separate clones instead of worktrees for isolation.

### 9.3 Hooks

Git hooks in `.git/hooks/` are shared across all worktrees. A hook that references
`$GIT_DIR` may behave unexpectedly:

- In the main worktree, `$GIT_DIR` is `.git/`
- In linked worktrees, `$GIT_DIR` is `.git/worktrees/<name>/`

**Fix:** Use `$GIT_COMMON_DIR` when hooks need to access shared repository data, and
`$GIT_DIR` for worktree-specific data.

### 9.4 Branch Already Checked Out

A branch checked out in one worktree cannot be checked out in another:

```
fatal: 'feature/auth' is already checked out at '/path/to/worktree'
```

**Fix:** This is intentional — it prevents conflicting edits. Create a new branch for
the second worktree, or remove the first worktree if it is no longer needed.

### 9.5 Stale Worktree References

If a worktree directory is deleted with `rm -rf` instead of `git worktree remove`:

```bash
