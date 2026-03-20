# STEP 6: Completion Summary

### 6.1 Full Success

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PLAN EXECUTION COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Plan: {plan_name}
Tasks: {total}/{total} completed
Commits: {commit_count}
Duration: ~{elapsed} min

Results:
  [x] Task 1: {title} — PASSED
  [x] Task 2: {title} — PASSED
  [x] Task 3: {title} — PASSED (1 fix attempt)
  [x] Task 4: {title} — PASSED
  [x] Task 5: {title} — PASSED
  [x] Task 6: {title} — PASSED

All verifications passed.

Commits created:
  {hash1} plan-exec: {task_1_title}
  {hash2} plan-exec: {task_2_title}
  {hash3} plan-exec: Wave 2 — {task_3_title}, {task_4_title}
  {hash4} plan-exec: {task_5_title}
  {hash5} plan-exec: {task_6_title}

Suggested next steps:
  - Run full test suite to check for regressions
  - Review changes: git diff {rollback_hash}..HEAD
  - Squash commits if desired: git rebase -i {rollback_hash}
```

### 6.2 Partial Success

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PLAN EXECUTION PAUSED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Plan: {plan_name}
Tasks: {completed}/{total} completed, {failed} failed, {skipped} skipped

Results:
  [x] Task 1: {title} — PASSED
  [x] Task 2: {title} — PASSED
  [!] Task 3: {title} — FAILED (3 attempts exhausted)
  [-] Task 4: {title} — SKIPPED (depends on Task 3)
  [x] Task 5: {title} — PASSED (independent)
  [-] Task 6: {title} — SKIPPED (depends on Task 3)

Failed task details:
  Task 3: {title}
    Last error: {error_summary}
    Files with uncommitted changes: {file_list}

To resume after fixing Task 3:
  /executing-plans {plan_file} --from 3
```

### 6.3 Invoke Learn and Improve

After execution (success or partial), invoke `/learn-n-improve` to capture lessons:

```
Skill("learn-n-improve", args="session")
```

This records which tasks needed fix loops, what patterns caused failures, and what worked well for future plan creation.

---

