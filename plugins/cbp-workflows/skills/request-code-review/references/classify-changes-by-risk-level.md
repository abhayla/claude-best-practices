# STEP 2: Classify Changes by Risk Level

### 2.1 Risk Classification Rules

| Risk Level | Criteria | Examples |
|------------|----------|----------|
| **HIGH** | Authentication, authorization, payments, data migrations, security, cryptography, PII handling, rate limiting, session management | Changes to `auth/`, `payments/`, `migrations/`, `security/`, `middleware/auth*` |
| **HIGH** | Breaking changes to public APIs, shared interfaces, database schemas | Removed exports, changed function signatures, altered column types |
| **HIGH** | Concurrency, distributed state, cache invalidation | Mutex changes, distributed locks, cache TTL changes |
| **MEDIUM** | Core business logic, data transformations, state management | Service layer changes, reducers, data pipelines |
| **MEDIUM** | Error handling, retry logic, fallback behavior | Catch blocks, circuit breakers, timeout values |
| **MEDIUM** | Third-party integrations, external API calls | New SDK usage, webhook handlers, API client changes |
| **LOW** | Tests, documentation, comments | Test files, README, JSDoc/docstrings |
| **LOW** | Configuration, build, CI/CD (non-security) | package.json deps, Dockerfile, workflow YAML |
| **LOW** | Code style, formatting, renaming | Linter fixes, variable renames, import reordering |

### 2.2 Risk Report Format

Produce a risk-categorized file list:

```
CHANGE RISK ASSESSMENT
======================

HIGH RISK (review carefully):
  [M] src/auth/TokenService.ts        (+45, -12)  — Changed token refresh logic
  [M] migrations/0042_add_roles.sql    (+28, -0)   — New database migration
  [M] src/middleware/rateLimit.ts       (+15, -8)   — Modified rate limit thresholds

MEDIUM RISK (review normally):
  [M] src/services/OrderService.ts     (+62, -20)  — Added retry logic for payments
  [A] src/services/NotificationSvc.ts  (+85, -0)   — New notification service

LOW RISK (skim or skip):
  [M] tests/auth/token.test.ts         (+120, -5)  — New tests for token refresh
  [M] docs/api/authentication.md       (+25, -10)  — Updated API docs
  [M] .eslintrc.json                   (+2, -1)    — Added new lint rule

Summary: 3 high-risk, 2 medium-risk, 3 low-risk files
Estimated review time: 25-35 minutes
```

### 2.3 Automatic High-Risk Detection Patterns

Scan the diff for these high-risk patterns and flag them explicitly:

```bash
