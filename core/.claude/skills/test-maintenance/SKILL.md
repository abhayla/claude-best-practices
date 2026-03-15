---
name: test-maintenance
description: >
  Audit, clean up, and optimize a test suite. Identifies dead tests, duplicates,
  slow tests, and readability issues, then produces a health report with actionable
  recommendations. Use when test suites grow unwieldy, CI times balloon, or test
  confidence erodes from skips and flakes.
type: workflow
allowed-tools: "Bash Read Write Edit Grep Glob"
argument-hint: "[test_directory] [framework: pytest|jest|vitest] [focus: audit|dead|dupes|slow|readability|optimize|all]"
version: "1.1.0"
triggers:
  - test maintenance
  - test cleanup
  - test refactor
  - test health
  - test suite audit
  - slow tests
---

# Test Maintenance — Suite Health & Optimization

Audit a test suite for dead tests, duplicates, slow tests, and readability issues.
Produce a health dashboard with prioritized recommendations.

**CRITICAL**: This skill modifies test files. Always work on a clean git state —
verify no uncommitted changes before making edits. Recommend changes in batches
so the user can review before applying.

**Input:** $ARGUMENTS

---

## Framework Detection

If the user does not specify a framework, detect it automatically:

| Indicator | Framework |
|-----------|-----------|
| `pytest.ini`, `pyproject.toml` with `[tool.pytest]`, `conftest.py` | **pytest** |
| `jest.config.*`, `package.json` with `"jest"` key | **jest** |
| `vitest.config.*`, `package.json` with `"vitest"` key | **vitest** |
| `build.gradle*` with `testImplementation` | **JUnit/Android** |

Default test directories by framework:

| Framework | Common directories |
|-----------|--------------------|
| pytest | `tests/`, `test/`, `**/test_*.py` |
| jest | `__tests__/`, `**/*.test.{js,ts,tsx}`, `**/*.spec.{js,ts,tsx}` |
| vitest | `**/*.test.{js,ts,tsx}`, `**/*.spec.{js,ts,tsx}` |

---

## STEP 1: Audit Test Suite

Gather baseline metrics for the test suite health report.

### 1a. Count tests by type

Use framework-specific commands to collect test inventory:

**Python (pytest):**
```bash
# List all collected tests (dry run)
python -m pytest --co -q 2>/dev/null | tail -1

# Count by marker
python -m pytest --co -q -m unit 2>/dev/null | tail -1
python -m pytest --co -q -m integration 2>/dev/null | tail -1
python -m pytest --co -q -m e2e 2>/dev/null | tail -1
```

**JavaScript (jest):**
```bash
# List all tests without running
npx jest --listTests 2>/dev/null | wc -l

# Run with verbose to count pass/fail/skip
npx jest --verbose --detectOpenHandles 2>&1 | tail -20
```

If markers are not used, classify by heuristic:
- Files in `unit/` or with `test_unit_` prefix -> unit
- Files in `integration/` or with `test_integration_` prefix -> integration
- Files in `e2e/` or `end_to_end/` or with `test_e2e_` prefix -> e2e
- Remaining -> unclassified (flag for the report)

### 1b. Measure execution time

**Python (pytest):**
```bash
# Get the 20 slowest tests
python -m pytest --durations=20 -q 2>&1

# Full timing summary
python -m pytest --durations=0 -q 2>&1 | tail -30
```

**JavaScript (jest):**
```bash
# Jest shows timing per test file by default in verbose mode
npx jest --verbose 2>&1 | grep -E "^\s*(PASS|FAIL|Tests:|Time:)"
```

### 1c. Count skipped and expected-failure tests

**Python:** Search for `@pytest.mark.skip`, `@pytest.mark.xfail`, `pytest.skip()`
**JavaScript:** Search for `test.skip`, `it.skip`, `describe.skip`, `xit(`, `xdescribe(`

```bash
# Python skip/xfail count
grep -rn "@pytest.mark.skip\|@pytest.mark.xfail\|pytest.skip(" tests/ 2>/dev/null | wc -l

# JavaScript skip count
grep -rn "\.skip(\|xit(\|xdescribe(" __tests__/ src/ 2>/dev/null | wc -l
```

Record all metrics for the final report in STEP 7.

---

## STEP 2: Find Dead Tests

Dead tests provide false confidence — they pass but no longer test real code.

### 2a. Tests referencing deleted or renamed code

1. Extract all function/class names imported or called in test files
2. Search the source tree for each referenced name
3. Flag any test that references symbols not found in the codebase

```bash
# Python: extract tested function names, check if they exist in source
grep -rhoP "(?<=def test_)\w+" tests/ | sort -u | while read -r fn; do
  grep -rq "$fn" src/ lib/ app/ 2>/dev/null || echo "DEAD: test_$fn"
done
```

### 2b. Orphaned fixtures

Find fixtures or test helpers defined but never referenced:

- **Python:** `grep -rn "@pytest.fixture" tests/ conftest.py` — for each fixture name, check if it appears as a test function parameter. Zero references = orphaned.
- **JavaScript:** `grep -rn "export.*function\|module\.exports" __tests__/helpers/ test/utils/` — check each export for import references.

### 2c. Unused test data files

Search for test data files (JSON, CSV, fixtures) in test directories that are never
referenced by any test:

```bash
# Find fixture/data files
find tests/fixtures/ test/data/ __tests__/fixtures/ -type f 2>/dev/null | while read -r f; do
  basename_f=$(basename "$f")
  grep -rq "$basename_f" tests/ __tests__/ src/ 2>/dev/null || echo "ORPHANED: $f"
done
```

---

## STEP 2.5: Find Incomplete E2E Stubs

Scan the test suite for E2E test stubs that were generated but never implemented. Stubs that linger too long indicate forgotten test intent and erode confidence in E2E coverage.

### 2.5a. Detect E2E stub markers

Search for skip markers with E2E stub reasons:

**Python (pytest):**
```bash
# Find E2E stubs — @pytest.mark.skip with E2E stub reason
grep -rn "@pytest.mark.skip.*E2E stub\|@pytest.mark.skip.*e2e stub\|@pytest.mark.skip.*Stage 8" tests/ 2>/dev/null
```

**JavaScript (Playwright / Jest / Vitest):**
```bash
# Find E2E stubs — test.skip() with E2E stub markers
grep -rn "test\.skip.*E2E stub\|test\.skip.*e2e stub\|test\.skip.*Stage 8\|\.skip(.*stub" tests/ __tests__/ 2>/dev/null
```

### 2.5b. Count stubs vs implemented E2E tests

Compare the number of skipped E2E stubs against implemented (non-skipped) E2E tests:

```bash
# Python: count implemented E2E tests (not skipped)
python -m pytest tests/e2e/ --co -q 2>/dev/null | tail -1

# Python: count skipped E2E tests
python -m pytest tests/e2e/ --co -q -m "skip" 2>/dev/null | tail -1
```

Report the ratio:
- **Healthy:** <20% of E2E tests are stubs
- **Warning:** 20-50% of E2E tests are stubs — prioritize implementation
- **Critical:** >50% of E2E tests are stubs — E2E coverage is largely aspirational

### 2.5c. Flag stale stubs (older than 30 days)

Use `git blame` to check when each stub was created. Stubs older than 30 days are stale and should be either implemented or removed:

```bash
# For each stub file:line found in 2.5a, check the commit date
git blame -L <line>,<line> -- <file> --date=short 2>/dev/null
```

Compare the blame date against today. If the stub is older than 30 days, flag it:

```markdown
| Stub | File | Line | Created | Age | Status |
|------|------|------|---------|-----|--------|
| test_user_registration | tests/e2e/test_signup.py | 12 | 2026-01-15 | 59 days | STALE |
| test_checkout_flow | tests/e2e/test_checkout.py | 8 | 2026-03-01 | 14 days | OK |
```

### 2.5d. Recommendations

For each stale stub:
- If the feature is implemented: schedule E2E test implementation (fill in assertions and navigation)
- If the feature is not yet implemented: keep the stub but add a tracking issue reference
- If the feature was dropped: remove the stub entirely

Include stale stub count and stub-to-implemented ratio in the STEP 7 health report.

---

## STEP 3: Detect Duplicates

Duplicate tests waste CI time and create maintenance burden.

### 3a. Tests asserting the same behavior

1. Extract assertion targets from each test (the function/method under test + input pattern)
2. Group tests by target
3. Flag groups with 2+ tests that have overlapping assertions

Look for:
- Tests with identical or near-identical assertion lines
- Tests calling the same function with the same arguments
- Copy-pasted test bodies with only variable names changed

### 3b. Overlapping parametrize cases

**Python:** Check `@pytest.mark.parametrize` for redundant test cases:
- Duplicate rows in the parameter list
- Cases that test the same equivalence class (e.g., testing both `1` and `2` for "positive integer")

**JavaScript:** Check `test.each` / `describe.each` for the same issues.

### 3c. Redundant setup

Find `setUp` / `beforeEach` blocks that create identical state across multiple test
classes/describes. Candidates for extraction into shared fixtures.

---

## STEP 4: Identify Slow Tests

### 4a. Profile test execution

**Python:**
```bash
# Top 20 slowest tests with duration
python -m pytest --durations=20 --timeout=60 -q 2>&1
```

**JavaScript:**
```bash
# Jest shows slow tests automatically (>5s by default)
npx jest --verbose --detectOpenHandles 2>&1
```

### 4b. Classify slow test causes

Search each slow test for common causes:

| Pattern to search | Cause | Fix |
|-------------------|-------|-----|
| `time.sleep(`, `setTimeout(`, `await new Promise` | Hardcoded delays | Replace with polling/retry or mock time |
| `requests.get(`, `fetch(`, `axios.` without mock | Real HTTP calls | Add mocks for external services |
| `open(`, `fs.readFileSync`, `fs.writeFileSync` | Real file I/O | Use in-memory alternatives or tmp fixtures |
| `subprocess.run(`, `child_process.exec` | Spawning processes | Mock or isolate to integration suite |
| `@pytest.fixture(scope="function")` on heavy setup | Per-test heavy setup | Consider `scope="module"` or `scope="session"` |
| Database creation in every test | Per-test DB setup | Use transactions with rollback instead |

```bash
# Python: find sleep calls in tests
grep -rn "time\.sleep\|asyncio\.sleep" tests/ 2>/dev/null

# Python: find unmocked HTTP calls
grep -rn "requests\.\(get\|post\|put\|delete\)" tests/ 2>/dev/null | grep -v "mock\|patch\|Mock"

# JavaScript: find unmocked fetch/axios
grep -rn "fetch(\|axios\.\|http\." __tests__/ src/**/*.test.* 2>/dev/null | grep -v "mock\|jest\.\|vi\."
```

### 4c. Estimate savings

For each slow test, estimate time saved if the fix is applied:
- Replacing `sleep(N)` saves N seconds per invocation
- Mocking HTTP calls typically saves 0.5-3 seconds per call
- Fixture scoping improvements save setup time * (num_tests - 1)

---

## STEP 5: Improve Readability

### 5a. Standardize naming conventions

Check test naming against the project's dominant convention:

| Convention | Example |
|-----------|---------|
| `test_<action>_<condition>_<expected>` | `test_login_with_invalid_password_returns_401` |
| `should <behavior> when <condition>` | `should return 401 when password is invalid` |
| `<method>_<scenario>_<result>` | `login_invalidPassword_returns401` |

Flag tests that deviate from the dominant pattern. Suggest renames but do NOT
auto-rename without user approval.

### 5b. Enforce Arrange-Act-Assert (AAA) pattern

Scan test bodies for structure:
- **Arrange**: Setup/fixture code at the top
- **Act**: Single action being tested (one function call or request)
- **Assert**: Verification at the bottom

Flag tests that:
- Mix assertions throughout the body (interleaved act-assert)
- Have no clear separation between phases
- Contain multiple unrelated actions

### 5c. Consolidate inline test data

Find tests with hardcoded test data that should be extracted:
- Magic numbers repeated across tests
- Inline JSON/dict/object literals duplicated in multiple tests
- String constants used in assertions that could be factory-generated

Recommend extracting to:
- **Python:** `conftest.py` fixtures or a `factories.py` using `factory_boy` or similar
- **JavaScript:** Shared test helpers or a `factories/` directory

---

## STEP 6: Optimize Execution

### 6a. Recommend parallelization

- **Python:** Check for `pytest-xdist` (`pip show pytest-xdist`). If not installed, recommend `pip install pytest-xdist` and `python -m pytest -n auto` (uses all CPU cores). For CI, use a fixed worker count: `-n 4`.
- **JavaScript:** Jest parallelizes per-file by default. For tuning: `npx jest --maxWorkers=4` or `--maxWorkers=50%`.

### 6b. Fixture scoping improvements

**Python:** Audit fixture scopes and recommend promotions:

| Current scope | Candidate for promotion when... | New scope |
|--------------|--------------------------------|-----------|
| `function` (default) | Fixture is read-only and expensive to create | `module` or `session` |
| `module` | Fixture is identical across all modules | `session` |

NEVER promote fixtures that modify state — mutable fixtures MUST stay `function`-scoped.

### 6c. Test splitting for CI

Recommend splitting test suites into parallel CI jobs by type (unit / integration / e2e).
For large suites, recommend sharding:
- **Python:** `pytest --splits N --group G` (pytest-split) or `pytest-xdist`
- **JavaScript:** `jest --shard=1/3`, `jest --shard=2/3`, `jest --shard=3/3`

---

## STEP 7: Report

Generate a test health dashboard summarizing all findings.

### Dashboard format

```
============================================================
                    TEST HEALTH REPORT
============================================================

SUITE OVERVIEW
  Framework:        <detected framework>
  Total tests:      <count>
  Unit:             <count>  |  Integration: <count>  |  E2E: <count>
  Unclassified:     <count>

EXECUTION
  Total time:       <duration>
  Slowest test:     <name> (<duration>)
  Tests > 5s:       <count>
  Tests > 30s:      <count>

SKIP RATE
  Skipped:          <count> (<percentage>%)
  Expected fail:    <count> (<percentage>%)
  Skip rate:        <OK | WARNING if >5% | CRITICAL if >10%>

DEAD TESTS
  Dead references:  <count>
  Orphaned fixtures:<count>
  Orphaned data:    <count>

DUPLICATES
  Duplicate tests:  <count> groups
  Redundant params: <count> cases
  Duplicate setup:  <count> blocks

SLOW TESTS (top 5)
  1. <test_name> — <duration> — <cause>
  2. <test_name> — <duration> — <cause>
  ...

RECOMMENDATIONS (by estimated impact)
  Priority  Action                           Est. Time Saved
  --------  ------                           ---------------
  HIGH      Mock HTTP calls in 12 tests      ~18s per run
  HIGH      Remove 5 dead tests              maintenance burden
  MEDIUM    Promote 3 fixtures to session     ~8s per run
  MEDIUM    Deduplicate 4 test groups         ~4s per run
  LOW       Rename 15 tests for consistency   readability
  LOW       Add pytest-xdist for parallelism  ~40% wall time

ESTIMATED TOTAL SAVINGS: <time> per CI run
============================================================
```

Present the report to the user. If `--apply` or `focus` was specified, offer to
execute the recommended changes interactively, one batch at a time.

---

## MUST DO

- Verify clean git state (`git status`) before modifying any test files
- Run the full test suite after each batch of changes to confirm nothing broke
- Preserve all existing test coverage — never delete a test unless its target code is confirmed deleted
- Show the user each proposed change before applying it
- Classify recommendations by priority (HIGH / MEDIUM / LOW) based on time savings
- Support both Python and JavaScript ecosystems with appropriate commands
- Count actual test functions, not test files, for accurate metrics

## MUST NOT DO

- MUST NOT delete tests without confirming the tested code no longer exists
- MUST NOT change test behavior — only structure, naming, and performance
- MUST NOT auto-apply changes without user review and approval
- MUST NOT assume a specific test directory — detect or ask
- MUST NOT skip the audit step even if the user asks to "just fix slow tests" — baseline metrics are required for the report
- MUST NOT introduce new dependencies without flagging them to the user (e.g., `pytest-xdist`, `factory_boy`)
- MUST NOT use hardcoded paths — always detect or accept as argument
- MUST NOT modify source code (non-test files) — this skill is test-only
