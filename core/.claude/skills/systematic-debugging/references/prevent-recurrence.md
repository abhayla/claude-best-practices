# STEP 8: Prevent Recurrence

### 8.1 Add a Regression Test

Write a test that specifically covers the bug scenario:

```
Regression test:
  Name: test_{descriptive_name_of_bug_scenario}
  Input: {the minimal reproduction input from Step 1}
  Expected: {correct behavior}
  Verifies: {root cause from Step 5 does not recur}
```

The test should:
1. **Fail without the fix** — verify by temporarily reverting your fix and running the test
2. **Pass with the fix** — confirms the test actually covers the bug
3. **Be minimal** — test the specific scenario, not a broad integration
4. **Have a descriptive name** — future developers should understand WHAT bug this prevents

### 8.2 Add Defensive Guards

Based on the root cause, add guards at system boundaries:

| Guard Type | When to Add | Example |
|------------|-------------|---------|
| **Input validation** | Bad data caused the bug | Validate email format before processing |
| **Assertion** | Invariant was violated | `assert profile is not None, "User must have a profile"` |
| **Type check** | Wrong type passed silently | Add type annotation, runtime type check |
| **Error message** | Failure was hard to diagnose | Add context to the exception: what was expected, what was received |
| **Default value** | Missing value caused crash | Provide a sensible default instead of crashing |
| **Boundary check** | Out-of-range value caused bug | Validate array index, check for overflow |

### 8.3 Improve Error Messages

If the original error message was unhelpful (e.g., "NullPointerException" with no context), improve it:

Before:
```
NullPointerException at UserService.java:42
```

After:
```
User profile not found for user_id=12345. The profiles table may need migration.
Run: python manage.py migrate --run-syncdb
See: docs/deployment.md#database-setup
```

Good error messages include:
1. **What happened** — the specific failure
2. **Why it matters** — the operation that could not complete
3. **What to do** — actionable next steps for the developer or operator

### 8.4 Document the Bug

For non-trivial bugs, leave a breadcrumb in the code:

```python
