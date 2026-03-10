# Approval Scenarios

11 scenarios requiring user approval before applying fixes during auto-verify.

---

## Auto-Approved (No Confirmation Needed)

These fix types are applied automatically:

| Fix Type | Condition | Example |
|---|---|---|
| Simple assertion update | Expected value changed due to refactoring | `assert count == 5` → `assert count == 6` |
| Missing import | New module added, test needs import | `from app.services.new_service import ...` |
| Path / PYTHONPATH fix | Incorrect working directory or path | Add `PYTHONPATH=.` prefix |
| KB strategy (high score) | Score >= 0.3 AND iteration <= 2 | Apply known upsert fix |

---

## Approval Required (AskUserQuestion)

### 1. Protected Files
**Files:** `.env`, `conftest.py`, `build.gradle.kts`, `alembic/versions/`, `settings.json`
**Why:** Changes affect all tests or security configuration.
**Format:** Show exact diff, explain why change is needed.

### 2. Shared Utilities
**Files:** Test fixtures, base classes (`BaseE2ETest`), DI modules (`AppModule`)
**Why:** Changes propagate to many tests/features.
**Format:** List all downstream consumers affected.

### 3. Database Schema
**Files:** Alembic migrations, Room `@Database` annotation, entity classes
**Why:** Schema changes are hard to reverse and affect data integrity.
**Format:** Show migration SQL or Room schema change.

### 4. Multi-Feature Impact
**When:** Fix touches files in >1 module (e.g., backend + android, or data + domain)
**Why:** Cross-module changes need holistic review.
**Format:** List all modules affected, show dependency chain.

### 5. Assertion Changes
**When:** Modifying test expectations to match new behavior
**Why:** May mask actual bugs — the test might be RIGHT and the code WRONG.
**Format:** Show old vs new expected value, explain why new value is correct.

### 6. Mock/Dummy Data
**When:** Replacing real behavior with fakes to make tests pass
**Why:** May hide integration issues.
**Format:** Show what's being mocked, explain why real behavior can't be used.

### 7. Disabling Tests
**When:** Adding @Ignore, @Disabled, skip, or commenting out test methods
**Why:** Almost always wrong — prefer fixing the underlying issue.
**Format:** Explain why the test can't be fixed, propose timeline for re-enabling.

### 8. Workarounds
**When:** Applying a patch instead of a proper fix (e.g., try-catch swallowing errors)
**Why:** Technical debt — may hide real issues.
**Format:** Show workaround, explain proper fix and why it can't be done now.

### 9. Assumptions
**When:** Guessing intended behavior (ambiguous test, unclear specification)
**Why:** Wrong assumption → wrong fix → harder debugging later.
**Format:** State assumption explicitly, offer 2-3 alternatives.

### 10. Iteration Threshold
**When:** After 3 fix iterations for the same error
**Why:** Prevent thrashing — repeated failures suggest misdiagnosis.
**Format:** Summarize all 3 attempts, ask user for direction.

### 11. Max Attempts (Safety Valve)
**When:** After 5 total attempts across all errors
**Why:** Hard stop to prevent unbounded iteration.
**Format:** Full summary of all attempts, outcomes, and remaining failures.
