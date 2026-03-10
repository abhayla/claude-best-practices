---
name: run-backend-tests
description: >
  Run backend pytest with smart defaults and short-name resolution.
  Use when running backend tests, checking test counts, or verifying backend changes.
  Resolves short names like "auth" to test_auth.py. Suggests /fix-loop on failure.
allowed-tools: "Bash Read Grep Glob Skill"
argument-hint: "[test_path] [--coverage] [--collect-only] [-x] [--file <shortname>] [--func <name>]"
---

# Run Backend Tests

Run pytest with smart defaults, short-name resolution, and failure follow-up.

**Arguments:** $ARGUMENTS

---

## Input Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `test_path` | positional | (all) | Direct path like `tests/test_auth.py` |
| `--file <name>` | string | — | Short name to resolve: `auth` -> `tests/test_auth.py` |
| `--func <name>` | string | — | Specific test function name |
| `--coverage` | flag | false | Add `--cov=app` for coverage report |
| `--collect-only` | flag | false | Only collect tests, don't run |
| `-x` | flag | false | Stop on first failure |

**Common patterns:**

| Command | What it does |
|---------|-------------|
| `/run-backend-tests` | Full suite |
| `/run-backend-tests auth` | Run `tests/test_auth.py` |
| `/run-backend-tests --file household --func test_create` | Single test function |
| `/run-backend-tests --coverage` | Full suite with coverage |
| `/run-backend-tests --collect-only` | Count tests only |

---

## STEP 1: Resolve Test Path

If `--file <shortname>` or a bare word is given, resolve it:

```bash
cd backend && ls tests/*${SHORTNAME}*.py tests/**/*${SHORTNAME}*.py 2>/dev/null
```

If multiple matches, pick the most specific match. If no match, report error and list available test files.

If `--func` is also given, append `::${FUNC_NAME}` to the resolved path.

If no path/file given, run the full suite.

---

## STEP 2: Pre-flight Check

```bash
cd backend && python -c "import sys; venv = hasattr(sys, 'real_prefix') or sys.base_prefix != sys.prefix; print('venv: active' if venv else 'WARNING: venv not active — activate with: source venv/bin/activate')"
```

---

## STEP 3: Run Tests

Build and execute the pytest command:

```bash
cd backend && PYTHONPATH=. pytest {resolved_path} -v --tb=short {extra_flags}
```

**Flags:**
- Add `--cov=app` if `--coverage`
- Add `--collect-only -q` if `--collect-only`
- Add `-x` if `-x`
- Add `--tb=short` always (unless `--collect-only`)

**Timeouts:**
- Full suite: 300 seconds
- Single file: 120 seconds
- Single function: 60 seconds

---

## STEP 4: Parse Results

Extract from pytest summary line:
- Total tests run
- Passed / Failed / Error / Skipped counts
- Duration

---

## STEP 5: Report

**On success:**
```
Backend Tests: PASSED
  {N} passed, {N} skipped in {duration}s
  Target: {resolved_path or "full suite"}
```

**On failure:**
```
Backend Tests: FAILED
  {N} passed, {N} failed, {N} errors in {duration}s
  Target: {resolved_path}

  Failed tests:
    - test_name_1: {brief error}
    - test_name_2: {brief error}

  Suggested: /fix-loop with retest_command:
    cd backend && PYTHONPATH=. pytest {resolved_path} -v --tb=short -x
```

If tests fail and the failure looks fixable, suggest invoking `/fix-loop` with the appropriate retest command pre-built.

---

## CRITICAL NOTES

- Always run from `backend/` directory
- Always set `PYTHONPATH=.`
- Use `--tb=short` for readable failure output (not `--tb=long`)
- If stale `.pyc` errors appear, suggest `/clean-pyc` first
