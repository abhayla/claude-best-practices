# 1.2 Categorize Affected Files

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

