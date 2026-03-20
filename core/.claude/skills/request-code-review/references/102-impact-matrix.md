# 10.2 Impact Matrix

### 10.2 Impact Matrix

```
DEPENDENCY IMPACT ANALYSIS
===========================

Changed shared utilities:
  src/utils/validation.ts (imported by 12 files)
    Changed function: validateEmail()
    Signature change: NO (safe)
    Behavior change: YES — now rejects emails with consecutive dots
    Affected consumers:
      - src/services/UserService.ts (uses validateEmail in registration)
      - src/services/InviteService.ts (uses validateEmail in invite flow)
      - src/api/routes/auth.ts (uses validateEmail in login)
    Risk: MEDIUM — some previously accepted emails will now be rejected

  src/types/User.ts (imported by 8 files)
    Changed: Added required `role` field to User interface
    Impact: All files that construct User objects must provide `role`
    Affected consumers: {list files that construct User objects}
    Risk: HIGH — TypeScript will catch this at compile time, but runtime
          code that constructs Users from raw data (API responses, DB rows)
          may fail silently
```

