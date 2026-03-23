---
name: coverage-analysis
description: >
  Analyze test coverage across a project, identify gaps in critical code paths,
  and prioritize which files and functions to test next. Use when coverage is
  below target or when determining where to add tests for maximum impact.
type: workflow
allowed-tools: "Bash Read Grep Glob"
argument-hint: "[target-directory] [--threshold LINE:BRANCH e.g. 80:70]"
version: "1.0.0"
triggers:
  - "coverage analysis"
  - "test coverage"
  - "find untested code"
  - "coverage gaps"
  - "coverage report"
---

# Coverage Analysis Workflow

**This skill is analysis only — do not modify source code or test files.** Read coverage data, identify gaps, and report recommendations. The user decides what to act on.

Detect the project's test/coverage framework, run coverage collection, parse results,
identify gaps in critical code, and produce a prioritized action plan.

## Default Coverage Targets

| Metric   | Default | Override Source                              |
|----------|---------|----------------------------------------------|
| Line     | 80%     | `pyproject.toml`, `jest.config.*`, `vitest.config.*`, `build.gradle` |
| Branch   | 70%     | Same as above                                |
| Function | 75%     | Same as above                                |

Always read project configuration first. Only fall back to defaults when no
project-level targets are defined.

---

## STEP 1: Detect Framework

Identify which test and coverage framework the project uses by examining project
files. Check in this order and stop at the first match per language ecosystem.

### Python

1. Look for `pyproject.toml`, `setup.cfg`, or `pytest.ini`
2. Check for `pytest-cov` in dependencies:
   ```
   Grep for "pytest-cov" in pyproject.toml, requirements*.txt, setup.cfg, Pipfile
   ```
3. Check for `.coveragerc` or `[tool.coverage]` section in `pyproject.toml`
4. If `pytest-cov` is not installed, note it and recommend installation

### JavaScript / TypeScript

1. Read `package.json` — check `devDependencies` for:
   - `vitest` and `@vitest/coverage-v8` or `@vitest/coverage-istanbul`
   - `jest` and `--coverage` in test scripts, or `collectCoverage` in config
   - Standalone `c8` or `nyc` (istanbul CLI)
2. Check for `vitest.config.*`, `jest.config.*`, or `nyc` section in `package.json`

### Android / JVM

1. Look for `build.gradle` or `build.gradle.kts` files
2. Check for `jacoco` plugin: `apply plugin: 'jacoco'` or `id("jacoco")`
3. Check for `jacocoTestReport` task configuration

### Output of this step

Set internal variables:
- `FRAMEWORK` — one of: `pytest-cov`, `vitest-v8`, `vitest-istanbul`, `jest`, `c8`, `nyc`, `jacoco`, `unknown`
- `CONFIG_FILE` — path to the coverage configuration file (if any)
- `COVERAGE_TARGETS` — line/branch/function thresholds from project config or defaults

If the framework cannot be detected, inform the user and ask which framework
to use before proceeding.

---

## STEP 2: Run Coverage

Execute coverage collection using the detected framework. Always run from the
project root directory.

### Python (pytest-cov)

```bash
# Use python or python3 depending on the environment
python -m pytest --cov=<source-package> --cov-report=term-missing --cov-report=json:coverage.json --cov-branch -q
```

- `<source-package>` — auto-detect from `pyproject.toml` `[tool.pytest.ini_options]`
  `testpaths`, or from `src/` or top-level package directory
- If `--cov-branch` is not already configured, add it to capture branch coverage
- Parse coverage targets from `[tool.coverage.report]` `fail_under` if present

### JavaScript / TypeScript (vitest)

```bash
# Use npx, yarn dlx, or pnpm exec depending on the project's package manager
npx vitest run --coverage --coverage.reporter=json --coverage.reporter=text
```

- Coverage output typically goes to `coverage/coverage-final.json`
- Read thresholds from `vitest.config.*` under `coverage.thresholds`

### JavaScript / TypeScript (jest)

```bash
# Use npx, yarn dlx, or pnpm exec depending on the project's package manager
npx jest --coverage --coverageReporters=json --coverageReporters=text
```

- Coverage output typically goes to `coverage/coverage-final.json`
- Read thresholds from `jest.config.*` under `coverageThreshold.global`

### Android / JVM (jacoco)

```bash
./gradlew jacocoTestReport
```

- Report output typically at `build/reports/jacoco/test/jacocoTestReport.xml`
- Or per-module: `<module>/build/reports/jacoco/`

### Error handling

- If tests fail, report the failure count but continue with partial coverage data
  if a coverage report was still generated
- If coverage tooling is missing, provide the exact install command and stop
- Capture both stdout and stderr for diagnostic purposes

---

## STEP 3: Parse Results

Extract structured coverage metrics from the generated report.

### From JSON reports (pytest-cov, vitest, jest)

Read the coverage JSON file and extract per-file metrics:

| Metric     | JSON Path (pytest-cov)       | JSON Path (istanbul/v8)          |
|------------|------------------------------|----------------------------------|
| Line %     | `totals.percent_covered`     | `<file>.lines.pct`              |
| Branch %   | `totals.percent_covered_branches` | `<file>.branches.pct`      |
| Function % | `totals.covered_functions / total_functions` | `<file>.functions.pct` |
| Missing    | `<file>.missing_lines`       | `<file>.lines.uncovered`        |

### From XML reports (jacoco)

Parse the jacoco XML report:
- `<counter type="LINE">` — `missed` and `covered` attributes
- `<counter type="BRANCH">` — `missed` and `covered` attributes
- `<counter type="METHOD">` — `missed` and `covered` attributes
- Aggregate at package and class level

### Build per-file summary

For each source file, record:
- File path (relative to project root)
- Line coverage percentage
- Branch coverage percentage
- Function/method coverage percentage
- List of uncovered line numbers
- List of uncovered branch locations

Sort files by coverage percentage (ascending) to surface the worst-covered files first.

---

## STEP 4: Identify Gaps

Analyze uncovered code paths and classify them by risk.

### Risk classification

| Risk Level | Category | Examples |
|------------|----------|---------|
| Critical   | Security & Auth | Authentication, authorization, token validation, input sanitization |
| Critical   | Data Integrity | Payment processing, financial calculations, data migrations |
| High       | Business Logic | Domain rules, state machines, validation logic |
| High       | Error Handling | Exception handlers, retry logic, fallback paths |
| Medium     | Integration | API clients, database queries, external service calls |
| Low        | Infrastructure | Configuration loading, logging setup, utility helpers |
| Low        | UI/Presentation | View rendering, formatting, display logic |

### Gap identification process

1. For each file below the coverage target:
   a. Read the uncovered line numbers from Step 3
   b. Read the actual source file to understand what those lines do
   c. Classify uncovered regions by risk level using the table above
   d. Group contiguous uncovered lines into logical blocks (functions, branches, error handlers)

2. For branch coverage gaps specifically:
   a. Identify conditional branches where only one path is tested
   b. Flag untested error/exception branches as high priority
   c. Flag untested edge cases in validation logic

3. Build a gap inventory:
   - File path
   - Uncovered region (line range or function name)
   - Risk classification
   - Brief description of what is not tested

---

## STEP 5: Prioritize

Rank uncovered areas to recommend what to test next, combining three signals.

### Signal 1: Criticality (weight: 50%)

Use the risk classification from Step 4. Score:
- Critical = 10
- High = 7
- Medium = 4
- Low = 1

### Signal 2: Change Frequency (weight: 30%)

Run git log to find recently and frequently changed files:

```bash
git log --format='' --name-only --since='3 months ago' | sort | uniq -c | sort -rn | head -30
```

Files changed more frequently are more likely to introduce regressions
when untested. Score on a relative scale (most changed = 10, least = 1).

### Signal 3: Coverage Delta (weight: 20%)

How far below target is the file? Score:
- More than 40% below target = 10
- 20-40% below target = 7
- 10-20% below target = 4
- Less than 10% below target = 1

### Composite score

```
priority = (criticality * 0.5) + (change_frequency * 0.3) + (coverage_delta * 0.2)
```

Sort all gaps by composite score descending. Present the top 10-15 items
as the recommended testing backlog.

---

## STEP 6: Report

Output a structured summary with three sections.

### Section A: Coverage Summary

```
=== Coverage Summary ===

Overall:  Lines 74.2%  |  Branches 61.8%  |  Functions 69.5%
Target:   Lines 80.0%  |  Branches 70.0%  |  Functions 75.0%
Status:   BELOW TARGET (needs +5.8% lines, +8.2% branches, +5.5% functions)

Files analyzed: 42
Files below target: 12
Files with zero coverage: 2
```

### Section B: Module Breakdown

List coverage per top-level module/package, sorted by coverage ascending:

```
Module/Directory         Lines    Branches  Functions  Status
─────────────────────────────────────────────────────────────
src/auth/                52.3%    38.1%     44.0%      CRITICAL
src/payments/            61.7%    55.2%     58.3%      BELOW
src/api/handlers/        71.4%    63.0%     68.9%      BELOW
src/models/              88.2%    79.5%     91.0%      OK
src/utils/               93.1%    85.2%     95.0%      OK
```

### Section C: Prioritized Recommendations

Present the top recommendations from Step 5:

```
Priority  File                          Gap Description              Score
──────────────────────────────────────────────────────────────────────────
1         src/auth/token_validator       Token refresh error path     9.2
2         src/payments/charge            Partial refund branch        8.7
3         src/api/handlers/webhook       Signature verification       7.9
...
```

For each top-5 item, include:
- The specific uncovered lines or branches
- A one-sentence description of what test to write
- The estimated coverage improvement if this gap is filled

### Final notes

End the report with:
- Total estimated coverage if all recommended gaps are filled
- Suggested command to re-run coverage after writing new tests
- Any configuration improvements (e.g., adding branch coverage if not enabled)

---

## MUST DO

- Always detect the framework before running commands — never assume a specific tool
- Read project-level coverage configuration before applying defaults
- Show actual uncovered line numbers and code regions, not just percentages
- Classify gaps by business risk, not just raw numbers
- Use relative paths in all output — never absolute paths
- Include branch coverage analysis, not just line coverage
- Sort recommendations by composite priority score
- Provide actionable next steps (what test to write, not just "increase coverage")
- Handle monorepos by detecting per-package coverage configurations
- Report partial results if some tests fail during coverage collection

## MUST NOT DO

- Do not modify source code or test files — this skill is analysis only
- Do not run coverage with `--fail-under` that would exit non-zero and hide the report
- Do not ignore files just because they have low coverage — analyze why
- Do not treat all coverage gaps as equal — risk classification matters
- Do not hardcode file paths, package names, or project-specific references
- Do not assume a specific OS, package manager, or directory structure
- Do not skip branch coverage even if the project only tracks line coverage
- Do not report coverage for vendored, generated, or third-party code unless explicitly asked
