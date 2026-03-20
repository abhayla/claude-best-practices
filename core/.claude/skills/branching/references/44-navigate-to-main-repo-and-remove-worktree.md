# 4.4 Navigate to Main Repo and Remove Worktree

### 4.4 Navigate to Main Repo and Remove Worktree

```bash
if [ "$IS_WORKTREE" = true ]; then
  # Switch to the main repository before removing the worktree
  cd "$MAIN_REPO"

  # Remove the worktree
  git worktree remove "$WORKTREE_PATH"
  echo "Worktree removed: $WORKTREE_PATH"

  # Prune stale worktree references
  git worktree prune
  echo "Stale worktree references pruned."

  # Verify the worktree directory is gone
  if [ -d "$WORKTREE_PATH" ]; then
    echo "WARNING: Worktree directory still exists at $WORKTREE_PATH"
    echo "Manual cleanup may be needed."
  else
    echo "Worktree directory confirmed removed."
  fi
fi
```

