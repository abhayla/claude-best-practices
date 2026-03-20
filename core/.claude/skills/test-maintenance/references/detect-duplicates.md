# STEP 3: Detect Duplicates

### 3a. Tests asserting the same behavior

1. Extract assertion targets from each test (the function/method under test + input pattern)
2. Group tests by target
3. Flag groups with 2+ tests that have overlapping assertions

Look for:
- Tests with identical or near-identical assertion lines
- Tests calling the same function with the same arguments
- Copy-pasted test bodies with only variable names changed

### 3b. Overlapping parametrize cases

**Python:** Check `@pytest.mark.parametrize` for redundant test cases:
- Duplicate rows in the parameter list
- Cases that test the same equivalence class (e.g., testing both `1` and `2` for "positive integer")

**JavaScript:** Check `test.each` / `describe.each` for the same issues.

### 3c. Redundant setup

Find `setUp` / `beforeEach` blocks that create identical state across multiple test
classes/describes. Candidates for extraction into shared fixtures.

---

