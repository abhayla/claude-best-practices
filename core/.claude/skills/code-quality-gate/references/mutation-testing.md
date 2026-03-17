# Mutation Testing — Reference

Extracted from `/code-quality-gate` Step 8.5 for size management.
This file is loaded on-demand when Step 8.5 executes.

## STEP 8.5: Mutation Testing

Run mutation testing on changed files to validate that the test suite catches real bugs, not just achieves line coverage.

### 8.5.1 Detect Mutation Testing Tool

| Stack | Tool | Detection |
|-------|------|-----------|
| Python | mutmut | `pip show mutmut` or `mutmut` in `pyproject.toml` / `requirements*.txt` |
| JavaScript/TS | Stryker | `npx stryker --version` or `@stryker-mutator/core` in `package.json` |

If the tool is not installed, install it:

```bash
# Python
pip install mutmut

# JavaScript/TypeScript
npx stryker init
```

### 8.5.2 Run Mutation Testing on Changed Files

Scope mutation testing to files changed in the current branch to keep execution time reasonable:

**Python (mutmut):**
```bash
# Get changed source files (exclude tests)
CHANGED=$(git diff --name-only origin/main...HEAD -- '*.py' | grep -v test)

# Run mutmut on each changed file
for f in $CHANGED; do
  mutmut run --paths-to-mutate="$f" 2>&1
done

# View results
mutmut results
```

**JavaScript/TypeScript (Stryker):**
```bash
# Get changed source files (exclude tests)
CHANGED=$(git diff --name-only origin/main...HEAD -- '*.ts' '*.tsx' '*.js' | grep -v test | grep -v spec)

# Run Stryker with file-level scope
npx stryker run --mutate "$CHANGED"
```

### 8.5.3 Evaluate Mutation Score

Calculate the mutation score: `killed mutants / total mutants * 100`.

| Mutation Score | Rating | Gate Action |
|---------------|--------|-------------|
| >= 80% | Excellent | PASS — tests effectively catch bugs |
| 60-79% | Acceptable | PASS with WARNING — review surviving mutants |
| 40-59% | Weak | WARN — tests exist but miss many real bugs |
| < 40% | Inadequate | BLOCK — test suite provides false confidence |

### 8.5.4 Report Surviving Mutants

For each surviving mutant (mutation not caught by tests):

```markdown
## Mutation Testing Report

**Tool:** mutmut / Stryker
**Files tested:** <count>
**Total mutants:** <count>
**Killed:** <count> | **Survived:** <count> | **Timeout:** <count>
**Mutation score:** <percentage>%

### Surviving Mutants (top priority)

| File | Line | Mutation | Why It Survived |
|------|------|----------|-----------------|
| src/domain/<module>.py | 45 | Changed `>` to `>=` | No boundary test for threshold value |
| src/services/<module>.py | 112 | Removed return statement | No test asserts the return value |
```

For each surviving mutant, recommend a specific test to add. If the mutation is equivalent (does not change observable behavior), document it as such.

### 8.5.5 CI Integration Note

For CI pipelines, add mutation testing as a non-blocking check initially. Once the team baseline is established, enforce the threshold:

```yaml
# GitHub Actions example
- name: Mutation testing
  run: |
    mutmut run --paths-to-mutate=src/
    SCORE=$(mutmut results | grep -oP '\d+(?=% killed)')
    if [ "$SCORE" -lt 40 ]; then echo "BLOCK: mutation score $SCORE% < 40%"; exit 1; fi
    if [ "$SCORE" -lt 60 ]; then echo "WARN: mutation score $SCORE% < 60%"; fi
```

---