---
name: batch
description: >
  Orchestrate parallel codebase-wide changes — renames, API migrations, pattern updates
  across many files. Performs exhaustive impact analysis, decomposes changes into independent
  batches, dispatches parallel subagents in isolated worktrees, verifies consistency across
  the full codebase, runs auto-simplify cleanup, and creates well-structured PRs with
  rollback safety. Inspired by Boris Cherny's approach to large-scale codemods.
triggers:
  - /batch
  - /codemod
  - /mass-rename
  - /migrate-api
  - batch change
  - codebase-wide rename
  - mass update
  - migrate api
  - codemod
  - rename across codebase
  - update all callers
  - replace deprecated
allowed-tools: "Bash Read Write Edit Grep Glob Agent Skill"
argument-hint: "<description of codebase-wide change, e.g. 'rename UserService to AccountService' or 'migrate from axios v0.x to v1.x'>"
---

# Batch — Parallel Codebase-Wide Changes

Orchestrate large-scale changes across an entire codebase: renames, API migrations,
pattern updates, dependency upgrades, and structural refactors. Changes are analyzed,
decomposed into independent batches, executed in parallel via isolated subagents, and
verified for full-codebase consistency.

**Change Request:** $ARGUMENTS

---

## STEP 1: Codebase-Wide Impact Analysis

Before changing anything, build a complete picture of every file affected by the change.
Missing even one file turns a clean migration into a broken build.

### 1.1 Exhaustive Search

Run multiple search strategies to find ALL references. A single grep is never enough.

```bash
# Strategy 1: Exact string match
grep -rn "UserService" --include="*.ts" --include="*.tsx" --include="*.js" src/ tests/ scripts/

# Strategy 2: Case variations
grep -rn -i "userservice" --include="*.ts" --include="*.tsx" src/ tests/

# Strategy 3: Import paths (may differ from class name)
grep -rn "from.*user-service" --include="*.ts" src/
grep -rn "require.*user-service" --include="*.js" src/

# Strategy 4: String literals and comments
grep -rn "'UserService'\|\"UserService\"" src/ tests/ docs/

# Strategy 5: Configuration files
grep -rn "UserService" *.json *.yml *.yaml *.toml config/ .github/

# Strategy 6: Documentation
grep -rn "UserService" docs/ *.md README*

# Strategy 7: Generated files and build config
grep -rn "UserService" webpack.config.* tsconfig.* jest.config.* vite.config.*
```

### 1.2 Categorize Affected Files

Sort every match into categories — each category may need different handling:

```
Impact Analysis: Rename UserService → AccountService
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DIRECT REFERENCES (class/function usage):
  src/services/UserService.ts          — class definition (rename class + file)
  src/services/index.ts                — re-export
  src/api/controllers/UserController.ts — imports and instantiates UserService
  src/api/controllers/AdminController.ts — imports UserService for admin ops
  src/middleware/auth.ts                — imports UserService for token validation

TRANSITIVE DEPENDENCIES (import chains):
  src/api/routes/userRoutes.ts         — imports UserController (which uses UserService)
  src/app.ts                           — registers userRoutes

TEST FILES:
  tests/services/UserService.test.ts   — unit tests (rename file + all references)
  tests/api/UserController.test.ts     — integration tests with UserService mock
  tests/e2e/auth.test.ts              — e2e test that references UserService in setup
  tests/fixtures/userFixtures.ts       — test fixtures with UserService factory

CONFIG FILES:
  jest.config.ts                       — moduleNameMapper for UserService path
  tsconfig.json                        — path alias for @services/UserService
  docker-compose.yml                   — environment variable USER_SERVICE_URL

DOCUMENTATION:
  docs/architecture.md                 — references UserService in architecture diagram
  docs/api-reference.md               — documents UserService endpoints
  README.md                           — mentions UserService in quickstart

GENERATED / CI:
  .github/workflows/test.yml          — references UserService in test job name
  openapi.yaml                        — schema references

TOTAL: 18 files affected
```

### 1.3 Verify Completeness

After the initial search, validate that nothing was missed:

```bash
# Count total occurrences across the entire repo
grep -rn "UserService" . --include="*.ts" --include="*.tsx" --include="*.js" \
  --include="*.json" --include="*.yml" --include="*.yaml" --include="*.md" \
  --include="*.toml" | wc -l

# Cross-reference: search for the file path pattern too
grep -rn "user-service\|UserService\|user_service" . | grep -v node_modules | grep -v .git

# Check for dynamic references (string concatenation, template literals)
grep -rn "User.*Service\|user.*service" --include="*.ts" src/ | grep -v "UserService"
```

### 1.4 Flag Ambiguous Matches

Some matches need human judgment:

```
AMBIGUOUS — Requires manual review:
  src/utils/naming.ts:42    — "UserServiceFactory" — rename to AccountServiceFactory?
  src/types/global.d.ts:18  — "UserServiceConfig" — rename to AccountServiceConfig?
  docs/adr/003-auth.md:15   — historical reference — update or leave as-is?
  migrations/002_add_user_service_table.sql — migration file — NEVER rename
```

Present ambiguous matches to the user for a decision before proceeding.

---

## STEP 2: Change Decomposition

Group affected files into independent batches that can be processed in parallel without
conflicts.

### 2.1 Dependency Graph

Map which files import from which:

```
Dependency Graph:
  UserService.ts ← UserController.ts ← userRoutes.ts ← app.ts
  UserService.ts ← AdminController.ts
  UserService.ts ← auth.ts
  UserService.test.ts (standalone — mocks UserService)
  UserController.test.ts (standalone — mocks UserService)
```

### 2.2 Batch Grouping Rules

| Rule | Rationale |
|------|-----------|
| Files in different modules with no shared imports can be parallel | No merge conflicts possible |
| Files with shared imports must be in the same batch OR sequential | Prevents broken import chains |
| Test files grouped with their source files | Tests must stay in sync with source |
| Config files in a dedicated batch (or main context) | Config changes affect everything |
| Documentation in its own batch | No code dependencies |
| Generated files handled last | May need regeneration after source changes |

### 2.3 Batch Assignment

```
Batch Plan: Rename UserService → AccountService
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PRE-WORK (main context — before any parallel dispatch):
  - Rename src/services/UserService.ts → src/services/AccountService.ts
  - Update src/services/index.ts re-export
  - Commit: "refactor: rename UserService file to AccountService"

BATCH A — Controllers + Tests:
  src/api/controllers/UserController.ts
  src/api/controllers/AdminController.ts
  tests/api/UserController.test.ts

BATCH B — Middleware + Auth Tests:
  src/middleware/auth.ts
  tests/e2e/auth.test.ts

BATCH C — Unit Tests + Fixtures:
  tests/services/UserService.test.ts → AccountService.test.ts
  tests/fixtures/userFixtures.ts

BATCH D — Documentation:
  docs/architecture.md
  docs/api-reference.md
  README.md

POST-WORK (main context — after all batches merge):
  - Update jest.config.ts path aliases
  - Update tsconfig.json path aliases
  - Update .github/workflows/test.yml
  - Regenerate openapi.yaml if applicable
  - Run full test suite
```

### 2.4 Present Plan for Approval

Before executing, show the user the full batch plan:

```
Batch Execution Plan
━━━━━━━━━━━━━━━━━━━━
Change: Rename UserService → AccountService
Files affected: 18
Batches: 4 parallel + pre-work + post-work

Pre-work:  2 files (main context, sequential)
Batch A:   3 files (controllers + controller tests)
Batch B:   2 files (middleware + auth tests)
Batch C:   2 files (unit tests + fixtures)
Batch D:   3 files (documentation)
Post-work: 4 files (config + CI + verification)

Estimated time: ~3 minutes
Parallel agents: 4

Proceed? [Waiting for user confirmation]
```

MUST NOT execute without user confirmation. The plan may reveal files the user does not
want changed, or batches that need different ordering.

---

## STEP 3: Parallel Execution

Dispatch one subagent per batch, each in its own worktree for full isolation.

### 3.1 Pre-Work

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

### 3.2 Dispatch Subagents

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

---

## STEP 4: Consistency Verification

After all batches complete and their branches are merged, verify the entire codebase is
consistent. Individual batch verification is necessary but not sufficient.

### 4.1 Type Checker / Compiler

```bash
# TypeScript
npx tsc --noEmit

# Python (mypy)
mypy src/ --ignore-missing-imports

# Go
go build ./...

# Rust
cargo check

# Java/Kotlin
./gradlew compileJava compileKotlin
```

Every type error after a batch change indicates a missed reference.

### 4.2 Linter

```bash
# ESLint
npx eslint src/ tests/ --max-warnings=0

# Ruff (Python)
ruff check src/ tests/

# golangci-lint
golangci-lint run ./...
```

Linter errors after renames often indicate unused imports or undefined references.

### 4.3 Full Test Suite

```bash
# Run the complete test suite — not just the files that were changed
npm test
pytest tests/ -v
go test ./...
./gradlew test
```

A passing full suite is the strongest signal that the batch change is correct.

### 4.4 Re-Run Impact Analysis

Repeat the search from Step 1 to verify no references were missed:

```bash
# The OLD name should appear ZERO times (excluding git history, changelogs, ADRs)
grep -rn "UserService" src/ tests/ --include="*.ts" --include="*.tsx" --include="*.js"

# Expected output: (empty)
# If any results remain, those files were missed — fix them before proceeding
```

### 4.5 Symbol Count Comparison

For renames, verify the counts balance:

```bash
# Before the change (check from git history)
git stash
grep -rn "UserService" src/ tests/ --include="*.ts" | wc -l
# Result: 47

git stash pop
grep -rn "AccountService" src/ tests/ --include="*.ts" | wc -l
# Result: should be 47 (same count, new name)
```

If counts do not match, investigate: either references were missed, or some were
intentionally not renamed (ambiguous matches from Step 1.4).

### 4.6 Import Graph Validation

Verify no broken import chains exist:

```bash
# TypeScript: check for unresolved imports
npx tsc --noEmit 2>&1 | grep "Cannot find module"

# Python: check for import errors
python -c "import src.services.AccountService" 2>&1

# Node.js: attempt to require the entry point
node -e "require('./src/index')" 2>&1
```

---

## STEP 5: Auto-Simplify

After a codebase-wide change, leftover artifacts accumulate. Run a cleanup pass to
remove dead code, unused imports, and redundant patterns.

### 5.1 Remove Unused Imports

Renames often leave behind imports of the old name that the search-and-replace missed:

```bash
# TypeScript/JavaScript: use eslint auto-fix
npx eslint src/ tests/ --rule '{"no-unused-vars": "error", "import/no-unresolved": "error"}' --fix

# Python: use autoflake
autoflake --remove-all-unused-imports --in-place --recursive src/ tests/

# Go: goimports handles this automatically
goimports -w src/
```

### 5.2 Delete Dead Code

After API migrations, old adapter code or compatibility shims may no longer be needed:

```bash
# Search for the old API surface that should no longer have callers
grep -rn "oldApiCall\|legacyEndpoint\|deprecatedMethod" src/

# If zero results, the old code is dead — remove it
rm src/compat/legacy-api-adapter.ts
rm src/utils/deprecated-helpers.ts
```

### 5.3 Remove Redundant Type Assertions

After a type rename, explicit type assertions that cast to the old type become errors
or unnecessary casts to the new type:

```bash
# Find casts that reference the change
grep -rn "as AccountService\|<AccountService>" src/ --include="*.ts"

# Review each: is the cast still needed, or was it only there because of the old type?
```

### 5.4 Run Formatter

Ensure all changes conform to the project's formatting standards:

```bash
# Prettier
npx prettier --write src/ tests/

# Black (Python)
black src/ tests/

# gofmt
gofmt -w src/

# rustfmt
cargo fmt
```

### 5.5 Final Lint Pass

After all cleanup:

```bash
npx eslint src/ tests/ --max-warnings=0
npx tsc --noEmit
npm test
```

All three must pass before proceeding to PR creation.

---

## STEP 6: PR Strategy

Choose the right PR structure based on the size and nature of the change.

### 6.1 Single PR (Small Changes — Under 50 Files)

For straightforward renames or pattern updates affecting fewer than 50 files:

```bash
gh pr create \
  --title "refactor: rename UserService to AccountService" \
  --body "## Summary
- Renamed UserService class, file, and all references to AccountService
- Updated 18 files across controllers, middleware, tests, and documentation
- All tests passing, type checker clean

## Files Changed
- **Source**: 5 files (service, controllers, middleware)
- **Tests**: 5 files (unit, integration, e2e, fixtures)
- **Config**: 3 files (jest, tsconfig, CI)
- **Docs**: 3 files (architecture, API reference, README)

## Verification
- TypeScript: \`npx tsc --noEmit\` — clean
- Tests: \`npm test\` — 142 passed, 0 failed
- Lint: \`npx eslint\` — 0 warnings
- Zero remaining references to old name in source/test files"
```

### 6.2 Split by Module (Large Changes — 50-200 Files)

For changes spanning multiple modules or team boundaries:

```bash
# PR 1: Core service rename
gh pr create --title "refactor: rename UserService core module" \
  --body "Part 1/4 of UserService → AccountService rename. Core module only."

# PR 2: Controller layer
gh pr create --title "refactor: update controllers for AccountService rename" \
  --body "Part 2/4. Updates all controller imports and usage. Depends on PR #1."

# PR 3: Test updates
gh pr create --title "test: update tests for AccountService rename" \
  --body "Part 3/4. Renames test files and updates mocks/fixtures."

# PR 4: Documentation and config
gh pr create --title "docs: update docs for AccountService rename" \
  --body "Part 4/4. Documentation and CI config updates."
```

### 6.3 Split by Change Type (API Migrations)

For API migrations where source, tests, and docs need different review:

```
PR 1: Source code changes (needs careful code review)
PR 2: Test updates (can be reviewed by test owners)
PR 3: Documentation updates (can be reviewed by docs team)
PR 4: Config/CI changes (needs DevOps review)
```

### 6.4 PR Description Template for Batch Changes

Every batch-change PR should include:

```markdown
## Summary
<1-2 sentences: what changed and why>

## Change Pattern
<The mechanical transformation applied>
- `OldName` → `NewName`
- `oldImport` → `newImport`

## Scope
- Files changed: X
- Lines added: Y
- Lines removed: Z

## Verification
- [ ] Type checker: clean
- [ ] Full test suite: passing
- [ ] Linter: zero warnings
- [ ] Zero remaining references to old pattern
- [ ] Symbol count matches (before: N, after: N)

## Rollback
To revert this change:
`git revert <commit-hash>` (single PR)
`git revert <tag>..HEAD` (multi-PR, see rollback tags)
```

---

## STEP 7: Rollback Safety

Every batch change must be reversible. A failed migration that cannot be rolled back
is worse than no migration at all.

### 7.1 Pre-Change Tag

Before starting any batch work, create a tag:

```bash
# Tag the current state for easy rollback
git tag batch/pre-rename-userservice

# Verify the tag
git log --oneline -1 batch/pre-rename-userservice
```

### 7.2 Per-Batch Commits

Each batch gets its own commit. This enables surgical rollback of individual batches:

```bash
# Pre-work commit
git commit -m "refactor(batch 0/4): rename UserService file and class"

# Batch A commit (after merging agent worktree)
git commit -m "refactor(batch 1/4): update controllers for AccountService"

# Batch B commit
git commit -m "refactor(batch 2/4): update middleware for AccountService"

# Batch C commit
git commit -m "refactor(batch 3/4): update tests for AccountService"

# Batch D commit
git commit -m "refactor(batch 4/4): update docs for AccountService"

# Post-work commit
git commit -m "refactor(batch post): update config and CI for AccountService"
```

### 7.3 Partial Rollback

If Batch B introduced a bug but other batches are fine:

```bash
# Find the batch commit
git log --oneline --grep="batch 2/4"

# Revert only that batch
git revert <batch-2-commit-hash> --no-edit

# Re-run tests to verify the partial rollback is safe
npm test
```

### 7.4 Full Rollback

If the entire batch change needs to be undone:

```bash
# Option A: Revert to the pre-change tag
git revert batch/pre-rename-userservice..HEAD --no-edit

# Option B: Reset to the tag (destructive — only if not yet pushed)
git reset --hard batch/pre-rename-userservice

# Option C: Revert each batch commit individually (preserves history)
git log --oneline batch/pre-rename-userservice..HEAD
# Then revert each commit in reverse order
```

### 7.5 Rollback Verification

After any rollback:

```bash
# Verify no references to the new name remain (should be zero)
grep -rn "AccountService" src/ tests/ --include="*.ts" | wc -l

# Verify all references to the old name are back
grep -rn "UserService" src/ tests/ --include="*.ts" | wc -l

# Run full test suite
npm test
```

---

## STEP 8: Common Change Patterns

Real-world examples for the most frequent codebase-wide changes.

### 8.1 Rename Symbol Across Codebase

**Scenario:** Rename a function, class, variable, or file everywhere it appears.

```
Change: Rename class `UserService` → `AccountService`

Search patterns:
  - Class name: "UserService"
  - File name: "UserService" or "user-service" or "user_service"
  - Variable instances: "userService", "user_service"
  - Type annotations: ": UserService", "<UserService>"
  - Import paths: from '.*UserService' or from '.*user-service'
  - Mock/stub names: "MockUserService", "UserServiceStub"
  - Test descriptions: "UserService should..."

Batch grouping:
  1. Pre-work: Rename file, rename class definition, update barrel export
  2. Parallel: Update each consuming module independently
  3. Post-work: Update config paths, regenerate imports

Gotchas:
  - Database table names or column names that match — do NOT rename (schema migration needed separately)
  - Environment variables like USER_SERVICE_URL — coordinate with ops team
  - API response bodies that include the class name as a string — breaking change for clients
  - Third-party code or vendored dependencies — do not modify
```

### 8.2 Migrate API v1 to v2

**Scenario:** An internal or external API changed its interface. Update all callers.

```
Change: Migrate from `httpClient.get(url, callback)` → `httpClient.get(url): Promise`

Search patterns:
  - "httpClient.get(" with callback argument
  - "httpClient.post(" with callback argument
  - ".get(url, function" and ".get(url, (err"

Transformation:
  BEFORE:
    httpClient.get('/api/users', (err, response) => {
      if (err) { handleError(err); return; }
      processUsers(response.data);
    });

  AFTER:
    try {
      const response = await httpClient.get('/api/users');
      processUsers(response.data);
    } catch (err) {
      handleError(err);
    }

Batch grouping:
  1. Pre-work: Update httpClient wrapper to support both old and new API (shim)
  2. Parallel: Migrate each module's callers independently
  3. Post-work: Remove the compatibility shim, run full suite

Gotchas:
  - Functions calling httpClient must become async (cascading signature change)
  - Error handling patterns differ (callback err vs try/catch)
  - Test mocks need updating (mock callback invocation → mock Promise resolution)
  - Some callers may use the callback for streaming — different migration path
```

### 8.3 Update Dependency Usage

**Scenario:** A dependency released a new major version with API changes.

```
Change: Migrate from `moment.js` → `date-fns`

Search patterns:
  - "import moment" or "require('moment')"
  - "moment(" — constructor calls
  - ".format(" — moment-specific method
  - ".add(", ".subtract(" — moment duration methods
  - ".isValid(", ".isBefore(", ".isAfter(" — moment comparison methods

Transformation map:
  moment()                    → new Date()
  moment(dateStr)             → parseISO(dateStr)
  moment().format('YYYY-MM') → format(new Date(), 'yyyy-MM')
  moment().add(1, 'days')    → addDays(new Date(), 1)
  moment().isBefore(other)   → isBefore(date, other)

Batch grouping:
  1. Pre-work: Install date-fns, create adapter module with both APIs
  2. Parallel: Migrate each module (services, utils, components)
  3. Post-work: Remove moment from package.json, remove adapter, run suite

Gotchas:
  - Timezone handling differs significantly between moment and date-fns
  - moment objects are mutable; date-fns returns new Date objects
  - Some moment plugins (moment-timezone) need separate migration
  - Format string syntax differs ('YYYY' → 'yyyy', 'DD' → 'dd')
```

### 8.4 Apply Code Pattern (Callbacks to Async/Await)

**Scenario:** Modernize callback-based code to use async/await throughout.

```
Change: Convert callback-style functions to async/await

Search patterns:
  - "function.*callback\)" — functions accepting callbacks
  - "callback(null," — success callback invocations
  - "callback(err" — error callback invocations
  - ".then(" followed by ".catch(" — promise chains to simplify

Transformation:
  BEFORE:
    function getUser(id, callback) {
      db.query('SELECT * FROM users WHERE id = ?', [id], (err, rows) => {
        if (err) { callback(err); return; }
        callback(null, rows[0]);
      });
    }

  AFTER:
    async function getUser(id) {
      const rows = await db.query('SELECT * FROM users WHERE id = ?', [id]);
      return rows[0];
    }

Batch grouping:
  1. Pre-work: Ensure db.query returns a Promise (promisify if needed)
  2. Parallel: Convert each service file independently
  3. Post-work: Update all callers to use await instead of callbacks

Gotchas:
  - Callers of converted functions must also become async (cascading change)
  - Error handling shifts from callback(err) to try/catch
  - Some callbacks are event-style (not error-first) — different conversion pattern
  - Streams and event emitters should NOT be converted to async/await
```

### 8.5 Update Import Paths After Directory Restructure

**Scenario:** Moved files to a new directory structure, need to update all imports.

```
Change: Moved src/utils/ → src/shared/utils/ and src/helpers/ → src/shared/helpers/

Search patterns:
  - "from '../utils/" or "from '../../utils/"
  - "from '../helpers/" or "from '../../helpers/"
  - "require('./utils/" or "require('../utils/"

Transformation:
  - All imports from 'utils/' → 'shared/utils/'
  - All imports from 'helpers/' → 'shared/helpers/'
  - Relative path depth may change depending on the importing file's location

Batch grouping:
  1. Pre-work: Move directories, update tsconfig/webpack path aliases
  2. Parallel: Update imports in each top-level module directory
  3. Post-work: Verify no broken imports, run full suite

Gotchas:
  - Relative path depth changes based on the importing file's directory level
  - Path aliases in tsconfig/webpack may mask the actual import paths
  - Jest moduleNameMapper may need updating
  - Dynamic imports (import()) with string paths need manual attention
```

### 8.6 Replace Deprecated Function Calls

**Scenario:** A function is deprecated and callers must switch to the replacement.

```
Change: Replace `logger.warn()` → `logger.warning()` (aligning with Python logging levels)

Search patterns:
  - "logger.warn("
  - "log.warn("
  - ".warn(" preceded by a logger variable

Transformation:
  logger.warn("message")  → logger.warning("message")
  logger.warn("msg", ctx) → logger.warning("msg", ctx)

Batch grouping: Simple enough for a single pass — one agent per top-level directory.

Gotchas:
  - console.warn() should NOT be changed (different API)
  - Some logger.warn() calls may have different argument signatures
  - Ensure logger.warning() actually exists in the logger interface
```

### 8.7 Add/Remove Function Parameter Across All Call Sites

**Scenario:** A function signature changed — a parameter was added or removed.

```
Change: Add `options: RequestOptions` parameter to `apiClient.request(method, url)` →
        `apiClient.request(method, url, options: RequestOptions = {})`

Search patterns:
  - "apiClient.request(" — all call sites
  - "request(method, url)" — function definition and overrides
  - Mock/stub definitions that match the old signature

Transformation:
  BEFORE: apiClient.request('GET', '/users')
  AFTER:  apiClient.request('GET', '/users', {})
  OR:     apiClient.request('GET', '/users', { timeout: 5000 })

Batch grouping:
  1. Pre-work: Update function definition with default parameter value
  2. Parallel: Update call sites that need non-default options
  3. Post-work: Update type definitions, mocks, and tests

Gotchas:
  - If the new parameter has a default value, existing call sites MAY not need changes
  - Spread operators: request(...args) — the args array length changed
  - Interface/type definitions must be updated alongside the implementation
  - Overloaded functions need all overload signatures updated
```

---

## STEP 9: Dry Run Mode

Preview all changes without applying them. Essential for high-risk changes or
unfamiliar codebases.

### 9.1 Generate Preview Diffs

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

### 9.2 Batch Summary

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

### 9.3 Risk Assessment

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

### 9.4 User Confirmation

```
Dry run complete. No changes have been applied.

Options:
  1. Execute the full batch plan as shown
  2. Execute with modifications (specify which batches to skip or reorder)
  3. Abort — no changes will be made

Proceed with option [1/2/3]?
```

---

## STEP 10: Progress Tracking

Real-time visibility into batch execution status.

### 10.1 Progress Dashboard

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

### 10.2 Status Updates

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

### 10.3 Final Report

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

## MUST DO

- Always run exhaustive multi-strategy search (Step 1.1) — a single grep misses references
- Always categorize affected files (direct, transitive, tests, config, docs) before grouping batches
- Always present the batch plan for user approval before executing
- Always complete and commit pre-work before dispatching parallel agents
- Always use `isolation: "worktree"` for batch subagents — codebase-wide changes are too risky without isolation
- Always create a rollback tag before starting any batch work
- Always commit each batch independently — enables surgical rollback
- Always run the full test suite after merging all batches (Step 4.3) — batch-level tests are insufficient
- Always re-run impact analysis after completion (Step 4.4) — verify zero old references remain
- Always include a rollback section in PR descriptions
- Always track and report progress through every phase of execution
- Always flag ambiguous matches for human review rather than guessing

## MUST NOT DO

- MUST NOT execute a batch plan without user confirmation — show the plan first (Step 2.4)
- MUST NOT skip the impact analysis — changing files without a complete inventory causes silent breakage
- MUST NOT put files with shared imports into different parallel batches — they must be sequential or same-batch
- MUST NOT modify database migration files, lock files, or vendored dependencies in batch changes
- MUST NOT rename environment variables without coordinating with the operations team
- MUST NOT assume a single grep finds all references — use multiple search strategies (exact, case-insensitive, path patterns, string literals)
- MUST NOT skip the auto-simplify pass (Step 5) — dead imports and unused code accumulate after batch changes
- MUST NOT retry a failed batch more than 3 times — escalate to the user after 3 failures
- MUST NOT modify files outside the declared batch scope — each agent owns only its listed files
- MUST NOT create a single monolithic commit for batch changes — one commit per batch enables partial rollback
