# Auto-Simplify Cleanup

After a codebase-wide change, leftover artifacts accumulate. Run a cleanup pass to
remove dead code, unused imports, and redundant patterns.

## Remove Unused Imports

Renames often leave behind imports of the old name that the search-and-replace missed:

```bash
# TypeScript/JavaScript: use eslint auto-fix
npx eslint src/ tests/ --rule '{"no-unused-vars": "error", "import/no-unresolved": "error"}' --fix

# Python: use autoflake
autoflake --remove-all-unused-imports --in-place --recursive src/ tests/

# Go: goimports handles this automatically
goimports -w src/
```

## Delete Dead Code

After API migrations, old adapter code or compatibility shims may no longer be needed:

```bash
# Search for the old API surface that should no longer have callers
grep -rn "oldApiCall\|legacyEndpoint\|deprecatedMethod" src/

# If zero results, the old code is dead — remove it
rm src/compat/legacy-api-adapter.ts
rm src/utils/deprecated-helpers.ts
```

## Remove Redundant Type Assertions

After a type rename, explicit type assertions that cast to the old type become errors
or unnecessary casts to the new type:

```bash
# Find casts that reference the change
grep -rn "as AccountService\|<AccountService>" src/ --include="*.ts"

# Review each: is the cast still needed, or was it only there because of the old type?
```

## Run Formatter

Ensure all changes conform to the project's formatting standards:

```bash
# Prettier
npx prettier --write src/ tests/

# Black (Python)
black src/ tests/

# gofmt
gofmt -w src/

# rustfmt
cargo fmt
```
