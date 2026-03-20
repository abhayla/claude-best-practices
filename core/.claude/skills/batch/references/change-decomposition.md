# STEP 2: Change Decomposition

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

