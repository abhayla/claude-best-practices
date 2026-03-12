---
name: tdd
description: >
  Execute strict Test-Driven Development using the red-green-refactor cycle.
  Write a failing test first, implement the minimum code to pass it, then refactor
  with full test coverage as a safety net. Use for building new logic, algorithms,
  business rules, or any code where correctness matters.
triggers:
  - tdd
  - test-driven
  - red-green-refactor
allowed-tools: "Bash Read Write Edit Grep Glob Skill"
argument-hint: "<feature-or-behavior-description>"
---

# Test-Driven Development (Red-Green-Refactor)

Build the requested feature using strict TDD discipline. Every line of production code
must be justified by a failing test.

**Request:** $ARGUMENTS

---

## Overview

TDD is a three-phase cycle repeated in small increments:

```
  RED ──────► GREEN ──────► REFACTOR
  (write a     (make it      (clean it
   failing      pass with     up without
   test)        minimal       changing
                code)         behavior)
       ◄────────────────────────┘
              start next cycle
```

Each cycle adds ONE small behavior. A feature is built from many small cycles,
not one large implementation.

---

## BEFORE STARTING: Environment Check

1. Identify the project's test framework and test runner command
2. Run the existing test suite to establish a green baseline
3. If any tests are already failing, STOP and report to the user — TDD requires a green baseline

```bash
# Record the test command and current state
{test_runner_command}
```

If the baseline is not green, do NOT proceed. TDD builds on a foundation of passing tests.
Ask the user whether to fix existing failures first or proceed with a known-broken baseline
(not recommended).

4. Identify where new tests should live (follow existing test file conventions)
5. Identify where production code should live

---

## PHASE 1: RED — Write a Failing Test

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

## PHASE 2: GREEN — Minimal Implementation

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

## PHASE 3: REFACTOR — Clean Up

### 3.1 Pre-Refactor Safety Check

Before changing anything, confirm all tests are green:

```bash
{full_test_suite_command}
```

If any test is failing, do NOT refactor. Fix the failure first (go back to GREEN phase).

### 3.2 Identify Refactoring Opportunities

Look for these code smells in both production and test code:

| Smell | Refactoring | Example |
|-------|------------|---------|
| **Duplication** | Extract method/function | Same 3 lines appear in two places |
| **Hardcoded values** | Replace with computation | `return 3` becomes `return a + b` (driven by multiple tests) |
| **Long function** | Extract smaller functions | A function doing 5 things becomes 5 functions |
| **Poor naming** | Rename variable/function | `x` becomes `total_price` |
| **Magic numbers** | Extract constant | `0.08` becomes `SALES_TAX_RATE` |
| **Deep nesting** | Early return / guard clause | 4 levels of `if` become flat guards |
| **Test duplication** | Extract test fixture/helper | Same setup in 5 tests becomes a fixture |
| **Dead code** | Remove it | Unused imports, unreachable branches |

### 3.3 Refactor in Small Steps

Make ONE refactoring change at a time. After EACH change:

```bash
{full_test_suite_command}
```

| Outcome | Action |
|---------|--------|
| All tests pass | Continue refactoring or proceed to next cycle |
| Any test fails | UNDO the last change immediately, try a different approach |

This is non-negotiable. Refactoring must never break tests. If it does, the refactoring
was incorrect — not the tests.

#### How to Undo

```bash
# Undo the last change if tests fail during refactoring
git checkout -- {file_that_was_changed}
```

Then try a different refactoring approach, or skip that refactoring for now.

### 3.4 Common Refactoring Sequences

#### Generalizing from Hardcoded Values (Triangulation)

After faking it in GREEN, use refactoring to generalize:

```
Cycle 1 GREEN: return 3                    (hardcoded for add(1,2))
Cycle 2 GREEN: if a==1: return 3; return 7 (hardcoded for add(1,2) and add(3,4))
Cycle 2 REFACTOR: return a + b             (generalized — both tests force this)
```

The key insight: you need at least TWO tests before generalizing. One test can always
be satisfied by a constant. Two tests with different expected outputs force real logic.

#### Extracting Methods

When a function grows beyond ~10 lines across multiple cycles:

1. Identify a coherent block of code (3-5 lines doing one thing)
2. Extract to a new function with a descriptive name
3. Run tests — must still pass
4. Repeat for other blocks

#### Removing Duplication Between Tests

When multiple tests share setup code:

1. Extract shared setup to a fixture or helper function
2. Run tests — must still pass
3. Verify each test is still readable (the setup should have a clear name)

### 3.5 Refactor Phase Output

```
REFACTOR PHASE COMPLETE
  Refactorings: {list of changes made}
  All tests:    {X passed, 0 failed}
  Code quality: {brief assessment — cleaner naming, less duplication, etc.}
```

### 3.6 Refactor Phase Rules

During the REFACTOR phase, you MUST NOT:

- Add new functionality or behavior
- Write new tests for untested behavior
- Change what the code does (only HOW it does it)
- Add new features "while you're in there"
- Change test assertions (refactor test structure, not expectations)

You MAY only:

- Restructure production code (extract, rename, simplify)
- Restructure test code (extract fixtures, rename, reduce duplication)
- Remove dead code
- Improve naming and readability
- Add comments where logic is non-obvious

Violation check: "If I removed all my refactoring changes, would the tests still pass
with the same assertions?" If yes, the refactoring is safe. If no, you changed behavior
— that belongs in a new RED phase.

---

## CYCLE MANAGEMENT

### Tracking Progress

After each complete cycle (RED + GREEN + REFACTOR), record:

```
CYCLE {N} COMPLETE
  Behavior added: {one-sentence description}
  Test:           {test_name}
  Files changed:  {list}
  Cumulative:     {total_tests} tests, {total_cycles} cycles
```

### Deciding the Next Cycle

After each cycle, choose the next behavior to add:

| Strategy | When to Use |
|----------|-------------|
| **Next simplest case** | Default — build complexity gradually |
| **Triangulation** | When current implementation is too hardcoded |
| **Edge case** | After core behavior is solid |
| **Error case** | After happy paths are covered |
| **Integration** | After unit-level behavior is complete |

### Progression Pattern

Follow this general order for building a feature:

```
1. Degenerate case     (empty input, zero, null)
2. Single simple case  (one item, basic input)
3. Multiple cases      (list of items, varied inputs)
4. Edge cases          (boundary values, special characters)
5. Error cases         (invalid input, missing data)
6. Performance cases   (large input — only if relevant)
```

### When to Stop

The feature is complete when:

- All acceptance criteria from the request are covered by tests
- Edge cases identified during development have tests
- Error handling is in place for expected failure modes
- The code is clean (no pending refactoring smells)
- All tests pass

Report completion with a summary:

```
TDD COMPLETE
  Feature:        {description}
  Total cycles:   {N}
  Tests written:  {count}
  Files created:  {list of new files}
  Files modified: {list of modified files}
  All tests:      {X passed, 0 failed}
```

---

## TDD PATTERNS

### Pattern 1: Fake It Till You Make It

Start with constants, evolve to variables, then to computations.

```
Step 1: return 42           (constant — satisfies first test)
Step 2: return n * 42       (variable — satisfies first two tests)
Step 3: return n * (n + 1)  (computation — satisfies all tests)
```

Use when: you are not sure what the general solution looks like. Let the tests guide you.

### Pattern 2: Triangulation

Add more test cases to force generalization of hardcoded solutions.

```
Test 1: assert add(1, 2) == 3   → impl: return 3
Test 2: assert add(3, 4) == 7   → impl: return a + b (forced to generalize)
```

Use when: a single test can be trivially satisfied. Add another test with different
values to force the real implementation.

### Pattern 3: Obvious Implementation

When the solution is trivially clear, skip fake-it and write the real code directly.

```
Test: assert len([1, 2, 3]) == 3
Impl: return len(items)          (no need to fake this)
```

Use when: the implementation is a single expression and you are confident it is correct.
If the test fails, revert to Fake It — your confidence was misplaced.

### Pattern 4: One to Many

Start with a single item, then generalize to collections.

```
Cycle 1: Process a single order  → works for one item
Cycle 2: Process a list of orders → generalize to iteration
Cycle 3: Process empty list       → handle degenerate case
```

Use when: building functionality that operates on collections. Starting with a single
item keeps the first cycles simple.

### Pattern 5: Transformation Priority Premise

Prefer simpler transformations before complex ones:

```
Priority (simple → complex):
  1. constant → constant          (return hardcoded value)
  2. constant → scalar            (return input unchanged)
  3. scalar → scalar              (transform input)
  4. collection → element         (select from collection)
  5. element → collection         (gather into collection)
  6. collection → collection      (transform collection)
  7. collection → different type  (reduce/aggregate)
```

Each cycle should move one step up this priority list.

### Pattern 6: Test Isolation with Stubs

When the code under test depends on external systems:

```
Cycle 1: Test with a stub/mock for the dependency
Cycle 2: Test the dependency integration separately
```

Keep unit tests fast and isolated. Test integration boundaries in separate integration tests.

---

## WHEN TO USE /tdd VS /implement

| Situation | Use | Why |
|-----------|-----|-----|
| New algorithm or business logic | `/tdd` | Correctness is critical, TDD catches logic errors |
| Data transformation pipeline | `/tdd` | Each transformation step needs verified correctness |
| Complex validation rules | `/tdd` | Edge cases are numerous and easy to miss |
| State machine or workflow | `/tdd` | State transitions need exhaustive testing |
| Mathematical computations | `/tdd` | Precision matters, regression risk is high |
| UI layout or styling | `/implement` | Visual output is hard to test with unit tests |
| Configuration changes | `/implement` | No logic to drive with tests |
| Third-party API integration | `/implement` | External behavior cannot be driven by your tests |
| Database migrations | `/implement` | Schema changes are not unit-testable |
| Broad feature with mixed concerns | Both | `/tdd` for core logic, `/implement` for integration |

### Combining /tdd and /implement

For features that have both core logic and integration concerns:

1. Use `/tdd` to build the core logic (algorithms, business rules, transformations)
2. Use `/implement` to wire the tested logic into the broader system (routes, UI, config)

This gives you TDD's correctness guarantees where they matter most, without forcing
test-first discipline on parts of the system where it adds friction without value.

---

## HANDLING COMMON SITUATIONS

### Situation: Need to Change Existing Code

When TDD requires modifying existing (already tested) code:

1. Run existing tests — confirm they pass
2. Write the new failing test (RED)
3. Modify the existing code minimally (GREEN)
4. Run ALL tests (existing + new) — all must pass
5. Refactor if needed (REFACTOR)

Never skip step 1. You need to know the baseline.

### Situation: Test is Hard to Write

If you are struggling to write a test, it usually means one of:

| Problem | Solution |
|---------|----------|
| Don't know what to test | Clarify requirements with the user |
| Too many dependencies | Extract the logic into a pure function that can be tested in isolation |
| Need a database/network | Use stubs/mocks for unit tests, test real integration separately |
| Non-deterministic behavior | Inject a clock/random seed, or test the range of valid outputs |
| Side effects | Separate pure logic from side effects, test pure logic first |

### Situation: Test Suite is Slow

If the full test suite takes too long to run every cycle:

1. Run only the targeted test file during RED and GREEN phases
2. Run the full suite during REFACTOR and at the end of each cycle
3. Mark slow tests (integration, E2E) and run them less frequently
4. Never skip the full suite before reporting completion

### Situation: Discovered a Bug in Existing Code

If you discover a bug while doing TDD on a new feature:

1. Do NOT fix it immediately — you are in the middle of a cycle
2. Write down the bug (file, line, what is wrong)
3. Complete the current TDD cycle
4. Start a NEW TDD cycle specifically for the bug (write a test that exposes it, then fix it)

This keeps your cycles clean and each fix backed by a test.

### Situation: Requirements Change Mid-Feature

If the user changes requirements during TDD:

1. Complete the current cycle (do not abandon a half-finished cycle)
2. Assess which existing tests are now invalid
3. Modify or delete invalidated tests (they test old requirements)
4. Start a new RED phase for the changed requirement
5. Keep tests for behaviors that are still valid

---

## MUST DO

- Always run the test and VERIFY it fails before writing any production code
- Always check that the test fails for the RIGHT reason (missing behavior, not syntax error)
- Always write the MINIMUM code to pass the test — resist writing the "real" solution early
- Always run ALL tests after implementing, not just the new one
- Always run ALL tests after EACH refactoring change
- Always undo refactoring immediately if any test fails
- Always track cycle count and cumulative progress
- Always start with the simplest test case and build complexity gradually
- Always keep phases separate: RED = test only, GREEN = minimal impl only, REFACTOR = restructure only
- Always establish a green baseline before starting TDD
- Always complete a full cycle before switching tasks or addressing discovered bugs

## MUST NOT DO

- MUST NOT write production code during the RED phase — only test code
- MUST NOT refactor or beautify during the GREEN phase — only make the test pass
- MUST NOT add new behavior during the REFACTOR phase — only restructure existing code
- MUST NOT proceed to GREEN if the test passes unexpectedly — investigate why it passes
- MUST NOT proceed to GREEN if the test fails for the wrong reason — fix the test first
- MUST NOT skip the regression check (running all tests) after GREEN phase
- MUST NOT skip running tests after each refactoring change
- MUST NOT write tests for multiple behaviors at once — one test per cycle
- MUST NOT generalize from a single test case — wait for triangulation (two+ tests)
- MUST NOT continue refactoring if a test fails — undo and try a different approach
- MUST NOT fix discovered bugs inline — complete the current cycle, then start a new one
- MUST NOT skip the green baseline check at the start — TDD requires all tests passing first
