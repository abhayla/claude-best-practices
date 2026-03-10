---
name: fix-loop
description: >
  Iterative fix cycle: analyze failures, apply minimal fixes, optionally retest.
  Full Loop mode (with retest command) iterates until resolved. Single Fix mode
  (no retest) does one pass. Use when tests fail, build breaks, or runtime errors.
allowed-tools: "Bash Read Grep Glob Write Edit Skill"
argument-hint: "[failure_output] [retest_command: <cmd>] [max_iterations: N]"
---

# Fix Loop — Iterative Fix Cycle

Analyze failures, apply minimal fixes, and optionally retest until resolved.

**Input:** $ARGUMENTS

---

## Mode Detection

| Input | Mode | Behavior |
|-------|------|----------|
| `retest_command` provided | **Full Loop** | Fix → retest → repeat until pass (max iterations) |
| No `retest_command` | **Single Fix** | Analyze → apply one fix → report |

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `failure_output` | — | The error output to analyze |
| `retest_command` | — | Command to re-run tests after fix |
| `max_iterations` | 5 | Maximum fix-test cycles |
| `files_of_interest` | — | Specific files to focus on |

---

## STEP 1: Analyze Failure

1. Parse the error output to identify:
   - Error type (compile, assertion, runtime, timeout)
   - Failing file and line number
   - Expected vs actual values
   - Stack trace information

2. Read the failing source code and test code

3. Identify root cause with confidence level (High/Medium/Low)

## STEP 2: Apply Fix

1. Make the minimal change to address the root cause
2. Do NOT refactor unrelated code
3. Do NOT change test expectations unless the test is wrong
4. Prefer fixing source code over fixing tests

## STEP 3: Retest (Full Loop mode only)

Run the retest command and check results:
- If all pass → report success
- If different failure → analyze new failure (new iteration)
- If same failure → escalate analysis depth
- If max iterations reached → report remaining failures and suggest manual review

## STEP 4: Report

**On success:**
```
Fix Loop: RESOLVED in {N} iterations
  Root cause: [description]
  Fix applied: [file:line — what changed]
  Tests: all passing
```

**On failure (max iterations):**
```
Fix Loop: UNRESOLVED after {N} iterations
  Remaining failures: [list]
  Attempted fixes: [list]
  Suggestion: [manual review guidance]
```

---

## ESCALATION

If the same error persists after 2 iterations:
1. Widen the search — read more context around the failing code
2. Check for deeper root causes (configuration, dependencies, environment)
3. Consider delegating to debugger agent for complex issues

## CRITICAL RULES

- Maximum {max_iterations} iterations — do NOT infinite loop
- Each iteration must try a DIFFERENT fix approach
- Never suppress errors or add broad exception handlers
- If confidence is Low, explain reasoning and ask for user input
