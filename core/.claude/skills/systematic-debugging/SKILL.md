---
name: systematic-debugging
description: >
  Debug failures methodically using a structured diagnosis workflow: reproduce,
  isolate, hypothesize, gather evidence, find root cause, apply targeted fix,
  verify, and prevent recurrence. Use when facing bugs, test failures, or
  unexpected behavior instead of making random code changes.
triggers:
  - debug
  - systematic-debug
  - diagnose bug
  - root cause analysis
  - why is this failing
allowed-tools: "Bash Read Write Edit Grep Glob Skill"
argument-hint: "<bug-description, error message, or failing test command>"
version: "1.0.0"
type: workflow
---

# Systematic Debugging

Debug the reported issue using a structured, evidence-driven workflow. Never guess — diagnose.

**Issue:** $ARGUMENTS

---

## STEP 0: Search Past Learnings

Before starting diagnosis from scratch, check if this error has been seen before.

### 0.1 Search the Learnings Database

```bash
# Check if learnings database exists
if [ -f .claude/learnings.json ]; then
  echo "Learnings database found. Searching for matching errors..."
fi
```

Search `.claude/learnings.json` (if it exists) for matching patterns:
1. **Error message match** — Search for key phrases from the error message
2. **File path match** — Check if the failing file has previous learnings
3. **Tag match** — Match error category (null-handling, async, import, etc.)

### 0.2 If Match Found

```
PAST LEARNING FOUND:
  Learning ID: L042
  Previous error: <similar error message>
  Previous fix: <what fixed it last time>
  Lesson: <what to do differently>
  Seen: <reuse_count> times before

Suggested action: Try the previous fix first. If it doesn't apply, proceed to Step 1.
```

Apply the known fix. If it works, increment `reuse_count` in the learnings database and skip to Step 7 (Verify). If it doesn't apply to this case, proceed to Step 1.

### 0.3 If No Match Found

Proceed to Step 1 (Reproduce the Failure). After resolving the issue, Step 8 will capture it as a new learning.

---

## STEP 1: Reproduce the Failure

Before touching any code, establish a reliable reproduction case.


**Read:** `references/reproduce-the-failure.md` for detailed step 1: reproduce the failure reference material.

# Record the exact reproduction command
{reproduction_command}
```

Save the reproduction command — you will run it repeatedly throughout this process.

### 1.3 Handle Non-Reproducible Failures

If the failure does not reproduce:

| Situation | Action |
|-----------|--------|
| **Works locally but fails in CI** | Check environment differences: OS, dependency versions, env vars, file permissions, timezone |
| **Intermittent failure** | Run reproduction 10+ times, check for race conditions, resource contention, or timing dependencies |
| **Only in production** | Check for data-dependent bugs, missing env vars, network issues, or config differences |
| **Cannot reproduce at all** | Ask user for exact steps, environment details, and full error output. Do NOT proceed without reproduction. |

If you cannot reproduce after reasonable effort, report back to the user with what you tried. Do NOT guess at fixes for bugs you cannot reproduce.

### 1.4 Classify the Failure Type

Identify the failure category to guide your investigation:

| Type | Signals | Investigation Strategy |
|------|---------|----------------------|
| **Crash / Exception** | Stack trace, exit code != 0 | Read stack trace bottom-up, focus on the frame in project code |
| **Wrong output** | Test assertion failure, incorrect data | Compare expected vs actual, trace data transformation pipeline |
| **Performance** | Timeout, slow response | Profile, check algorithmic complexity, look for N+1 queries |
| **Race condition** | Intermittent, timing-dependent | Add logging with timestamps, check shared mutable state |
| **Resource leak** | Gradual degradation, OOM | Check for unclosed handles, growing collections, missing cleanup |
| **Configuration** | Works in one env, fails in another | Diff configurations, check env vars, file paths |
| **Regression** | "This used to work" | Use `git bisect` to find the breaking commit |

---

## STEP 2: Isolate the Failure

Narrow down from "something is broken" to "this specific thing is broken."

### 2.1 Read the Error Trace

For failures with stack traces, read them systematically:

1. **Start at the bottom** — the final error message tells you WHAT went wrong
2. **Scan upward for project code** — skip framework/library frames, find the first frame in YOUR code
3. **Identify the failing line** — read that file and understand the context
4. **Check the call chain** — trace backward to understand HOW you got there

```bash
# Read the file at the error location
# Focus on the function containing the error line
```

Common stack trace patterns:

| Pattern | Meaning |
|---------|---------|
| `AttributeError: 'NoneType'` | A function returned None when you expected an object — check the caller |
| `KeyError: 'foo'` | Dictionary missing expected key — check where the dict was constructed |
| `ImportError` | Module not installed or circular import — check dependencies |
| `ConnectionRefusedError` | Service not running — check if the dependent service is up |
| `FileNotFoundError` | Wrong path or missing file — check path construction and working directory |

### 2.2 Narrow the Scope

Use these techniques to isolate the failure to the smallest possible unit:

#### Binary Search Through Code

If the failure is in a large function or pipeline:

1. Add a checkpoint (log/print/assert) at the midpoint
2. If the checkpoint is reached with correct state, the bug is in the second half
3. If not, the bug is in the first half
4. Repeat until you find the exact failing operation

#### Minimize the Input

If the failure depends on specific data:

1. Start with the full failing input
2. Remove half the input — does it still fail?
3. Keep removing until you find the minimal input that triggers the failure
4. The minimal input reveals WHAT about the data causes the problem

#### Comment-Out Isolation

If the failure occurs in a complex system:

1. Comment out non-essential components (middleware, plugins, observers)
2. If the failure stops, the last thing you commented out is involved
3. Re-enable components one by one until the failure returns
4. The component that re-introduces the failure is your target

### 2.3 Check Recent Changes

If this is a regression ("it used to work"):

```bash
# Find the commit that introduced the bug
git bisect start
git bisect bad HEAD
git bisect good {last_known_good_commit}
# Then run the reproduction command at each bisect point
git bisect run {reproduction_command}
```

If you don't know the last good commit:

```bash
# Check recent changes to the failing file
git log --oneline -20 -- {failing_file}

# See what changed recently
git diff HEAD~5 -- {failing_file}
```

### 2.4 Check for Related Failures

Before diving deep, check if this failure is part of a larger pattern:

```bash
# Run the broader test suite to see if other tests also fail
{broader_test_command}
```

If multiple tests fail, look for a common root cause rather than fixing each individually. Common patterns:
- **Database/migration issue** — multiple tests fail with schema errors
- **Missing fixture/setup** — multiple tests fail with similar setup errors
- **Dependency upgrade** — multiple tests fail after a version bump
- **Configuration change** — multiple tests fail in the same environment

---

## STEP 3: Form Hypotheses

Based on the evidence gathered in Steps 1-2, generate a ranked list of possible causes.


**Read:** `references/form-hypotheses.md` for detailed step 3: form hypotheses reference material.

## STEP 4: Gather Evidence

Systematically test hypotheses by collecting data. Do NOT change code to fix the bug yet — only add instrumentation.

### 4.1 Add Diagnostic Logging

Add temporary logging to verify or refute your hypotheses:

```python
# Example: Python diagnostic logging
import logging
logger = logging.getLogger(__name__)

# Log input values at the suspected function
logger.debug(f"[DEBUG] function_name called with: arg1={arg1!r}, arg2={arg2!r}")

# Log intermediate state
logger.debug(f"[DEBUG] after transformation: result={result!r}, type={type(result)}")

# Log branch taken
logger.debug(f"[DEBUG] taking branch: {'A' if condition else 'B'}, condition={condition!r}")
```

Keep diagnostic logging clearly marked (prefix with `[DEBUG]` or `[DIAG]`) so it is easy to find and remove later.

### 4.2 Inspect State

Check the actual runtime state at the point of failure:

| Technique | When to Use | How |
|-----------|-------------|-----|
| **Print/log variables** | Any language | Add print statements at key points |
| **Debugger breakpoint** | Complex state | Use `breakpoint()` (Python), `debugger` (JS) |
| **Database inspection** | Data issues | Query the relevant tables/collections directly |
| **Network inspection** | API issues | Log request/response bodies, check status codes |
| **File system check** | Path issues | List directories, check permissions, verify file contents |
| **Environment check** | Config issues | Print env vars, check config file contents |

### 4.3 Use Git Blame

When the bug is in a specific line or block of code, check its history:

```bash
# Who changed this line and when?
git blame {file} -L {start_line},{end_line}

# What was the full commit that introduced this code?
git show {commit_hash}

# Was there a PR or issue associated with this change?
git log --oneline --grep="{keyword}" -10
```

This reveals:
- Whether the code was recently changed (possible regression)
- The original intent of the code (from the commit message)
- Whether the change was part of a larger refactor that may have missed this case

### 4.4 Compare Working vs Broken

If the bug appears in one environment but not another, or with one input but not another:

```bash
# Diff configurations
diff {working_config} {broken_config}

# Diff dependency versions
diff {working_lockfile} {broken_lockfile}

# Compare environments
env | sort > /tmp/env_current.txt
# Compare with known working environment
```

The difference between working and broken often points directly to the cause.

### 4.5 Record Findings

After gathering evidence, update your hypothesis ranking:

```
Evidence Summary:
  Hypothesis 1: {CONFIRMED / REFUTED / INCONCLUSIVE}
    Finding: {what the evidence showed}

  Hypothesis 2: {CONFIRMED / REFUTED / INCONCLUSIVE}
    Finding: {what the evidence showed}

  Root cause candidate: Hypothesis {N}
    Confidence: {HIGH / MEDIUM / LOW}
    Evidence: {summary of supporting evidence}
```

If all hypotheses are refuted, return to Step 3 and generate new ones based on the additional evidence collected.

---

## STEP 5: Root Cause Analysis

Trace from the symptom to the actual underlying cause. The root cause is the earliest point in the causal chain where a fix would prevent the bug.


**Read:** `references/root-cause-analysis.md` for detailed step 5: root cause analysis reference material.

## STEP 6: Apply a Targeted Fix

Fix the root cause with a minimal, focused change.


**Read:** `references/apply-a-targeted-fix.md` for detailed step 6: apply a targeted fix reference material.

## STEP 7: Verify the Fix

Prove the fix works and does not break anything else.

### 7.1 Run the Original Reproduction

Execute the exact reproduction command from Step 1:

```bash
{reproduction_command}
```

| Outcome | Action |
|---------|--------|
| **Passes** | Proceed to regression check |
| **Still fails** | Your root cause analysis was wrong — return to Step 3 with new evidence |
| **Different error** | You may have fixed one issue but exposed another — analyze the new error |

### 7.2 Run Regression Tests

Verify the fix does not break existing functionality:

```bash
# Run the targeted test suite for the affected area
{targeted_test_command}

# Run the broader test suite
{broader_test_command}
```

If any existing test fails:
1. Check if the test failure is related to your fix — your fix may have correctly changed behavior that the old test was wrong about
2. If the test expectation was wrong, update the test
3. If your fix broke a valid test, revise your fix

### 7.3 Test Edge Cases

Based on the root cause, test related edge cases that might have the same underlying issue:

```
Edge cases to verify:
  - {edge_case_1}: {expected_behavior} — {PASS/FAIL}
  - {edge_case_2}: {expected_behavior} — {PASS/FAIL}
  - {edge_case_3}: {expected_behavior} — {PASS/FAIL}
```

Common edge cases to check based on failure type:

| Root Cause Type | Edge Cases to Test |
|----------------|-------------------|
| **Null/undefined** | Empty string, empty array, zero, false, missing key |
| **Off-by-one** | Zero, one, boundary value, max value, max+1 |
| **Encoding** | Unicode, special chars (`+`, `&`, `=`, spaces), emoji, RTL text |
| **Concurrency** | Rapid successive calls, parallel requests, timeout during operation |
| **Path handling** | Spaces in path, relative vs absolute, trailing slash, symlinks |

---

## STEP 8: Prevent Recurrence

Make sure this class of bug cannot happen again.


**Read:** `references/prevent-recurrence.md` for detailed step 8: prevent recurrence reference material.

# Fix for: users with '+' in email could not log in
# Root cause: email was used as URL parameter without encoding
# See: https://github.com/org/repo/issues/123
user_email = urllib.parse.quote(user_email)
```

This helps future developers understand WHY unusual-looking code exists.

---

## Common Debugging Patterns


**Read:** `references/common-debugging-patterns.md` for detailed common debugging patterns reference material.

## Anti-Patterns to Avoid


**Read:** `references/anti-patterns-to-avoid.md` for detailed anti-patterns to avoid reference material.

## MUST DO

- Always reproduce the failure yourself before investigating — never debug based on assumptions
- Always form hypotheses before gathering evidence — undirected investigation wastes time
- Always verify the root cause with a prediction before writing a fix
- Always run the original reproduction after applying the fix — no exceptions
- Always add a regression test that covers the specific bug scenario
- Always remove diagnostic logging before finalizing the fix
- Always check for related failures — the same root cause may affect other areas
- Always trace to the root cause — fixing the proximate cause creates band-aids
- Always try at least 3 hypotheses before concluding the bug is "impossible"
- Always document non-obvious fixes with a comment explaining the WHY

## MUST NOT DO

- MUST NOT make random code changes hoping to fix the bug — understand the cause first
- MUST NOT fix symptoms instead of root causes — trace the causal chain to the source
- MUST NOT skip reproduction — if you cannot reproduce it, you cannot verify a fix
- MUST NOT leave diagnostic logging in the code — always clean up debug prints and temporary logs
- MUST NOT declare a bug fixed without running the reproduction command — "it looks right" is not verification
- MUST NOT ignore intermittent failures — they are real bugs, usually race conditions or resource issues
- MUST NOT rewrite code you don't understand instead of debugging it — understand first, fix second
- MUST NOT proceed past Step 1 if you cannot reproduce the failure — go back to the user for more information
- MUST NOT fixate on a single hypothesis — if evidence contradicts it, generate new hypotheses
- MUST NOT skip the regression test — a fix without a test is a fix that will break again
