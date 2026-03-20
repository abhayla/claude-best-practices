# 10.4 Stale Handover Detection

### 10.4 Stale Handover Detection

A handover may be stale if:

| Signal | Threshold | Action |
|--------|-----------|--------|
| **Age** | > 7 days old | Warn: "This handover is {N} days old — the codebase may have changed." |
| **Branch mismatch** | Handover branch != current branch | Warn: "Handover was written on branch `X`, but you are on branch `Y`." |
| **Git state mismatch** | Files listed in handover no longer modified | Warn: "Some changes listed in the handover appear to have been committed or reverted." |

For stale handovers:
1. Read the handover for context (decisions and pitfalls are still valuable)
2. Re-gather current state (git, tests, env) instead of trusting the handover's state section
3. Cross-reference next steps against what has changed

