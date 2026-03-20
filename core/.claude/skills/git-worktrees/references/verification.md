# Verification

## Verification
Run: npm test -- --grep 'auth middleware'
", isolation="worktree")
```

When `isolation: "worktree"` is set:

1. Claude Code creates a new branch and worktree automatically
2. The subagent operates entirely within that worktree directory
3. File edits are isolated — no risk of conflicting with the main worktree or other agents
4. On completion, the changes remain on the worktree's branch for the orchestrator to merge

