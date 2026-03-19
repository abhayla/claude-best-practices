# Dry Run Mode

Preview all changes without applying them. Essential for high-risk changes or
unfamiliar codebases.

## Generate Preview Diffs

For each file that would be changed, show the expected diff:

```
Dry Run: Rename UserService → AccountService
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

--- src/api/controllers/UserController.ts
+++ src/api/controllers/UserController.ts
@@ -1,4 +1,4 @@
-import { UserService } from '../services/UserService';
+import { AccountService } from '../services/AccountService';

 export class UserController {
-  constructor(private userService: UserService) {}
+  constructor(private accountService: AccountService) {}

--- src/middleware/auth.ts
+++ src/middleware/auth.ts
@@ -1,3 +1,3 @@
-import { UserService } from '../services/UserService';
+import { AccountService } from '../services/AccountService';

-const userService = new UserService();
+const accountService = new AccountService();
```

## Batch Summary

```
Dry Run Summary
━━━━━━━━━━━━━━━

Batches: 4 parallel + pre-work + post-work
Total files: 18
Total lines changed: ~94 (47 removals, 47 additions)

Batch A (Controllers):    3 files, ~24 lines
Batch B (Middleware):      2 files, ~12 lines
Batch C (Tests):           2 files, ~38 lines
Batch D (Docs):            3 files, ~8 lines
Pre/Post-work:             8 files, ~12 lines

Estimated execution time: ~3 minutes (parallel)
```

## Risk Assessment

```
Risk Assessment
━━━━━━━━━━━━━━━

LOW RISK:
  - Documentation updates (no runtime impact)
  - Import path changes (type checker catches errors)

MEDIUM RISK:
  - Variable renames (string-based references may be missed)
  - Test fixture updates (may affect test isolation)

HIGH RISK:
  - Config file changes (may affect CI/CD pipelines)
  - Environment variable references (runtime failures, not caught by type checker)

AMBIGUOUS (requires manual review):
  - 3 files flagged in Step 1.4
```

## User Confirmation

```
Dry run complete. No changes have been applied.

Options:
  1. Execute the full batch plan as shown
  2. Execute with modifications (specify which batches to skip or reorder)
  3. Abort — no changes will be made

Proceed with option [1/2/3]?
```

---

# Progress Tracking

Real-time visibility into batch execution status.

## Progress Dashboard

Maintain a live tracker throughout execution:

```
Batch Progress: Rename UserService → AccountService
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Phase: PARALLEL EXECUTION
Started: 2 minutes ago

[DONE]    Pre-work       2/2 files    committed
[DONE]    Batch A        3/3 files    controllers updated, tests passing
[RUNNING] Batch B        0/2 files    agent dispatched 30s ago
[DONE]    Batch C        2/2 files    test files renamed, tests passing
[DONE]    Batch D        3/3 files    documentation updated
[PENDING] Post-work      0/4 files    waiting on Batch B

Overall: 10/16 files complete (62%)
Tests: passing (last run: Batch C verification)
Errors: 0
```

## Status Updates

After each batch completes, update the tracker and report:

```
Batch B COMPLETE — Middleware
  Status: PASSED
  Files modified: src/middleware/auth.ts, tests/e2e/auth.test.ts
  Lines changed: 12 (6 removals, 6 additions)
  Verification: tsc clean, 4/4 tests passing
  Duration: 45 seconds

Proceeding to post-work phase...
```

## Final Report

After all batches and post-work complete:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BATCH CHANGE COMPLETE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Change: Rename UserService → AccountService
Duration: 3 minutes 12 seconds

Execution:
  Pre-work:  2 files committed
  Batch A:   3 files — PASSED (1st attempt)
  Batch B:   2 files — PASSED (1st attempt)
  Batch C:   2 files — PASSED (1st attempt)
  Batch D:   3 files — PASSED (1st attempt)
  Post-work: 4 files committed

Verification:
  TypeScript:  npx tsc --noEmit — clean (0 errors)
  Tests:       npm test — 142 passed, 0 failed, 0 skipped
  Lint:        npx eslint — 0 warnings, 0 errors
  Old refs:    grep "UserService" — 0 matches in src/tests
  Symbol count: 47 references migrated (47 old → 47 new)

Commits: 6 (1 pre-work + 4 batches + 1 post-work)
Rollback tag: batch/pre-rename-userservice
PR: ready to create (18 files, ~94 lines changed)

Files modified:
  src/services/AccountService.ts (renamed from UserService.ts)
  src/services/index.ts
  src/api/controllers/UserController.ts
  src/api/controllers/AdminController.ts
  src/middleware/auth.ts
  tests/services/AccountService.test.ts (renamed from UserService.test.ts)
  tests/api/UserController.test.ts
  tests/e2e/auth.test.ts
  tests/fixtures/userFixtures.ts
  jest.config.ts
  tsconfig.json
  .github/workflows/test.yml
  docs/architecture.md
  docs/api-reference.md
  README.md
```

---
