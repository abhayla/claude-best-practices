# 4.2 Ensure Work is Committed

### 4.2 Ensure Work is Committed

```bash
if [ "$IS_WORKTREE" = true ]; then
  # Check for uncommitted changes
  if [ -n "$(git status --porcelain)" ]; then
    echo "ERROR: Worktree has uncommitted changes. Commit or stash before cleanup."
    git status --short
    exit 1
  fi
fi
```

