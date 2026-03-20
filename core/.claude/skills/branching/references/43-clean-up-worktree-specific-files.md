# 4.3 Clean Up Worktree-Specific Files

### 4.3 Clean Up Worktree-Specific Files

```bash
if [ "$IS_WORKTREE" = true ]; then
  # Remove worktree-specific env files that should not persist
  WORKTREE_ENV_FILES=(.env.local .env.development.local node_modules/.cache)
  for f in "${WORKTREE_ENV_FILES[@]}"; do
    if [ -e "$WORKTREE_PATH/$f" ]; then
      echo "Removing worktree-specific file: $f"
      rm -rf "$WORKTREE_PATH/$f"
    fi
  done
fi
```

