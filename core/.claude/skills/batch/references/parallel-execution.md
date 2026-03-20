# Parallel Execution Examples

## Pre-Work Example

Complete foundational changes that all batches depend on:

```bash
# Rename the source file first — all batches import from the new location
git mv src/services/UserService.ts src/services/AccountService.ts

# Update the barrel export
# In src/services/index.ts: change "export { UserService } from './UserService'"
#                          to "export { AccountService } from './AccountService'"

# Rename the class inside the file
# In src/services/AccountService.ts: class UserService → class AccountService

# Commit pre-work so subagents branch from a clean state
git add src/services/AccountService.ts src/services/index.ts
git commit -m "refactor: rename UserService file and class to AccountService

Pre-work for codebase-wide rename. All import paths will be updated in parallel batches."
```

## Subagent Dispatch Template

Each subagent gets a precise prompt with the change pattern, affected files, and
expected before/after:

```
Agent("
## Objective
Update all UserService references to AccountService in the controller layer.

## Change Pattern
- Import: `import { UserService } from '../services/UserService'`
  → `import { AccountService } from '../services/AccountService'`
- Usage: `new UserService(` → `new AccountService(`
- Usage: `userService.` → `accountService.` (variable names)
- Type: `UserService` → `AccountService` (type annotations)

## Files You Own (modify these)
- src/api/controllers/UserController.ts
- src/api/controllers/AdminController.ts
- tests/api/UserController.test.ts

## Files You May Read (do NOT modify)
- src/services/AccountService.ts (read for the new interface)
- src/services/index.ts (read to verify export name)

## Verification
Run: `npx tsc --noEmit src/api/controllers/*.ts`
Run: `npx jest tests/api/UserController.test.ts --no-coverage`
Expected: No type errors, all tests pass.

## Completion Report
Report: status, files modified, lines changed, test results.
", isolation="worktree")
```

## Multi-Batch Dispatch Example

Dispatch all batch agents simultaneously:

```
# Batch A — Controllers
Agent("[Batch A prompt as above]", isolation="worktree")

# Batch B — Middleware
Agent("
## Objective
Update UserService references in authentication middleware.

## Change Pattern
[same pattern as above]

## Files You Own
- src/middleware/auth.ts
- tests/e2e/auth.test.ts

## Verification
Run: `npx tsc --noEmit src/middleware/auth.ts`
Run: `npx jest tests/e2e/auth.test.ts --no-coverage`
", isolation="worktree")

# Batch C — Unit Tests
Agent("
## Objective
Rename and update UserService unit tests and fixtures.

## Files You Own
- tests/services/UserService.test.ts (rename to AccountService.test.ts)
- tests/fixtures/userFixtures.ts

## Special Instructions
- Use `git mv` to rename test file (preserves history)
- Update all mock/stub references from UserService to AccountService

## Verification
Run: `npx jest tests/services/AccountService.test.ts --no-coverage`
", isolation="worktree")

# Batch D — Documentation
Agent("
## Objective
Update all UserService references in documentation.

## Files You Own
- docs/architecture.md
- docs/api-reference.md
- README.md

## Special Instructions
- Preserve document structure and formatting
- Update code examples, not just prose
- Do NOT change historical references in ADR documents

## Verification
No automated verification — report changes for manual review.
", isolation="worktree")
```

## Retry with Failure Context

When a batch fails, retry with enriched context about the failure:

```
Agent("
## Objective
RETRY: Update UserService references in authentication middleware.

## Previous Failure
The prior attempt failed with:
  TypeError: Property 'validateToken' does not exist on type 'AccountService'

The prior agent renamed the import but missed that auth.ts uses a method
'validateToken' that was renamed to 'verifyToken' in the AccountService refactor.

## Updated Change Pattern
- Import: UserService → AccountService
- Method: validateToken → verifyToken (method was renamed in pre-work)
- Variable: userService → accountService

## Files You Own
- src/middleware/auth.ts
- tests/e2e/auth.test.ts

## Verification
Run: `npx tsc --noEmit src/middleware/auth.ts`
Run: `npx jest tests/e2e/auth.test.ts --no-coverage`
", isolation="worktree")
```
