# STEP 1: Understand Git Worktrees

### 1.1 What Worktrees Are

A git worktree is an additional working directory linked to the same repository. Each worktree
checks out a different branch simultaneously, sharing the same `.git` object store. Unlike
`git checkout` (which swaps files in place), worktrees give each branch its own directory on
disk.

```
repo/                     ← main worktree (branch: main)
  .git/
  src/
  tests/

repo-worktrees/
  feature-auth/           ← linked worktree (branch: feature/auth)
    src/
    tests/
  hotfix-crash/           ← linked worktree (branch: hotfix/crash-on-login)
    src/
    tests/
```

All three directories share the same git history. Commits made in any worktree are visible
to all others. Branches checked out in one worktree cannot be checked out in another.

### 1.2 Why Worktrees Matter for Parallel Development

| Problem with Single Working Directory | How Worktrees Solve It |
|----------------------------------------|------------------------|
| Branch switching discards uncommitted work | Each branch has its own directory — no switching needed |
| Subagents editing the same directory collide on files | Each subagent operates in its own worktree directory |
| Build caches invalidate on branch switch | Each worktree maintains its own build artifacts |
| Context switching between tasks is expensive | Keep multiple tasks open simultaneously |
| `index.lock` conflicts when parallel git ops run | Each worktree has its own index file |

### 1.3 Worktrees vs. Clones

| Aspect | Worktree | Separate Clone |
|--------|----------|----------------|
| Disk space | Shared object store — lightweight | Full copy — heavy |
| Branch visibility | Instant — shared history | Requires fetch/push |
| Setup time | Seconds | Minutes (network + disk) |
| Independence | Shared refs can cause lock contention | Fully independent |
| Best for | Same-repo parallel work | Cross-repo or fully isolated CI |

Use worktrees for same-repo parallel development. Use separate clones only when you need
complete isolation (e.g., testing different dependency versions simultaneously).

---

