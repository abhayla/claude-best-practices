---
name: fastapi-run-backend-tests
description: >
  Run backend pytest with smart defaults and short-name resolution.
  Resolves short names like "auth" to test_auth.py. Suggests /fix-loop on failure.
allowed-tools: "Bash Read Write Grep Glob"
argument-hint: "[test_path] [--coverage] [--collect-only] [-x] [--file <name>] [--func <name>]"
version: "1.2.0"
type: workflow
---

# Run Backend Tests (FastAPI + pytest)

Run pytest with smart defaults and short-name resolution.

**Arguments:** $ARGUMENTS

---

## STEP 1: Detect Backend Directory

Locate the project's backend directory by scanning for common indicators:

```bash
# Check common backend directory names
for dir in backend server app api src; do
  if [ -d "$dir" ] && [ -f "$dir/conftest.py" -o -d "$dir/tests" ]; then
    echo "Backend directory: $dir"
    break
  fi
done

# Fallback: check for conftest.py or tests/ at project root
if [ -f "conftest.py" ] || [ -d "tests" ]; then
  echo "Backend directory: . (project root)"
fi
```

Use the detected directory for all subsequent commands. If ambiguous, ask the user.

---

## STEP 2: Resolve Test Path

If a short name is given (e.g., `auth`), resolve it to a full test file path:

```bash
# Search by short name pattern
find {backend_dir}/tests -name "*${NAME}*.py" -type f 2>/dev/null

# Search by function name if --func given
grep -rl "def test_${FUNC}" {backend_dir}/tests/ 2>/dev/null
```

Resolution priority:
1. Exact file path if given → use as-is
2. Short name → find matching `test_*.py` or `*_test.py` files
3. Function name (`--func`) → grep across test files to find containing file
4. No arguments → run all tests in `{backend_dir}/tests/`

---

## STEP 3: Run Tests

```bash
cd {backend_dir} && PYTHONPATH=. pytest {path} -v --tb=short {flags}
```

### Flag Mapping

| Argument | pytest Flag | Purpose |
|----------|-----------|---------|
| `--coverage` | `--cov=app --cov-report=term-missing` | Show coverage with uncovered lines |
| `--collect-only` | `--collect-only -q` | List test names without running |
| `-x` | `-x` | Stop on first failure |
| `--file <name>` | Resolved path | Run specific file |
| `--func <name>` | `-k <name>` | Run tests matching name pattern |

### Common Patterns

```bash
# Run all tests
PYTHONPATH=. pytest tests/ -v --tb=short

# Run with coverage
PYTHONPATH=. pytest tests/ -v --cov=app --cov-report=term-missing

# Run specific test file by short name
PYTHONPATH=. pytest tests/test_auth.py -v --tb=short

# Run specific test function
PYTHONPATH=. pytest tests/test_auth.py::test_login_success -v --tb=short

# Run tests matching a keyword
PYTHONPATH=. pytest tests/ -v -k "auth and not admin"

# List tests without running
PYTHONPATH=. pytest tests/ --collect-only -q
```

---

## STEP 4: Analyze Results

### On Success

```
Backend Tests: PASSED — {N} passed in {duration}s
```

If `--coverage` was used, include coverage summary:
```
Coverage: {X}% overall | {Y}% app/ | {Z}% models/
Uncovered: app/routes/admin.py:45-67, app/services/email.py:23-31
```

### On Failure

```
Backend Tests: FAILED — {N} passed, {M} failed

Failed Tests:
  tests/test_auth.py::test_login_expired_token — AssertionError: 401 != 200
  tests/test_users.py::test_create_duplicate — IntegrityError

Suggested: /fix-loop with retest_command:
  cd {backend_dir} && PYTHONPATH=. pytest {failed_path} -v --tb=short -x
```

Categorize failures using these standard categories:
- `ASSERTION_FAILURE` — expected vs actual mismatch
- `RUNTIME_EXCEPTION` — unhandled exception
- `FIXTURE_MISMATCH` — setup/teardown issue
- `MISSING_IMPORT` — import not found
- `TIMEOUT` — test exceeded time limit

---

## STEP 5: Suggest Next Actions

| Result | Action |
|--------|--------|
| All passed | Report success, suggest broader suite if only subset was run |
| Failures found | Suggest `/fix-loop` with the retest command |
| Coverage below 80% | Highlight uncovered files, suggest `/test-generator` for gap filling |
| Flaky tests detected | Suggest re-running with `--count=3` (pytest-repeat) to confirm |

---

## STEP 6: Structured JSON Output

Write machine-readable results to `test-results/fastapi-run-backend-tests.json`:

```json
{
  "skill": "fastapi-run-backend-tests",
  "result": "PASSED|FAILED",
  "timestamp": "<ISO-8601>",
  "tests_run": "<total_count>",
  "tests_failed": "<failed_count>",
  "failures": [
    {
      "test": "<test_file>::<test_function>",
      "category": "ASSERTION_FAILURE|RUNTIME_EXCEPTION|FIXTURE_MISMATCH|MISSING_IMPORT|TIMEOUT",
      "file": "<test_file_path>:<line>",
      "message": "<error_message>"
    }
  ]
}
```

Create `test-results/` directory if it doesn't exist. This JSON is consumed by downstream stage gates.

```bash
mkdir -p test-results
python3 -c "
import json, datetime
result = {
    'skill': 'fastapi-run-backend-tests',
    'result': '<PASSED_or_FAILED>',
    'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'tests_run': '<N>',
    'tests_failed': '<N>',
    'failures': []
}
with open('test-results/fastapi-run-backend-tests.json', 'w') as f:
    json.dump(result, f, indent=2)
"
```

---

## MUST DO

- Always detect the backend directory before running — never assume `backend/`
- Always use `PYTHONPATH=.` to ensure cross-module imports work
- Always use `--tb=short` for readable output (unless user requests `--tb=long`)
- Always categorize failures in the report
- Always suggest `/fix-loop` with the exact retest command on failure

## MUST NOT DO

- MUST NOT assume the backend directory is named `backend/` — detect it
- MUST NOT run tests without `PYTHONPATH=.` — imports will break
- MUST NOT suppress test output — show failures clearly
- MUST NOT ignore flaky tests — flag them for investigation
