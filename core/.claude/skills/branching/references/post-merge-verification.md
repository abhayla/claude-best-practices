# Post-Merge Verification

After the merge lands on the base branch, verify that everything is healthy.

## 6.1 Update Local Base Branch

```bash
git checkout "$BASE_BRANCH"
git pull origin "$BASE_BRANCH"
echo "Local $BASE_BRANCH updated to $(git rev-parse --short HEAD)"
```

## 6.2 Run the Full Test Suite

```bash
# Detect the test runner and run tests
if [ -f package.json ]; then
  npm test
elif [ -f pytest.ini ] || [ -f pyproject.toml ] || [ -f setup.cfg ]; then
  python -m pytest
elif [ -f build.gradle ] || [ -f build.gradle.kts ]; then
  ./gradlew test
elif [ -f Cargo.toml ]; then
  cargo test
elif [ -f go.mod ]; then
  go test ./...
elif [ -f Makefile ] && grep -q '^test:' Makefile; then
  make test
else
  echo "WARNING: Could not detect test runner. Run tests manually."
fi
```

## 6.3 Run the Build

```bash
# Detect the build system and run build
if [ -f package.json ]; then
  npm run build 2>/dev/null || echo "No build script defined — skipping."
elif [ -f build.gradle ] || [ -f build.gradle.kts ]; then
  ./gradlew build
elif [ -f Cargo.toml ]; then
  cargo build
elif [ -f go.mod ]; then
  go build ./...
elif [ -f Makefile ] && grep -q '^build:' Makefile; then
  make build
else
  echo "No build system detected — skipping build verification."
fi
```

## 6.5 Compare Key Metrics (Optional)

```bash
# If the project tracks bundle size
if [ -f package.json ] && grep -q '"size"' package.json; then
  npm run size 2>/dev/null
fi

# Count total tests (rough check for test count regression)
if [ -f package.json ]; then
  npm test 2>&1 | grep -E 'Tests?:|passed|failed' | tail -3
elif [ -f pytest.ini ] || [ -f pyproject.toml ]; then
  python -m pytest --co -q 2>/dev/null | tail -1
fi
```
