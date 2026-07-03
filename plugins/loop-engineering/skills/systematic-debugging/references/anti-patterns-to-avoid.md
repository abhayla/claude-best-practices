# Anti-Patterns to Avoid

### Anti-Pattern 1: Random Code Changes

**What it looks like:** Changing code without understanding why, hoping it fixes the problem.

**Why it fails:**
- Even if the bug disappears, you don't know if you fixed it or masked it
- You may introduce new bugs
- You learn nothing for next time

**Instead:** Follow Steps 1-5 before touching any code. Understand the root cause FIRST.

### Anti-Pattern 2: Fixing Symptoms Instead of Causes

**What it looks like:** Adding a null check instead of preventing the null from occurring.

**Why it fails:**
- The null check fixes this one crash but the underlying data is still wrong
- Other code paths will hit the same bad data
- The bug report changes from "crash" to "silently wrong behavior" — harder to detect

**Instead:** Trace the causal chain (Step 5) and fix at the root cause level.

### Anti-Pattern 3: Untested Fixes

**What it looks like:** Making a code change, eyeballing it, and declaring it fixed without running the reproduction.

**Why it fails:**
- You may have fixed a different code path than the one that is actually failing
- The fix may only work in your dev environment
- Without a regression test, the bug will return

**Instead:** Always run the original reproduction (Step 7.1) and add a regression test (Step 8.1).

### Anti-Pattern 4: Debugging by Rewriting

**What it looks like:** "I don't understand this code, so I'll rewrite it from scratch."

**Why it fails:**
- The original code may handle edge cases you don't know about
- Rewriting introduces new bugs while potentially fixing the old one
- You still don't understand the root cause

**Instead:** Understand the existing code first. Fix the specific issue. Only refactor after the bug is fixed and tests pass.

### Anti-Pattern 5: Ignoring Intermittent Failures

**What it looks like:** "It only fails sometimes, so it's probably a flaky test."

**Why it fails:**
- Intermittent failures are real bugs — usually race conditions, timing issues, or resource leaks
- They become more frequent under load
- They are the hardest bugs to fix later because the reproduction conditions are complex

**Instead:** Take intermittent failures seriously. Add logging with timestamps, check for shared mutable state, look for race conditions.

### Anti-Pattern 6: "It Works on My Machine"

**What it looks like:** Dismissing a bug because it doesn't reproduce locally.

**Why it fails:**
- The bug is real for someone
- Environment differences are a common root cause category
- Dismissing it means it stays broken

**Instead:** Use differential debugging (Pattern 5) to find environment differences.

---

