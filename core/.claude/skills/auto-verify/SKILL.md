---
name: auto-verify
description: >
  Post-change verification loop: identifies changed files, maps to targeted tests,
  queries knowledge.db for known patterns, runs tests with smart priority selection,
  analyzes failures with automated diagnosis, applies fixes with approval checkpoints,
  runs regression checks, and records all outcomes to knowledge.db.
allowed-tools: "Bash Read Grep Glob Skill Task"
argument-hint: "[--scope backend|android|all] [--base HEAD~1] [--max-iterations 5]"
---

# Auto-Verify

Post-change verification that identifies changed files, maps to targeted tests, queries the knowledge database for known error patterns, runs tests with smart priority, analyzes failures, applies fixes with approval checkpoints, runs regression checks, and records outcomes.

**Arguments:** $ARGUMENTS

---

## Input Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `scope` | string | `"all"` | `backend`, `android`, or `all` |
| `base` | string | `"HEAD~1"` | Git base ref for change detection |
| `max_iterations` | int | `5` | Maximum fix iterations before stopping |
| `skip_regression` | bool | `false` | Skip regression checks after fix |
| `dry_run` | bool | `false` | Show what would run without executing |

---

## The 8-Step Algorithm

### Step 0: Cleanup + Prerequisites

1. **Clean old screenshots** (>24h) from `docs/testing/screenshots/`:
   ```bash
   find docs/testing/screenshots/ -name "*.png" -mtime +1 -delete 2>/dev/null || true
   ```

2. **Check scope prerequisites:**
   - `backend`: Verify backend running: `curl -sf http://localhost:8000/docs > /dev/null`
     - If not running: `cd backend && PYTHONPATH=. uvicorn app.main:app --port 8000 &` (wait 3s)
   - `android`: Verify emulator: check adb devices output for "emulator"
   - `all`: Check both

3. **Ensure test-map freshness:**
   ```bash
   python .claude/scripts/generate_test_map.py
   ```
   Regenerate if missing or >7 days old.

### Step 1: Identify Changes

```bash
git diff --name-only {base}
```

**Filter rules:**
- Include: `.py`, `.kt`, `.xml`, `.kts` files
- Exclude: `docs/`, `*.md`, `*.json`, `*.yml`, `*.yaml`, test files themselves
- Skip: files that are ONLY whitespace/comment changes

**Classify each file:**

| Path Pattern | Category |
|---|---|
| `backend/app/**` | `backend` |
| `backend/tests/**` | skip (test file) |
| `android/app/src/main/**` | `android-app` |
| `android/app/src/test/**` | skip (test file) |
| `android/app/src/androidTest/**` | skip (test file) |
| `android/data/**`, `android/domain/**`, `android/core/**` | `android-data`, `android-domain`, `android-core` |

If no changed files match scope: report "No changes in scope" and exit SUCCESS.

### Step 2: Map to Tests (Smart Selection)

For each changed file, find tests using prioritized lookup:

**Priority 0 — Smart Affected (test-map.json):**
```bash
python .claude/scripts/generate_test_map.py lookup {source_file}
```
Collect P1 + P2 tests, deduplicate.

**Priority 1 — Direct Convention:**

| Source Pattern | Test Pattern |
|---|---|
| `backend/app/api/v1/endpoints/{name}.py` | `backend/tests/test_{name}_api.py` |
| `backend/app/services/{name}_service.py` | `backend/tests/test_{name}_service.py` or `test_{name}.py` |
| `android/.../presentation/{feat}/{Feat}ViewModel.kt` | `android/.../test/.../presentation/{feat}/{Feat}ViewModelTest.kt` |
| `android/.../presentation/{feat}/{Feat}Screen.kt` | `android/.../androidTest/.../presentation/{feat}/{Feat}ScreenTest.kt` |

**Priority 2 — Import-based:**
Use Grep to find test files importing changed modules. Cap at 10 files.

**Priority 3 — Module Fallback:**
- Backend: `PYTHONPATH=. pytest backend/tests/ -v`
- Android unit: `./gradlew :app:testDebugUnitTest`

**Cap:** Maximum 20 test files per run. If more, fall back to Priority 3 (full module).

### Step 2c: Knowledge Base Pre-Check

For each changed file/area, query the KB for known issues:

```bash
bash .claude/scripts/query_knowledge.sh "TestFailure" "$RECENT_ERROR" "$FILE_PATH"
```

**Score-based behavior:**

| KB Score | Action |
|---|---|
| >= 0.7 | Try KB strategy FIRST, skip standard diagnosis |
| 0.3 — 0.7 | Use as hint alongside standard diagnosis |
| < 0.3 or none | Proceed with standard diagnosis only |

### Step 3: Run Targeted Tests

Execute tests by platform:

**Backend:**
```bash
cd backend && PYTHONPATH=. pytest {test_files} -v --tb=short 2>&1 | tee ../.claude/logs/auto-verify-output.log
```

**Android unit:**
```bash
cd android && ./gradlew :app:testDebugUnitTest --tests "{patterns}" 2>&1 | tee ../.claude/logs/auto-verify-output.log
```

**Android UI/E2E:**
```bash
cd android && ./gradlew :app:connectedDebugAndroidTest -Pandroid.testInstrumentationRunnerArguments.class={class} 2>&1 | tee ../.claude/logs/auto-verify-output.log
```

Record: test count, pass count, fail count, duration.

### Step 4: Analyze Results

If all tests pass: skip to Step 7 (regression check).

If failures exist, use the automated diagnosis table (see `references/automated-diagnosis.md`):

| Error Pattern | Automated Action | Rationale |
|---|---|---|
| `AssertionError: assert X == Y` | Check if test expectation outdated | Common after refactoring |
| `ImportError: cannot import name` | Check circular imports, renamed modules | Module restructuring |
| `IntegrityError: duplicate key` | Check upsert vs insert, unique constraints | DB constraint violation |
| `sqlalchemy.exc.MissingGreenlet` | Add `selectinload()` for eager loading | Async SQLAlchemy gotcha |
| `Timeout` / `asyncio.TimeoutError` | Check Gemini/API call blocking event loop | Known KKB issue |
| `FileNotFoundError` / `ModuleNotFoundError` | Check PYTHONPATH, working directory | Path issues |
| `Room migration` / `Schema mismatch` | Check Room version, run clean build | DB schema drift |
| `Hilt` / `@Inject` errors | Run `./gradlew clean :app:kspDebugKotlin` | KSP codegen issue |
| `CompilationError` | Check missing constructor params, type mismatches | Kotlin compilation |

### Step 5: Decision Point

| Outcome | Iteration | Action |
|---|---|---|
| All pass | Any | **SUCCESS** -> Step 7 |
| Known pattern (KB score >= 0.6) | 1-2 | Apply KB strategy -> Step 3 |
| Unknown failure | 1 | Analyze -> apply fix -> Step 3 |
| Same error 2x | 2 | Escalate: invoke `/fix-loop` with `max_iterations: 3` |
| Same error 3x | 3+ | **STOP** -> ask user |
| Max iterations reached | 5 | **STOP** -> show summary, ask user |

### Step 6: Fix and Iterate (with Approval Checkpoints)

See `references/approval-scenarios.md` for the complete list.

**Auto-approved (no confirmation needed):**
- Simple value updates in assertions (expected changed)
- Missing import fixes
- PYTHONPATH / path fixes
- Known KB strategies with score >= 0.3 AND iteration <= 2

**Require user approval (AskUserQuestion):**
1. Protected files: `.env`, `conftest.py`, `build.gradle.kts`, `alembic/versions/`
2. Shared utilities: test fixtures, base classes, DI modules
3. Database schema: Alembic migrations, Room migrations
4. Multi-feature impact: changes affecting >1 module
5. Assertion changes: modifying test expectations to match new behavior
6. Mock/dummy data: using fakes instead of real behavior
7. Disabling tests: skip, ignore, commenting out
8. Workarounds: patches instead of proper fixes
9. Assumptions: guessing intended behavior
10. Iteration threshold: after 3 iterations (prevent thrashing)
11. Max attempts: after 5 total attempts (safety valve)

**Approval format:**
```
Approval Required: {reason}

Proposed change:
  {file_path}:{line_number}
  - Old: {old_code}
  + New: {new_code}

Impact: {what_this_affects}
Alternatives: {other_options}
```

After applying a fix, go back to Step 3 (re-run tests).

### Step 7: Regression Check

After targeted tests pass, run adjacent tests to catch regressions.

**Backend adjacency map:**

| Fixed Area | Also Test |
|---|---|
| auth_service, auth | email_uniqueness, auth_merge |
| recipe_rules | recipe_rules_dedup, recipe_rules_sync, recipe_rules_lifecycle |
| meal_plans, ai_meal_service | family_aware_meal_gen |
| recipes, recipe_service | recipe_search, recipe_rating |
| chat | chat_integration, chat_api |
| users, user_service | user_preferences |
| family_members | family_members_api |
| notifications | notification_triggers |

**Android adjacency:**
- ViewModel fix -> also run corresponding ScreenTest
- ScreenTest fix -> also run corresponding ViewModelTest
- Repository fix -> run all ViewModelTests that use it

```bash
# Backend regression
cd backend && PYTHONPATH=. pytest {adjacent_tests} -v --tb=short

# Android regression
cd android && ./gradlew :app:testDebugUnitTest --tests "{adjacent_patterns}"
```

If regression found:
1. Revert the fix that caused regression
2. Escalate to `/fix-loop` with broader context
3. Record failure in KB

If `skip_regression` is true: skip this step.

### Step 8: Record to Knowledge DB

**On success (tests pass):**
```bash
# Record successful strategy
python .claude/scripts/knowledge_db.py record-attempt \
  --error-id $ERROR_ID --strategy-id $STRATEGY_ID \
  --outcome success --description "$FIX_DESCRIPTION"
```
- If this was a new error pattern: auto-create via `record-error` + `create-strategy`
- Strategy score boosted (+0.1)

**On failure (fix didn't work):**
```bash
python .claude/scripts/knowledge_db.py record-attempt \
  --error-id $ERROR_ID --strategy-id $STRATEGY_ID \
  --outcome failure --description "$WHAT_WAS_TRIED"
```
- Strategy score decreased (-0.05)

---

## Iteration Display Format

Show progress in every response:

```
[Iteration 1/5 | Priority 0 | backend] Running targeted tests...
Tests: 3 files (test_auth.py, test_auth_merge.py, test_email_uniqueness.py)
Result: PASS (23/23) | Duration: 4.2s | Status: SUCCESS

[Iteration 2/5 | Priority 1 | android-unit] Running ViewModel tests...
Tests: HomeViewModelTest
Result: FAIL (IntegrityError: duplicate key) | Strategy: KB #3 (score: 0.72)

[Iteration 3/5 | fix-loop] Escalated — applying known strategy...
Strategy: add_upsert (score: 0.72)
Fix: Changed insert to upsert in HomeRepository
Result: PASS | Regression Check: Running...
```

---

## Stop Conditions

| Condition | Action |
|---|---|
| All tests + regressions pass | Report SUCCESS with full summary |
| Max iterations (5) | Show summary, AskUserQuestion: Continue / Skip / Manual |
| Same error 3x | Auto-escalate to `/fix-loop` with full iteration memory |
| All KB strategies exhausted | AskUserQuestion: New heuristic / Record pattern / Skip |
| Cross-feature regression | AskUserQuestion before wider fix |

---

## Output Format

```markdown
## Auto-Verify Results

### Status: {SUCCESS | PARTIAL | FAILED | MAX_ITERATIONS}

### Summary
- Scope: {backend | android | all}
- Changed files: N
- Tests mapped: N (P0: N, P1: N, P2: N)
- Tests run: N
- Tests passed: N
- Tests failed: N
- Iterations used: N / max_iterations
- Regressions checked: N (passed: N, failed: N)

### Test Results
| Test File | Result | Duration | Notes |
|---|---|---|---|
| test_auth.py | PASS (5/5) | 1.2s | |
| test_recipe_rules.py | PASS (8/8) | 2.1s | Fixed: assertion update |

### Fixes Applied
1. [{file}:{line}] {description} — KB strategy: {name} (score: {score})

### Knowledge DB Updates
- Recorded: N new error patterns
- Updated: N strategy scores
- New strategies: N

### Regression Results
| Adjacent Area | Tests | Result |
|---|---|---|
| auth_merge | 5 | PASS |
| email_uniqueness | 7 | PASS |
```

---

## Reference Files

- `references/workflow-checklist.md` — Quick 8-step checklist
- `references/approval-scenarios.md` — 11 approval scenarios with examples
- `references/automated-diagnosis.md` — KKB-specific error pattern -> action table
