# 6.1 Single PR (Small Changes — Under 50 Files)

### 6.1 Single PR (Small Changes — Under 50 Files)

For straightforward renames or pattern updates affecting fewer than 50 files:

```bash
gh pr create \
  --title "refactor: rename UserService to AccountService" \
  --body "## Summary
- Renamed UserService class, file, and all references to AccountService
- Updated 18 files across controllers, middleware, tests, and documentation
- All tests passing, type checker clean

