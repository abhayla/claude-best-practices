# STEP 6: Generate Auto-Fixes

### 6.1 Auto-Fix Generation

For each auto-fixable violation:

1. **Read the current file content** at the violation line
2. **Apply the fix-pattern/fix-replacement** from the rule definition
3. **Generate a before/after diff** showing exactly what will change
4. **Validate the fix** — ensure it does not break syntax (for simple checks: matching brackets, valid indentation)

### 6.2 Auto-Fix Report

Present fixes for user confirmation:

```
AUTO-FIX PROPOSALS
==================

Fix 1 of 3: [W] no-print-debug (src/services/user_service.py:23)
  Before: print(f"Creating user: {email}")
  After:  logger.debug(f"Creating user: {email}")
  Note:   Requires `import logging; logger = logging.getLogger(__name__)` at top of file

Fix 2 of 3: [C] no-debugger (src/routes/users.py:45)
  Before:     debugger
  After:      (line removed)

Fix 3 of 3: [W] no-console-log (src/components/UserForm.tsx:112)
  Before: console.log('form submitted', data);
  After:  (line removed)

Apply all fixes? [y/N/select]
  y — Apply all 3 fixes
  N — Skip auto-fixes, report only
  select — Choose which fixes to apply (e.g., "1,3" to apply fixes 1 and 3)
```

### 6.3 Fix Application

When applying fixes:

```bash
