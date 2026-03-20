# Verification

### 3.3 Monitor Progress

Track each agent's status as results come in:

```
Batch Execution Status
━━━━━━━━━━━━━━━━━━━━━━
[DONE]    Pre-work: File rename + class rename (committed)
[DONE]    Batch A: Controllers — PASSED (3 files, 12 lines changed)
[RUNNING] Batch B: Middleware — dispatched 45s ago
[DONE]    Batch C: Unit tests — PASSED (2 files renamed, 28 lines changed)
[DONE]    Batch D: Documentation — PASSED (3 files, 8 lines changed)
[PENDING] Post-work: Config + verification (waiting on Batch B)
```

### 3.4 Handle Partial Failures

If some batches succeed and others fail:

1. **Commit successful batches** — Do not risk losing passing work
2. **Analyze the failure** — Read the agent's error report
3. **Retry with failure context** — Pass what was tried and why it failed
4. **Continue unblocked work** — Do not wait for retries if other batches are independent

```
Agent("
