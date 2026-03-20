# STEP 2: GREEN — Minimal Implementation

### 2.1 Write the Minimum Code to Pass

Write the SIMPLEST, most MINIMAL code that makes the failing test turn green.

This is the hardest discipline in TDD. Your instinct will be to write the "real"
solution. Resist it. Write the dumbest thing that works.

**Minimality examples:**

| Test Expects | Minimal Implementation | NOT This |
|-------------|----------------------|----------|
| `add(1, 2)` returns `3` | `return 3` (hardcoded!) | `return a + b` (too general) |
| `is_even(4)` returns `True` | `return True` | `return n % 2 == 0` (too general) |
| `greet("Alice")` returns `"Hello, Alice!"` | `return "Hello, Alice!"` | `return f"Hello, {name}!"` (too general) |
| List of users is empty by default | `return []` | Full user management system |

Why hardcode? Because the NEXT test will force you to generalize. If `add(1, 2)` returns
a hardcoded `3`, then `add(3, 4)` returning `7` forces you to write `return a + b`.
This is the TDD pattern called "Fake It Till You Make It" — and it ensures every line
of general code is justified by a test that demands it.

#### When to Skip Fake-It

Use the "Obvious Implementation" shortcut ONLY when:

- The implementation is trivially simple (one expression)
- You are 100% confident it is correct
- It would be faster to write the real code than the fake

Example: If the test expects `len([1,2,3])` to return `3`, just call `len()`. Do not
fake this. But when in doubt, fake it — you can always generalize in the next cycle.

### 2.2 Run the New Test

```bash
{test_command_for_new_test}
```

The new test MUST pass. If it does not:

1. Re-read the test to confirm what it expects
2. Re-read your implementation to see what it actually does
3. Fix the implementation (keep it minimal)
4. Re-run the test
5. If stuck after 3 attempts, re-examine whether the test itself is correct

### 2.3 Run ALL Existing Tests — Regression Check

```bash
{full_test_suite_command}
```

This is mandatory. Your new code must not break any existing tests.

| Outcome | Action |
|---------|--------|
| All tests pass | Proceed to REFACTOR phase |
| New test passes, existing test fails | You have a regression. Fix it before proceeding. |
| Multiple tests fail | Your change has a broader impact than expected. Reconsider your approach. |

#### Handling Regressions

If an existing test breaks:

1. Read the failing test to understand what it expects
2. Determine if your new code conflicts with existing behavior
3. Fix the regression while keeping the new test green
4. If you cannot satisfy both the old and new test, ask the user — there may be a
   requirements conflict

### 2.4 Green Phase Output

```
GREEN PHASE COMPLETE
  Test:         {test_name} — PASSING
  Changed:      {files_modified}
  Approach:     {what you wrote — e.g., "hardcoded return value" or "simple conditional"}
  All tests:    {X passed, 0 failed}
  Regressions:  None
```

### 2.5 Green Phase Rules

During the GREEN phase, you MUST NOT:

- Refactor anything (production or test code)
- Rename variables for clarity
- Extract methods or classes
- Add code for future tests that have not been written yet
- Add error handling beyond what the current test requires
- Improve performance
- Add comments explaining the code

You MAY only:

- Add the minimum production code to make the failing test pass
- Fix regressions in existing tests caused by your new code

Violation check: "Is this change required to make the test pass, or am I making the code
'better'?" If making it better — stop. That belongs in the REFACTOR phase.

---

