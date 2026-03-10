---
name: fastapi-run-backend-tests
description: >
  Run backend pytest with smart defaults and short-name resolution.
  Resolves short names like "auth" to test_auth.py. Suggests /fix-loop on failure.
allowed-tools: "Bash Read Grep Glob Skill"
argument-hint: "[test_path] [--coverage] [--collect-only] [-x] [--file <name>] [--func <name>]"
---

# Run Backend Tests (FastAPI + pytest)

Run pytest with smart defaults and short-name resolution.

**Arguments:** $ARGUMENTS

---

## STEP 1: Resolve Test Path

If a short name is given, resolve it:
```bash
cd backend && ls tests/*${NAME}*.py 2>/dev/null
```

## STEP 2: Run Tests

```bash
cd backend && PYTHONPATH=. pytest {path} -v --tb=short {flags}
```

Flags:
- `--cov=app` if `--coverage`
- `--collect-only -q` if `--collect-only`
- `-x` if `-x`

## STEP 3: Report

**On success:**
```
Backend Tests: PASSED — {N} passed in {duration}s
```

**On failure:**
```
Backend Tests: FAILED — {N} passed, {M} failed

Suggested: /fix-loop with retest_command:
  cd backend && PYTHONPATH=. pytest {path} -v --tb=short -x
```

## Notes

- Always run from `backend/` with `PYTHONPATH=.`
- Use `--tb=short` for readable output
