# Common Debugging Patterns

### Pattern 1: Binary Search with Git Bisect

When you know "it used to work" but not which commit broke it:

```bash
git bisect start
git bisect bad HEAD                          # Current version is broken
git bisect good v1.2.0                       # This version worked
git bisect run ./run_reproduction_test.sh    # Automate the search
```

Git bisect performs a binary search through commits, finding the exact commit that introduced the bug in O(log n) steps.

**When to use:** Regressions where you have a known good version.
**When NOT to use:** Bugs that have always existed, or when the reproduction requires external state (database, API).

### Pattern 2: Delta Debugging

When a large input causes the failure but you don't know which part:

1. Split input in half
2. Test each half separately
3. The half that fails contains the trigger
4. Recurse on the failing half
5. Continue until you find the minimal failing input

**When to use:** Large configuration files, complex data inputs, long sequences of operations.
**Example:** A 500-line config file causes a crash. Delta debugging finds that line 347 (`timeout: -1`) is the trigger.

### Pattern 3: Rubber Duck Debugging

When you are stuck and cannot form new hypotheses:

1. Explain the problem out loud (or in writing) as if teaching someone unfamiliar with the code
2. Explain each step: what the code SHOULD do, what it ACTUALLY does, and what you have already checked
3. The act of articulating forces you to identify assumptions you haven't examined

**When to use:** After exhausting your initial hypotheses, when the bug seems "impossible."
**Technique in practice:** Write a detailed description of the bug in a comment to the user. Often, the act of writing the description reveals the cause.

### Pattern 4: State Inspection

When the bug is about incorrect state rather than incorrect logic:

1. Identify the key state variables involved
2. Log their values at each state transition
3. Compare actual state transitions against expected
4. Find the first point where actual diverges from expected

**When to use:** Stateful systems, UI bugs, data pipeline issues, caching problems.

### Pattern 5: Differential Debugging

When the same code works in one context but not another:

1. Identify a working case and a broken case
2. List ALL differences between them (input, environment, config, timing, data)
3. Eliminate differences one by one until you find the one that matters
4. The critical difference is your root cause

**When to use:** "Works on my machine" bugs, environment-specific failures, user-specific bugs.

---

