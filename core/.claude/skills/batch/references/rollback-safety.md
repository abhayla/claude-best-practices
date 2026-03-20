# Rollback Safety

Every batch change must be reversible. A failed migration that cannot be rolled back
is worse than no migration at all.

## Pre-Change Tag

Before starting any batch work, create a tag:

```bash
# Tag the current state for easy rollback
git tag batch/pre-rename-userservice

# Verify the tag
git log --oneline -1 batch/pre-rename-userservice
```

## Per-Batch Commits

Each batch gets its own commit. This enables surgical rollback of individual batches:

```bash
# Pre-work commit
git commit -m "refactor(batch 0/4): rename UserService file and class"

# Batch A commit (after merging agent worktree)
git commit -m "refactor(batch 1/4): update controllers for AccountService"

# Batch B commit
git commit -m "refactor(batch 2/4): update middleware for AccountService"

# Batch C commit
git commit -m "refactor(batch 3/4): update tests for AccountService"

# Batch D commit
git commit -m "refactor(batch 4/4): update docs for AccountService"

# Post-work commit
git commit -m "refactor(batch post): update config and CI for AccountService"
```

## Partial Rollback

If Batch B introduced a bug but other batches are fine:

```bash
# Find the batch commit
git log --oneline --grep="batch 2/4"

# Revert only that batch
git revert <batch-2-commit-hash> --no-edit

# Re-run tests to verify the partial rollback is safe
npm test
```

## Full Rollback

If the entire batch change needs to be undone:

```bash
# Option A: Revert to the pre-change tag
git revert batch/pre-rename-userservice..HEAD --no-edit

# Option B: Reset to the tag (destructive — only if not yet pushed)
git reset --hard batch/pre-rename-userservice

# Option C: Revert each batch commit individually (preserves history)
git log --oneline batch/pre-rename-userservice..HEAD
# Then revert each commit in reverse order
```

## Rollback Verification

After any rollback:

```bash
# Verify no references to the new name remain (should be zero)
grep -rn "AccountService" src/ tests/ --include="*.ts" | wc -l

# Verify all references to the old name are back
grep -rn "UserService" src/ tests/ --include="*.ts" | wc -l

# Run full test suite
npm test
```
