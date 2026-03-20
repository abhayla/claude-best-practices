# Verification

### 6.2 Multiple Subagent Failures

When 2+ subagents fail in the same wave:

1. **Check for a common cause** — Same import error, shared dependency issue, or environment problem
2. **Fix the root cause in main context** if it is shared (e.g., missing package, broken base class)
3. **Commit the fix** before retrying
4. **Re-dispatch all failed subtasks** with updated context

### 6.3 Cascading Failures

When a failed subtask blocks downstream waves:

```
Wave 1: Agent A (PASSED) + Agent B (FAILED)
Wave 2: Agent C (depends on A — can proceed) + Agent D (depends on B — BLOCKED)
```

Action:
1. Dispatch Agent C (its dependency is satisfied)
2. Retry Agent B in parallel with Agent C
3. Once Agent B passes, dispatch Agent D

Do NOT wait for all retries to complete before making progress on unblocked work.

### 6.4 Retry Limits

| Attempt | Strategy |
|---------|----------|
| **1st retry** | Add failure context to prompt, suggest different approach |
| **2nd retry** | Simplify the task scope — break the subtask into smaller pieces |
| **3rd retry** | Escalate — do the work directly in the main context or ask the user |

MUST NOT retry more than 3 times. After 3 failures, the subtask has a deeper issue that automated retry will not solve.

### 6.5 Rollback a Failed Wave

If a wave produces partial results that cannot be salvaged:

```bash
