---
name: request-code-review
description: >
  Create high-quality, review-optimized pull requests that surface risks, generate
  intelligent review questions, annotate diffs with intent, and help reviewers focus
  on what matters. Goes beyond basic `gh pr create` to produce PRs that get reviewed
  faster and more thoroughly.
triggers:
  - request-review
  - pr-review
  - create review pr
  - prepare for review
  - review-ready pr
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "<branch-name or description of changes to prepare for review>"
---

# Request Code Review

Prepare a review-optimized pull request for the current changes. This skill analyzes your changes, categorizes them by risk, generates targeted review questions, and produces a structured PR description that helps reviewers focus.

**Request:** $ARGUMENTS

---

## STEP 1: Assess the Change Set

Before creating the PR, understand the full scope of what changed.

### 1.1 Gather Change Data

Collect all information about the changes to be reviewed:

```bash
# Get the base branch (usually main or master)
BASE_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")

# Summary of all commits on this branch
git log --oneline "$BASE_BRANCH"..HEAD

# Full diff stats
git diff --stat "$BASE_BRANCH"...HEAD

# Full diff for analysis
git diff "$BASE_BRANCH"...HEAD

# List of changed files with change type (Added, Modified, Deleted, Renamed)
git diff --name-status "$BASE_BRANCH"...HEAD

# Check for uncommitted changes that should be included
git status
```

### 1.2 PR Size Analysis

Evaluate whether the PR is appropriately sized:

```
PR Size Assessment:
  Files changed: {count}
  Lines added:   {count}
  Lines removed: {count}
  Total delta:   {added + removed}
```

| Size Category | Lines Changed | Verdict |
|---------------|---------------|---------|
| **Small** | < 100 | Good. Easy to review. |
| **Medium** | 100 - 300 | Acceptable. Consider splitting if changes span unrelated concerns. |
| **Large** | 300 - 500 | Warning. Split if possible. Reviewers lose focus above 300 lines. |
| **Too Large** | > 500 | MUST split. Recommend splitting strategy (see 1.3). |

Research shows reviewer effectiveness drops sharply after 200-400 lines. A 2,000-line PR will get rubber-stamped, not reviewed.

### 1.3 Splitting Strategy (if PR is too large)

When the PR exceeds 500 lines, suggest concrete splits:

| Strategy | When to Use | Example |
|----------|-------------|---------|
| **By layer** | Changes span multiple layers | Split into "backend API" + "frontend UI" + "database migration" PRs |
| **By feature** | Multiple features bundled | Split each feature into its own PR |
| **By risk** | Mix of risky and mechanical changes | Split into "refactor (safe)" + "behavior change (needs review)" PRs |
| **By dependency** | Some changes depend on others | Create a chain: PR1 (base) -> PR2 (depends on PR1) -> PR3 |
| **Extract refactor** | Refactoring mixed with new logic | PR1: pure refactor (no behavior change), PR2: new logic on clean code |

Recommend the split with specific file groupings:

```
Recommended split:
  PR 1: "Refactor UserService to extract validation"
    Files: src/services/UserService.ts, src/validators/UserValidator.ts
    Lines: ~120
    Risk: Low (pure refactor, no behavior change)

  PR 2: "Add email verification flow"
    Files: src/services/EmailService.ts, src/routes/auth.ts, tests/
    Lines: ~200
    Risk: Medium (new auth flow)
    Depends on: PR 1
```

---

## STEP 2: Classify Changes by Risk Level

Categorize every changed file by the risk its changes introduce. Present high-risk changes first so reviewers allocate attention accordingly.

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
# Security-sensitive patterns in the diff
git diff "$BASE_BRANCH"...HEAD | grep -n -E "(password|secret|token|api_key|private_key|credential)" || true

# SQL injection risk
git diff "$BASE_BRANCH"...HEAD | grep -n -E "(execute|raw_sql|rawQuery|query\()" || true

# Disabled security checks
git diff "$BASE_BRANCH"...HEAD | grep -n -E "(NOAUTH|skipAuth|disable.*csrf|no.*verify|unsafe)" || true

# Hardcoded values that should be config
git diff "$BASE_BRANCH"...HEAD | grep -n -E "([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}|localhost:[0-9]+)" || true
```

---

## STEP 3: Detect Breaking Changes

Identify changes that affect consumers, downstream services, or require migration steps.

### 3.1 Breaking Change Checklist

Scan for these categories of breaking changes:

| Category | What to Check | How to Detect |
|----------|---------------|---------------|
| **Removed exports** | Functions, classes, constants removed from public API | `git diff` shows removed `export` statements |
| **Changed signatures** | Function parameters added, removed, or reordered | Compare function signatures in the diff |
| **Schema changes** | Database columns added/removed/renamed, type changes | Check migration files, ORM model changes |
| **Config format** | Changed config keys, removed options, new required fields | Diff config files, check config parsing code |
| **API response shape** | Changed JSON structure, removed fields, renamed keys | Check serializers, response builders, API routes |
| **Behavioral changes** | Same input produces different output | Check for changed conditionals, altered defaults |
| **Dependency changes** | Major version bumps, removed dependencies | Check package.json, requirements.txt, go.mod |
| **Environment variables** | New required env vars, renamed vars | Check for new `os.getenv()` / `process.env` references |

### 3.2 Breaking Change Report

```
BREAKING CHANGES DETECTED
==========================

1. [API] POST /api/v1/users response shape changed
   Before: { "user": { "id": 1, "name": "..." } }
   After:  { "data": { "id": 1, "name": "...", "role": "..." } }
   Impact: All API consumers must update response parsing
   Migration: Update client code to read from `data` instead of `user`

2. [Schema] Added NOT NULL column `role` to `users` table
   Impact: Existing rows will fail migration without a default value
   Migration: Set default value in migration, backfill existing rows

3. [Config] Renamed ENV var `DB_URL` to `DATABASE_URL`
   Impact: All deployment configs must be updated
   Migration: Update .env files, CI/CD secrets, and deployment configs

No breaking changes: [NONE DETECTED] (state this explicitly if clean)
```

---

## STEP 4: Annotate Diff with Intent

For each significant change, explain WHY it was made, not just what changed. This saves reviewers from having to reverse-engineer your reasoning.

### 4.1 Intent Annotation Format

For each high-risk and medium-risk file, provide intent annotations:

```
FILE: src/auth/TokenService.ts

Line 42-55: Changed token refresh window from 5min to 15min
  WHY: Users on slow connections were getting logged out during page loads
       because the 5min window wasn't enough time for the refresh request
       to complete. 15min matches the P99 page load time from our metrics.
  RISK: Tokens are valid longer before refresh — increases window for
        stolen token use. Acceptable because we also added token binding
        to IP in this PR.

Line 78-92: Added IP-based token binding
  WHY: Compensating control for the extended refresh window above.
       If a token is used from a different IP than it was issued to,
       force a full re-authentication.
  RISK: Users on mobile networks with changing IPs may get logged out.
        Mitigated by only checking on sensitive operations, not every request.
```

### 4.2 When to Annotate

| Change Type | Annotate? | Reason |
|-------------|-----------|--------|
| New business logic | YES | Reviewer needs to understand the requirements |
| Bug fix | YES | Explain what was broken and why this fix is correct |
| Refactor | BRIEF | "Extracted to reduce duplication" is sufficient |
| Performance optimization | YES | Explain the bottleneck and why this approach helps |
| Security change | YES + RISK | Security changes always need threat model context |
| Test changes | BRIEF | "Added coverage for edge case X" |
| Config/build changes | ONLY IF NON-OBVIOUS | "Upgraded to Node 20 for native fetch support" |
| Formatting/style | NO | Should be self-evident |

---

## STEP 5: Generate Review Questions

Create specific, actionable questions about areas where you have the least confidence. Generic "please review" wastes reviewer time.

### 5.1 Question Generation Rules

Good review questions are:
- **Specific** — Reference exact functions, lines, or decisions
- **Bounded** — Ask about one thing, not "is this okay?"
- **Contextual** — Explain what you considered and why you're unsure
- **Actionable** — The reviewer can answer without extensive research

### 5.2 Question Categories

| Category | Template | Example |
|----------|----------|---------|
| **Correctness** | "Is {approach} correct for {scenario}?" | "Is the retry logic in `OrderService.retry()` safe for concurrent requests? I'm concerned about duplicate charges if two retries execute simultaneously." |
| **Edge cases** | "What happens when {edge case}?" | "What happens when a user's session expires mid-payment? I added a check at line 85 but I'm not sure it covers the Stripe webhook race condition." |
| **Architecture** | "Is {pattern} the right approach for {goal}?" | "I used an event-driven approach for notifications instead of direct calls. Does this align with how we handle cross-service communication elsewhere?" |
| **Performance** | "Will {approach} scale for {load}?" | "The new query joins 3 tables. Is this acceptable for the /users endpoint which handles ~500 RPS, or should I denormalize?" |
| **Security** | "Does {change} introduce {risk}?" | "I'm passing the user ID in the JWT payload instead of looking it up. Does this create a privilege escalation risk if someone modifies their token?" |
| **Compatibility** | "Will {change} break {consumer}?" | "I renamed the `getData()` export to `fetchData()`. I found 3 internal consumers — are there external ones I'm missing?" |

### 5.3 Review Questions Output Format

```
REVIEW QUESTIONS
================

For: @security-team (or whoever owns auth)
  1. TokenService.ts#L78: The IP-binding check skips WebSocket connections
     because they don't carry the origin IP reliably. Is this acceptable,
     or should we enforce a different binding for WS connections?

For: @backend-team
  2. OrderService.ts#L142: The retry uses exponential backoff with jitter,
     but I'm not sure if the max retry count (3) is appropriate for payment
     operations. Our Stripe webhook has a 30s timeout — could 3 retries
     with backoff exceed that?

For: @dba / database owner
  3. Migration 0042: I added a `role` column with DEFAULT 'user'. The users
     table has ~2M rows. Will this lock the table during migration in
     Postgres, or does Postgres handle ADD COLUMN with DEFAULT without a
     full table rewrite?
```

---

## STEP 6: Pre-Review Self-Check

Before requesting review, verify the branch is clean and professional. Sloppy PRs waste reviewer time and erode trust.

### 6.1 Code Hygiene Checklist

Run these checks before creating the PR:

```bash
# Check for debug/development artifacts in the diff
echo "=== Debug Code Check ==="
git diff "$BASE_BRANCH"...HEAD | grep -n -E "(console\.log|print\(|debugger|binding\.pry|pdb\.set_trace|var_dump|dd\()" || echo "Clean: no debug statements found"

# Check for TODO/FIXME without ticket references
echo "=== Untracked TODOs ==="
git diff "$BASE_BRANCH"...HEAD | grep -n -E "(TODO|FIXME|HACK|XXX)" | grep -v -E "(TODO\(#[0-9]+\)|TODO\([A-Z]+-[0-9]+\))" || echo "Clean: all TODOs have ticket references"

# Check for commented-out code (more than 2 consecutive commented lines)
echo "=== Commented-out Code ==="
git diff "$BASE_BRANCH"...HEAD | grep -n "^+" | grep -E "^\+\s*(//|#|/\*|\*)" | head -20

# Check for merge conflict markers
echo "=== Merge Conflicts ==="
git diff "$BASE_BRANCH"...HEAD | grep -n -E "^(<<<<<<<|=======|>>>>>>>)" || echo "Clean: no conflict markers"

# Check for large files accidentally added
echo "=== Large Files ==="
git diff --stat "$BASE_BRANCH"...HEAD | grep -E "\+[0-9]{4,}" || echo "Clean: no unusually large files"

# Check for sensitive data patterns
echo "=== Sensitive Data ==="
git diff "$BASE_BRANCH"...HEAD | grep -n -i -E "(password\s*=|api_key\s*=|secret\s*=|-----BEGIN)" || echo "Clean: no sensitive data patterns"
```

### 6.2 Hygiene Violations Response

| Finding | Action |
|---------|--------|
| Debug statements | Remove ALL debug code before requesting review |
| TODOs without tickets | Either create tickets and reference them, or remove the TODO |
| Commented-out code | Delete it. Version control is the backup. |
| Merge conflict markers | Resolve conflicts before creating PR |
| Large binary files | Add to `.gitignore`, use Git LFS, or confirm intentional |
| Sensitive data | Remove immediately. Rotate any exposed credentials. Consider `git filter-branch` if already committed. |

### 6.3 Branch Hygiene

```bash
# Ensure branch is rebased on latest base
git fetch origin "$BASE_BRANCH"
git log --oneline "origin/$BASE_BRANCH"..HEAD  # Your commits
git log --oneline "HEAD..origin/$BASE_BRANCH"  # Commits you're missing

# Check commit messages are clean
git log --oneline "$BASE_BRANCH"..HEAD
```

| Issue | Action |
|-------|--------|
| Branch is behind base | Rebase: `git rebase origin/$BASE_BRANCH` |
| Messy commit history | Consider interactive rebase to squash fixup commits |
| Unclear commit messages | Each commit message should be meaningful on its own |

---

## STEP 7: Suggest Reviewers

Identify the best reviewers based on code ownership and recent activity.

### 7.1 Reviewer Selection Data

```bash
# Check CODEOWNERS for explicit ownership
cat .github/CODEOWNERS 2>/dev/null || cat CODEOWNERS 2>/dev/null || echo "No CODEOWNERS file found"

# Find who has recently modified the changed files
for file in $(git diff --name-only "$BASE_BRANCH"...HEAD); do
  echo "=== $file ==="
  git log --format="%an" -5 -- "$file" 2>/dev/null | sort | uniq -c | sort -rn | head -3
done

# Find who reviewed recent PRs in the same area (if gh CLI available)
# gh pr list --state merged --limit 10 --json author,reviewedBy,files
```

### 7.2 Reviewer Selection Logic

| Priority | Criterion | Rationale |
|----------|-----------|-----------|
| 1 | CODEOWNERS match | Explicit ownership — they are responsible for this area |
| 2 | Most recent commits to changed files | Fresh context — they know the current state of the code |
| 3 | Original author of changed code (git blame) | Historical context — they know WHY the code was written that way |
| 4 | Domain expert (auth, payments, infra) | Domain expertise for high-risk changes |
| 5 | Available team member | Practical — someone who can review promptly |

### 7.3 Reviewer Assignment Output

```
SUGGESTED REVIEWERS
===================

Required (CODEOWNERS):
  @alice — owns src/auth/ (high-risk changes)

Recommended:
  @bob — last 3 commits to OrderService.ts, has fresh context
  @carol — original author of TokenService.ts (git blame), knows the design intent

Optional:
  @dave — DBA, can validate migration 0042 performance impact

Review load check:
  @alice — 2 open review requests (OK)
  @bob — 5 open review requests (BUSY — consider @eve as alternative)
```

---

## STEP 8: Generate PR Description

Produce a structured, comprehensive PR description that enables efficient review.

### 8.1 PR Description Template

Use this template, filling in all sections that apply:

```markdown
## Summary

- {1-3 bullet points describing what this PR does at a high level}

## Motivation / Context

{Why is this change needed? Link to issue/ticket if applicable.}
{What problem does it solve? What was the user-facing impact of the bug or missing feature?}

## Changes by Risk Level

### High Risk (review carefully)
| File | Change | Why |
|------|--------|-----|
| `src/auth/TokenService.ts` | Extended refresh window, added IP binding | Users on slow connections were getting logged out |
| `migrations/0042_add_roles.sql` | New `role` column on users table | Needed for RBAC feature |

### Medium Risk
| File | Change | Why |
|------|--------|-----|
| `src/services/OrderService.ts` | Added retry with exponential backoff | Payment timeouts were causing failed orders |

### Low Risk (skim or skip)
| File | Change | Why |
|------|--------|-----|
| `tests/auth/token.test.ts` | New tests for token refresh | Coverage for high-risk changes above |
| `docs/api/authentication.md` | Updated token endpoint docs | Reflects new refresh behavior |

## Breaking Changes

{List any breaking changes with migration steps, or state "None"}

## Review Questions

1. **@alice**: Is IP-binding sufficient as a compensating control for the
   extended token refresh window? (TokenService.ts#L78)
2. **@bob**: Is 3 retries with exponential backoff appropriate for Stripe
   payment operations? (OrderService.ts#L142)

## Testing

- [ ] Unit tests for token refresh edge cases (added)
- [ ] Integration test for IP-binding enforcement (added)
- [ ] Manual test: slow connection simulation with Chrome DevTools throttling
- [ ] Load test: verified retry logic under 100 concurrent payment requests

## Screenshots / Recordings

{If UI changes, include before/after screenshots. If CLI/API changes, include example output.}

## Migration Steps

{If breaking changes exist, provide step-by-step migration instructions:}
1. Deploy the migration: `python manage.py migrate`
2. Update environment variable: rename `DB_URL` to `DATABASE_URL`
3. Restart all services

## Rollback Plan

{For high-risk changes, describe how to revert if something goes wrong:}
1. Revert this PR's merge commit: `git revert <sha>`
2. Run rollback migration: `python manage.py migrate 0041`
3. Restore original env var name in deployment config

## Checklist

- [ ] Tests pass locally
- [ ] No debug code (console.log, print, debugger)
- [ ] No TODOs without ticket references
- [ ] Documentation updated (if applicable)
- [ ] Migration tested against production-like data
- [ ] Rollback plan verified
```

### 8.2 PR Title Guidelines

| Pattern | Example | When to Use |
|---------|---------|-------------|
| `feat: {description}` | `feat: add role-based access control` | New feature |
| `fix: {description}` | `fix: prevent duplicate charges on retry` | Bug fix |
| `refactor: {description}` | `refactor: extract validation from UserService` | Pure refactor |
| `perf: {description}` | `perf: add index for users.email lookup` | Performance improvement |
| `security: {description}` | `security: add IP-binding for token refresh` | Security change |
| `breaking: {description}` | `breaking: rename /api/v1/users response shape` | Breaking API change |

Rules:
- Keep under 70 characters
- Use imperative mood ("add", not "added" or "adding")
- Do not end with a period
- Include the scope if the repo uses scoped commits: `feat(auth): add token binding`

---

## STEP 9: Create the Pull Request

Execute the PR creation with all gathered information.

### 9.1 Build and Submit the PR

```bash
# Ensure we're on the feature branch and it's pushed
CURRENT_BRANCH=$(git branch --show-current)
git push -u origin "$CURRENT_BRANCH"

# Create the PR using gh CLI
gh pr create \
  --title "{generated title}" \
  --body "{generated body from template}" \
  --reviewer "{suggested reviewers}" \
  --label "{appropriate labels}" \
  --assignee "@me"
```

### 9.2 Post-Creation Steps

After creating the PR:

1. **Add inline comments** on the PR diff for complex changes that need per-line explanation
2. **Link related issues** using `Closes #123` or `Relates to #456` in the description
3. **Set labels** for the PR type (bug, feature, breaking-change, security)
4. **Request review** from the suggested reviewers identified in Step 7

```bash
# Add labels (if not set during creation)
gh pr edit --add-label "type:feature,risk:high,needs:security-review"

# Link to issue
gh pr edit --body "$(gh pr view --json body -q .body)

Closes #123"
```

---

## STEP 10: Dependency and Impact Analysis

Check if changes affect shared code that other modules depend on.

### 10.1 Identify Shared Code Changes

```bash
# Find all changed files that are imported by other modules
for file in $(git diff --name-only "$BASE_BRANCH"...HEAD); do
  # Count how many other files import this one
  basename=$(basename "$file" | sed 's/\.[^.]*$//')
  import_count=$(grep -rl "$basename" --include="*.ts" --include="*.js" --include="*.py" --include="*.go" --include="*.java" . 2>/dev/null | grep -v "$file" | grep -v node_modules | grep -v __pycache__ | wc -l)
  if [ "$import_count" -gt 2 ]; then
    echo "SHARED: $file is imported by $import_count other files"
  fi
done
```

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

### 10.3 Cross-Service Impact

For changes that might affect other services or deployments:

```
CROSS-SERVICE IMPACT
====================

API contract changes:
  POST /api/v1/users — response shape changed (see Breaking Changes)
  Consumers:
    - Mobile app (v3.2+) — uses this endpoint for registration
    - Admin dashboard — uses this endpoint for user management
    - Partner API integration — uses this endpoint via API gateway

  Action required:
    - Coordinate with mobile team for app update
    - Update API gateway response transformation
    - Notify partner integrations 2 weeks before deployment
```

---

## Review Readiness Summary

After completing all steps, produce a final summary:

```
PR REVIEW READINESS REPORT
============================

PR: feat(auth): add role-based access control with token binding
Branch: feature/rbac-token-binding -> main

Size: 342 lines changed (Medium)
Risk: HIGH (auth changes, schema migration)

Files by risk:
  HIGH:   3 files (src/auth/*, migrations/*)
  MEDIUM: 2 files (src/services/*)
  LOW:    4 files (tests/*, docs/*)

Breaking changes: 2 detected (API response shape, new env var)
Review questions: 3 targeted questions for specific reviewers
Pre-review checks: ALL PASSED
  [PASS] No debug code
  [PASS] No untracked TODOs
  [PASS] No commented-out code
  [PASS] No merge conflicts
  [PASS] No sensitive data
  [PASS] Branch rebased on latest main

Suggested reviewers:
  Required: @alice (CODEOWNERS: src/auth/)
  Recommended: @bob (recent context), @carol (original author)
  Optional: @dave (DBA for migration review)

Estimated review time: 25-35 minutes

PR created: https://github.com/org/repo/pull/456
```

---

## MUST DO

- Always classify changes by risk level — reviewers need to know where to focus
- Always run the pre-review self-check — debug code in PRs wastes everyone's time
- Always generate specific review questions — "please review" is not a question
- Always check for breaking changes — undocumented breaking changes cause incidents
- Always explain WHY for high-risk changes — the diff shows WHAT, you must provide WHY
- Always check PR size and recommend splits above 500 lines
- Always check for shared code impact — changes to utilities affect many consumers
- Always include a testing section — reviewers need to know what was and wasn't tested
- Always include a rollback plan for high-risk changes — things go wrong in production
- Always push the branch and verify CI passes before requesting review

## MUST NOT DO

- MUST NOT create PRs with debug code (console.log, print, debugger, pdb) — remove ALL debug statements before review
- MUST NOT leave TODOs without ticket references — either create a ticket or remove the TODO
- MUST NOT include commented-out code — delete it, version control is your backup
- MUST NOT write generic review questions like "please review" or "LGTM?" — be specific about what you want reviewed
- MUST NOT skip the breaking change check — undocumented breaking changes are a top cause of production incidents
- MUST NOT submit PRs that are behind the base branch — rebase first to avoid merge conflicts during review
- MUST NOT assign reviewers who are overloaded — check their open review count and suggest alternatives
- MUST NOT bundle unrelated changes in one PR — split by concern, risk level, or feature
- MUST NOT skip the risk classification — a flat file list gives reviewers no signal about where to spend time
- MUST NOT omit migration or rollback steps for breaking changes — reviewers and deployers need this information
