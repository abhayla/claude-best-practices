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
  - test first
  - write tests before code
  - failing test first
allowed-tools: "Bash Read Write Edit Grep Glob"
argument-hint: "<feature-or-behavior-description>"
version: "1.1.0"
type: workflow
---

# Test-Driven Development (Red-Green-Refactor)

Build the requested feature using strict TDD discipline. Every line of production code
must be justified by a failing test. MUST NOT write production code without a failing test.
MUST NOT skip the green baseline check. For bulk test generation from PRDs/specs before
starting TDD cycles, use `/tdd-failing-test-generator` instead.

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

If no test framework is found, STOP and present framework options appropriate for the
project's language (e.g., pytest for Python, Jest/Vitest for TypeScript, JUnit for Kotlin).
Install the chosen framework before continuing. TDD requires a working test runner.

4. Identify where new tests should live (follow existing test file conventions)
5. Identify where production code should live

---

## STEP 1: RED — Write a Failing Test

Choose the smallest meaningful behavior. Write ONE test using Arrange-Act-Assert with a
descriptive name (`test_{action}_{scenario}_{expected}`). Run the test — it MUST fail.
Verify it fails for the RIGHT reason (missing behavior, not syntax error). If it passes
unexpectedly, STOP and investigate. MUST NOT write any production code during this phase.

**Read:** `references/red-write-a-failing-test.md` for detailed sub-steps (1.1–1.6), failure gate table, and phase rules.

## STEP 2: GREEN — Minimal Implementation

Write the SIMPLEST code that makes the failing test pass — hardcode if possible (e.g.,
`return 3` instead of `return a + b`). The next test will force generalization. Run the
new test, then run ALL existing tests for regression. MUST NOT refactor, rename, or
beautify during this phase.

**Read:** `references/green-minimal-implementation.md` for detailed sub-steps (2.1–2.5), regression handling, and phase rules.

## STEP 3: REFACTOR — Clean Up

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


**Read:** `references/tdd-patterns.md` for detailed tdd patterns reference material.

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
