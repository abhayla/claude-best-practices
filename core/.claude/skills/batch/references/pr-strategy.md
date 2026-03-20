# PR Strategy

Choose the right PR structure based on the size and nature of the change.

## Single PR (Small Changes — Under 50 Files)

Include a summary of files changed, verification results, and zero remaining references.

Example PR body:

```markdown
## Files Changed
- **Source**: 5 files (service, controllers, middleware)
- **Tests**: 5 files (unit, integration, e2e, fixtures)
- **Config**: 3 files (jest, tsconfig, CI)
- **Docs**: 3 files (architecture, API reference, README)

## Verification
- TypeScript: `npx tsc --noEmit` — clean
- Tests: `npm test` — 142 passed, 0 failed
- Lint: `npx eslint` — 0 warnings
- Zero remaining references to old name in source/test files
```

## Split by Module (Large Changes — 50-200 Files)

For changes spanning multiple modules or team boundaries:

```bash
# PR 1: Core service rename
gh pr create --title "refactor: rename UserService core module" \
  --body "Part 1/4 of UserService → AccountService rename. Core module only."

# PR 2: Controller layer
gh pr create --title "refactor: update controllers for AccountService rename" \
  --body "Part 2/4. Updates all controller imports and usage. Depends on PR #1."

# PR 3: Test updates
gh pr create --title "test: update tests for AccountService rename" \
  --body "Part 3/4. Renames test files and updates mocks/fixtures."

# PR 4: Documentation and config
gh pr create --title "docs: update docs for AccountService rename" \
  --body "Part 4/4. Documentation and CI config updates."
```

## PR Description Template for Batch Changes

Every batch-change PR should include:

```markdown
## Summary
<1-2 sentences: what changed and why>

## Change Pattern
<The mechanical transformation applied>
- `OldName` → `NewName`
- `oldImport` → `newImport`

## Scope
- Files changed: X
- Lines added: Y
- Lines removed: Z

## Verification
- [ ] Type checker: clean
- [ ] Full test suite: passing
- [ ] Linter: zero warnings
- [ ] Zero remaining references to old pattern
- [ ] Symbol count matches (before: N, after: N)

## Rollback
To revert this change:
`git revert <commit-hash>` (single PR)
`git revert <tag>..HEAD` (multi-PR, see rollback tags)
```
