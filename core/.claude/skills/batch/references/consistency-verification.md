# Consistency Verification

After all batches complete and their branches are merged, verify the entire codebase is
consistent. Individual batch verification is necessary but not sufficient.

## Type Checker / Compiler

```bash
# TypeScript
npx tsc --noEmit

# Python (mypy)
mypy src/ --ignore-missing-imports

# Go
go build ./...

# Rust
cargo check

# Java/Kotlin
./gradlew compileJava compileKotlin
```

Every type error after a batch change indicates a missed reference.

## Linter

```bash
# ESLint
npx eslint src/ tests/ --max-warnings=0

# Ruff (Python)
ruff check src/ tests/

# golangci-lint
golangci-lint run ./...
```

Linter errors after renames often indicate unused imports or undefined references.

## Full Test Suite

```bash
# Run the complete test suite — not just the files that were changed
npm test
pytest tests/ -v
go test ./...
./gradlew test
```

A passing full suite is the strongest signal that the batch change is correct.

## Re-Run Impact Analysis

Repeat the search from Step 1 to verify no references were missed:

```bash
# The OLD name should appear ZERO times (excluding git history, changelogs, ADRs)
grep -rn "UserService" src/ tests/ --include="*.ts" --include="*.tsx" --include="*.js"

# Expected output: (empty)
# If any results remain, those files were missed — fix them before proceeding
```

## Symbol Count Comparison

For renames, verify the counts balance:

```bash
# Before the change (check from git history)
git stash
grep -rn "UserService" src/ tests/ --include="*.ts" | wc -l
# Result: 47

git stash pop
grep -rn "AccountService" src/ tests/ --include="*.ts" | wc -l
# Result: should be 47 (same count, new name)
```

If counts do not match, investigate: either references were missed, or some were
intentionally not renamed (ambiguous matches from Step 1.4).

## Import Graph Validation

Verify no broken import chains exist:

```bash
# TypeScript: check for unresolved imports
npx tsc --noEmit 2>&1 | grep "Cannot find module"

# Python: check for import errors
python -c "import src.services.AccountService" 2>&1

# Node.js: attempt to require the entry point
node -e "require('./src/index')" 2>&1
```
