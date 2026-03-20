# STEP 9: Completion Summary

### 9.1 Full Success

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUBAGENT ORCHESTRATION COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Task: {task_description}
Subtasks: {total}/{total} completed
Waves: {wave_count}
Subagents dispatched: {agent_count} ({retry_count} retries)

Results:
  [PASSED] Agent A: User validation — 3 files, 3 tests added
  [PASSED] Agent B: Order validation — 3 files, 4 tests added
  [PASSED] Agent C: Product validation — 3 files, 3 tests added

Integration verification: ALL TESTS PASSING
Commits: {commit_count}

Files modified:
  src/api/users.py, src/api/orders.py, src/api/products.py
  src/api/validators.py (pre-work)
  tests/test_users.py, tests/test_orders.py, tests/test_products.py
```

### 9.2 Partial Success

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUBAGENT ORCHESTRATION PAUSED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Task: {task_description}
Subtasks: {completed}/{total} completed, {failed} failed

Results:
  [PASSED]  Agent A: User validation — committed
  [FAILED]  Agent B: Order validation — 3 retries exhausted
  [PASSED]  Agent C: Product validation — committed
  [BLOCKED] Agent D: Integration tests — blocked on Agent B

Failed subtask details:
  Agent B: Order validation
    Last error: {error_summary}
    Files with uncommitted changes: {file_list}
    Attempts: 3/3

Options:
  1. Fix Order validation manually, then resume
  2. Skip Order validation and proceed with unblocked subtasks
  3. Roll back all changes from this orchestration
```

### 9.3 Post-Completion

After orchestration completes:

1. **Run the full project test suite** — Subagent-level tests passing does not guarantee integration correctness
2. **Review the diff** — `git diff {start_hash}..HEAD` to see all changes holistically
3. **Invoke `/learn-n-improve`** to capture orchestration lessons:
   - Which subtask prompts worked well
   - Which needed retries and why
   - File boundary violations encountered
   - Patterns to reuse in future orchestrations

```
Skill("learn-n-improve", args="session")
```

---

