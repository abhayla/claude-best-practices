# STEP 4: Fix Loop (Conditional)

### 4.1 Collect All Blocking Findings

Gather all BLOCK/CRITICAL findings from Steps 1-6 into a single fix list:

```
BLOCKING FINDINGS TO FIX:
  [QG-1] Cyclomatic complexity 22 in src/services/order.py:process_order
  [SEC-1] SQL injection in src/api/routes.py:42
  [AR-1] Unresolved critical: missing null check in payment flow
  [PS-1] Debugger statement in src/routes/users.py:45
```

### 4.2 Apply Fixes

For each blocking finding:

1. Apply the fix (using the suggested fix from the sub-skill's report)
2. Verify the fix does not introduce regressions:

```
Skill("auto-verify", args="--files <fixed_files>")
```

3. If `auto-verify` fails:

```
Skill("fix-loop", args="retest_command: <TEST_CMD> max_iterations: 3")
```

### 4.3 Scope-Aware Re-Run Policy

After fix-loop applies fixes, determine the re-run scope based on whether the fix touched files outside the original finding's scope:

1. **Identify fix scope**: Compare the files modified by the fix against the files referenced in the original finding
2. **Classify fix reach**:

| Fix Reach | Condition | Re-Run Scope |
|-----------|-----------|-------------|
| Scoped | Fix modified ONLY files listed in the original finding (same directory/module) | Re-run ONLY the sub-skill that produced the BLOCK status |
| Cross-cutting | Fix modified files in DIFFERENT directories or modules than the original finding | Re-run ALL sub-skills (quality, architecture, security, adversarial, risk, PR standards) |

3. **Detect cross-cutting fixes**:

```bash
