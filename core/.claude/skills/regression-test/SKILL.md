---
name: regression-test
description: >
  Run targeted regression tests based on code changes. Analyze git diffs to identify affected
  source files, map them to test files via import graphs and naming conventions, classify risk,
  execute tests in priority order, and report confidence in the change.
type: workflow
allowed-tools: "Bash Read Grep Glob Agent"
argument-hint: "<branch|commit-range|staged> [--full] [--framework pytest|jest|gradle]"
triggers:
  - regression test
  - regression
  - affected tests
  - impact analysis
  - change impact
version: "1.1.0"
---

# Regression Test — Change-Aware Test Execution

Identify what changed, find the tests that cover those changes, run them in priority order, and report confidence. Fast feedback on targeted tests first, broader regression only when warranted.

**Critical constraint:** This skill MUST NOT modify source code or test files. It is a diagnostic workflow.

**Target:** $ARGUMENTS

---

## STEP 1: Identify Changes

Determine the changeset based on the provided arguments.

```bash
BASE_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")

# Select mode based on argument:
git diff --cached --name-only --diff-filter=ACMR          # staged
git diff --name-only --diff-filter=ACMR                   # unstaged
git diff --name-only "$BASE_BRANCH"...HEAD                # branch diff
git diff --name-only <commit1>..<commit2>                 # commit range
```

Argument modes: `staged` (cached only), branch name (diff HEAD against it), `abc123..def456` (commit range), no argument (all uncommitted).

### 1.1 Classify Changed Files

| Category | Pattern | Action |
|----------|---------|--------|
| Source code | `src/**`, `lib/**`, `app/**` (excluding tests) | Map to tests in STEP 2 |
| Test files | `tests/**`, `**/*_test.*`, `**/*.test.*`, `**/*.spec.*` | Run directly in STEP 4 |
| Config files | `*.yml`, `*.yaml`, `*.json`, `*.toml`, `*.cfg` | Flag for broad regression |
| Build/CI | `Dockerfile`, `*.gradle`, `pom.xml`, `package.json` | Flag for full suite |
| Documentation | `*.md`, `*.rst`, `*.txt` | Skip — no tests needed |
| Migrations | `migrations/**`, `alembic/**` | Flag as high risk |

Record `CHANGED_SOURCE_FILES`, `CHANGED_TEST_FILES`, `CHANGED_CONFIG_FILES`, and `TOTAL_CHANGED`.

---

## STEP 2: Map Changes to Tests

For each file in `CHANGED_SOURCE_FILES`, find corresponding test files. Use a subagent to parallelize mapping for large changesets (>15 files).

### 2.1 Naming Convention Mapping

Try common patterns per language:

- **Python:** `src/auth/service.py` -> `tests/test_auth_service.py` or `tests/auth/test_service.py`
- **JS/TS:** `src/auth/service.ts` -> `src/auth/service.test.ts` or `__tests__/auth/service.test.ts`
- **Java/Kotlin:** `src/main/.../AuthService.java` -> `src/test/.../AuthServiceTest.java`
- **Go:** `pkg/auth/service.go` -> `pkg/auth/service_test.go` (co-located)
- **Ruby:** `lib/auth/service.rb` -> `spec/auth/service_spec.rb`

Strategies: (1) mirror path with test prefix/suffix, (2) co-located tests, (3) glob for filename match.

### 2.2 Import Graph Tracing (2-Level Transitive)

For shared modules (utilities, base classes, types), trace importers up to 2 levels deep. This catches indirect dependents that would be missed by single-level tracing.

**Level 1 — Direct importers of the changed module:**

```bash
# Python:  grep -r "from changed_module import" --include="*.py" -l
# JS/TS:   grep -r "from.*changed_module" --include="*.ts" --include="*.js" -l
# Java:    grep -r "import.*ChangedClass" --include="*.java" --include="*.kt" -l
```

**Level 2 — Importers of each Level-1 file:**

For each direct importer found in Level 1, repeat the import search to find files that import the Level-1 file. Apply naming convention mapping to all Level-1 and Level-2 importers.

```bash
# For each Level-1 importer, find its importers:
# Python:  grep -r "from level1_module import" --include="*.py" -l
# JS/TS:   grep -r "from.*level1_module" --include="*.ts" --include="*.js" -l
# Java:    grep -r "import.*Level1Class" --include="*.java" --include="*.kt" -l
```

**Transitive dependency cap:** Stop at 2 levels — do not trace Level-3 or deeper. If the combined count of Level-1 and Level-2 dependents exceeds 20, auto-escalate to full test suite instead of tracing further. Log the escalation:

```
Transitive dependents: {count} (> 20 threshold) — escalating to full suite
```

### 2.3 Coverage Mapping (If Available)

If `coverage.json` (pytest-cov) or `coverage-final.json` (Istanbul/NYC) exists, parse it to find tests that exercised the changed source files. If unavailable, note it and rely on 2.1 + 2.2.

### 2.4 Build the Test Map

```
CHANGED FILE                     -> AFFECTED TESTS
src/services/auth.py             -> tests/test_auth.py, tests/integration/test_login.py
src/utils/validation.py          -> tests/test_validation.py, tests/test_auth.py (via import)
[NO TESTS FOUND]                 -> src/services/<unmapped-file>
```

Flag any source file with **no mapped tests** as a coverage gap.

---

## STEP 3: Classify Risk

Rank changed areas by risk to prioritize test execution.

| Risk Level | Areas | Rationale |
|------------|-------|-----------|
| CRITICAL | Auth, authorization, payment, crypto, security | Bugs cause breaches or financial loss |
| HIGH | Core business logic, data models, API contracts, migrations | Bugs break primary functionality |
| MEDIUM | API routes, controllers, middleware, integrations | Bugs affect specific features |
| LOW | Utilities, helpers, formatting, logging | Limited blast radius |
| SKIP | Documentation, comments, test-only changes | No production risk |

Detect risk via path patterns: `**/auth/**`, `**/security/**` = CRITICAL; `**/models/**`, `**/migrations/**` = HIGH; `**/api/**`, `**/routes/**` = MEDIUM; `**/utils/**` = LOW.

Compute overall risk:

```
OVERALL_RISK = max(risk_level of all changed files)
If config files changed:     OVERALL_RISK = max(OVERALL_RISK, MEDIUM)
If migration files changed:  OVERALL_RISK = max(OVERALL_RISK, HIGH)
If >20 source files changed: OVERALL_RISK = max(OVERALL_RISK, HIGH)
```

---

## STEP 4: Execute Targeted Tests

Run only tests mapped to changed files. Order by risk (CRITICAL first, then HIGH, MEDIUM, LOW).

### Framework-Specific Test Selection

**Python (pytest):**
```bash
pytest tests/test_auth.py tests/test_user.py -x -v        # specific files, fail-fast
pytest -k "auth or user_model" -v                          # keyword match
```

**JavaScript/TypeScript (Jest / Vitest):**
```bash
npx jest --findRelatedTests src/services/auth.ts -verbose  # related tests
npx jest --testPathPattern="auth|user" --verbose           # path match
npx vitest run auth user                                   # vitest pattern
```

**Java/Kotlin (Gradle):**
```bash
./gradlew test --tests "*AuthServiceTest" --tests "*UserTest"
./gradlew connectedDebugAndroidTest -Pandroid.testInstrumentationRunnerArguments.class=com.example.AuthTest
```

**Go:**
```bash
go test ./pkg/auth/... ./pkg/models/... -v                 # specific packages
go test ./... -run "TestAuth|TestUser" -v                   # pattern match
```

**Ruby (RSpec):**
```bash
bundle exec rspec spec/services/auth_spec.rb spec/models/user_spec.rb
```

Record pass/fail/skip status, duration, and failure messages for each test. If any test **fails**, stop — do not expand scope until failures are addressed.

---

## STEP 5: Expand to Full Suite

After targeted tests pass, decide scope expansion based on risk.

| Condition | Action |
|-----------|--------|
| OVERALL_RISK = CRITICAL | Run full test suite |
| OVERALL_RISK = HIGH | Run affected module suite + integration tests |
| OVERALL_RISK = MEDIUM, <10 files | Targeted tests sufficient |
| OVERALL_RISK = LOW, <5 files | Targeted tests sufficient |
| Config files changed | Run integration and E2E tests |
| `--full` flag provided | Run full suite regardless |
| >10 transitive dependents | Run full suite for safety |

Run E2E tests only if API contracts, route handlers, or auth logic changed, or if `--full` was provided.

```bash
# Full suite examples:
pytest tests/ -v --tb=short                                # Python
npx jest --verbose                                         # JavaScript
./gradlew test                                             # Gradle
go test ./... -v                                           # Go
```

---

## STEP 6: Report

### 6.1 Summary Format

```
REGRESSION TEST REPORT
========================
Change Scope:
  Target: <branch> (vs <base>)
  Files changed: N source, N tests, N config
  Overall risk: <LEVEL> (<reason>)

Test Mapping:
  Source files with tests:    N / M  (%)
  Coverage gaps:              N      [listed below]
  Total test files executed:  N

Targeted Test Results:
  Passed: N | Failed: N | Skipped: N | Duration: Ns

Expanded Suite: <RAN / SKIPPED> (<reason>)

Confidence: <HIGH|MEDIUM|LOW|BLOCKED>
Recommended Actions:
  1. <action item>
```

### 6.2 Confidence Levels

| Level | Criteria |
|-------|----------|
| HIGH | All tests pass, no coverage gaps, risk <= MEDIUM |
| MEDIUM | All tests pass but coverage gaps exist, OR HIGH risk with full suite passing |
| LOW | Any test failure, OR CRITICAL risk with coverage gaps |
| BLOCKED | Test infrastructure broken, cannot run tests |

### 6.3 Structured Output

Write to `test-results/regression-test.json`:

```json
{
  "skill": "regression-test",
  "timestamp": "<ISO-8601>",
  "result": "PASSED|FAILED",
  "summary": { "total": 47, "passed": 46, "failed": 1, "skipped": 0, "flaky": 0 },
  "change_scope": { "source_files": 8, "test_files": 3, "config_files": 1, "overall_risk": "HIGH" },
  "coverage_gaps": ["<files with no mapped tests>"],
  "confidence": "MEDIUM",
  "failures": [{ "test": "<name>", "file": "<path>", "message": "<error>" }],
  "duration_ms": 12300
}
```

---

## MUST DO

- Always start with `git diff` to determine the actual changeset — never guess what changed
- Always attempt multiple test-mapping strategies (naming, import graph, coverage) before declaring a file untested
- Always run CRITICAL and HIGH risk tests before MEDIUM and LOW
- Always report coverage gaps — files with no mapped tests are the highest risk
- Always stop expansion if targeted tests fail — fix failures before running more tests
- Always produce both human-readable and machine-readable output
- Always detect the project's test runner from `package.json`, `pyproject.toml`, `build.gradle`, or equivalent
- Always flag config and migration changes as requiring broader test scope

## MUST NOT DO

- MUST NOT modify source code or test files — this skill is diagnostic only
- MUST NOT run the full test suite by default — targeted tests first, expand only when warranted
- MUST NOT skip test mapping and blindly run all tests — that defeats the purpose of regression targeting
- MUST NOT ignore import graph dependencies — a change to a shared utility affects all its importers
- MUST NOT report HIGH confidence when coverage gaps exist — uncovered code is unknown risk
- MUST NOT assume a specific test framework — detect from project configuration
- MUST NOT use hardcoded file paths — use glob patterns and project-relative paths
- MUST NOT run destructive commands (git reset, git clean, git checkout) — read-only git operations only
