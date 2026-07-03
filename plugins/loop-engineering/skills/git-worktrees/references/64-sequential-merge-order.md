# 6.4 Sequential Merge Order

### 6.4 Sequential Merge Order

When merging multiple worktree branches, order matters:

1. **Merge the branch with the most foundational changes first** — e.g., data models before
   API endpoints
2. **Run tests after each merge** — catch integration issues incrementally
3. **Resolve conflicts immediately** — do not batch conflict resolution

```bash
