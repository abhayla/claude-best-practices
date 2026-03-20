# STEP 1: RED — Write a Failing Test

### 1.1 Choose the Next Behavior

Select the smallest meaningful behavior to add:

| Cycle Stage | What to Test | Example |
|-------------|-------------|---------|
| First cycle | Simplest happy path, single input | `add(1, 2)` returns `3` |
| Early cycles | Core behavior variations | `add(0, 0)` returns `0` |
| Middle cycles | Edge cases, boundary conditions | `add(-1, 1)` returns `0` |
| Late cycles | Error handling, invalid inputs | `add("a", 1)` raises `TypeError` |

Start simple. Resist the urge to write the "interesting" test first. The simplest test
drives the simplest implementation, which is the foundation for everything that follows.

### 1.2 Write the Test

Write ONE test that defines the expected behavior. The test must:

- Test exactly ONE behavior (one logical assertion)
- Have a descriptive name that states the scenario and expected outcome
- Follow Arrange-Act-Assert structure
- Use the project's existing test conventions and patterns

```
Test structure:
  ARRANGE: Set up inputs, dependencies, and expected state
  ACT:     Call the function/method under test
  ASSERT:  Verify the output matches expectations
```

Test naming convention — the name should read like a specification:

| Pattern | Example |
|---------|---------|
| `test_{action}_{scenario}_{expected}` | `test_add_two_positive_numbers_returns_sum` |
| `test_{scenario}_should_{expected}` | `test_empty_cart_should_have_zero_total` |
| `test_{method}_{condition}` | `test_divide_by_zero_raises_error` |

### 1.3 Run the Test — Verify It FAILS

```bash
{test_command_for_new_test}
```

This is a mandatory gate. The test MUST fail before you proceed.

### 1.4 Red Confirmation Gate

Analyze the test failure. There are three possible outcomes:

| Outcome | Meaning | Action |
|---------|---------|--------|
| **Test fails with expected reason** | The behavior does not exist yet | Proceed to GREEN phase |
| **Test fails with unexpected reason** | Syntax error, import error, wrong setup | Fix the TEST (not production code), re-run |
| **Test PASSES unexpectedly** | DANGER — test is not testing what you think | STOP and investigate (see below) |

#### If the Test Passes Unexpectedly

This is a critical signal. Do NOT proceed. Common causes:

1. **Testing existing behavior** — The feature already exists. Check if you are duplicating
   an existing test. If the behavior is already implemented, this cycle is unnecessary.
2. **Wrong assertion** — The assertion is trivially true (e.g., `assert True`, comparing
   a variable to itself, or asserting on a default value).
3. **Test hitting wrong code path** — The test is not exercising the code you think it is.
   Add a deliberate failure in the production code to verify the test reaches it.
4. **Mock/stub returning expected value** — A mock is providing the answer instead of
   real code. Check your test doubles.

Resolution: Fix the test so it fails for the right reason, THEN proceed.

### 1.5 Red Phase Output

After confirming a proper failure, record:

```
RED PHASE COMPLETE
  Test:    {test_name}
  File:    {test_file_path}
  Failure: {failure_message}
  Reason:  Fails because {the behavior does not exist / returns wrong value / raises wrong error}
  Status:  Confirmed failing for the RIGHT reason
```

### 1.6 Red Phase Rules

During the RED phase, you MUST NOT:

- Write any production code
- Modify any existing production files
- Add helper functions to production modules
- Create production classes or functions

You MAY only:

- Create or modify test files
- Add test helper functions or fixtures (in test files/directories only)
- Add imports in test files

Violation check: "Am I writing code that will be deployed, or code that will only run
during testing?" If deployed — stop. That belongs in the GREEN phase.

---

