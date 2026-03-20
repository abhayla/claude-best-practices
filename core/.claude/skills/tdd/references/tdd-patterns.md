# TDD PATTERNS

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

