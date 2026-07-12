# STEP 6: Apply a Targeted Fix

### 6.1 Design the Fix

Before writing code, plan the fix:

```
Fix Plan:
  Root cause: {root cause from Step 5}
  Fix approach: {what to change}
  Files to modify: {list of files}
  Risk assessment: {what could go wrong with this fix}
  Alternative approaches considered: {other ways to fix, and why this one is better}
```

### 6.2 Fix Principles

| Principle | Description |
|-----------|-------------|
| **Minimal change** | Change only what is necessary to fix the root cause. Do NOT refactor nearby code. |
| **Same abstraction level** | Fix at the same level as the root cause — don't add workarounds at a higher level |
| **Preserve behavior** | The fix should change only the broken behavior, not any working behavior |
| **Defensive coding** | Add validation/guards at the boundary where bad data enters, not deep inside the call chain |
| **No TODO fixes** | Do not write `// TODO: fix this properly later` — fix it properly now or document the limitation |

### 6.3 Implement the Fix

Apply the fix using targeted edits:

1. Make the minimum code change to address the root cause
2. If the fix requires changes to multiple files, change them in logical order
3. Do NOT fix unrelated issues you noticed during debugging — log them separately

### 6.4 Remove Diagnostic Code

After implementing the fix, remove all temporary debugging code added in Step 4:

- Remove `[DEBUG]` / `[DIAG]` log statements
- Remove temporary print statements
- Remove debugging breakpoints
- Revert any temporary configuration changes

Leaving diagnostic code in production is a common source of log noise, performance issues, and security leaks.

---

