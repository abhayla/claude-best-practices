# STEP 2: Review the Session

### 2.1 Catalog All Work Attempted

Review the full conversation history and categorize every task:

```
Session Work Catalog:
  COMPLETED:
    - [task description] — [outcome summary]
    - [task description] — [outcome summary]

  IN PROGRESS:
    - [task description] — [current state, what remains]

  FAILED / ABANDONED:
    - [task description] — [why it failed, what was tried]

  DEFERRED:
    - [task description] — [why deferred, prerequisites]
```

Be thorough. Scan from the beginning of the conversation. Include:
- Feature implementations
- Bug investigations and fixes
- Configuration changes
- Research and exploration
- Refactoring
- Test additions or modifications
- Documentation updates
- Failed attempts (these are especially valuable for the next session)

### 2.2 Extract Key Interactions

Identify conversation moments that carry context the next session needs:

| Type | What to Capture | Example |
|------|----------------|---------|
| **User corrections** | When the user redirected your approach | "User said: don't modify that file, it's auto-generated" |
| **Scope changes** | When requirements shifted mid-session | "Originally asked for X, pivoted to Y because of Z" |
| **Blocked moments** | When progress stalled and why | "Blocked on API response format — docs were wrong" |
| **Explicit preferences** | User preferences revealed during work | "User prefers integration tests over unit tests for this module" |
| **Rejected approaches** | Approaches considered but not taken | "Considered using Redis but user wants to keep deps minimal" |

### 2.3 Measure Progress

If working from a spec, issue, or previous handover's next-steps list:

```
Progress Against Plan:
  Original items: N
  Completed: X
  Partially done: Y
  Not started: Z
  New items added: W

  Completion rate: X/N (percentage)
```

This gives the next session a clear sense of momentum and what remains.

---

