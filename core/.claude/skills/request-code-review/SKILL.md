---
name: request-code-review
description: >
  Create high-quality, review-optimized pull requests that surface risks, generate
  intelligent review questions, annotate diffs with intent, and help reviewers focus
  on what matters. Use when preparing a PR for review to ensure it gets reviewed
  faster and more thoroughly.
triggers:
  - request code review
  - create review pr
  - review-ready pr
  - submit for review
  - need code review
  - open pull request for review
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "<branch-name or description of changes to prepare for review>"
version: "1.1.0"
type: workflow
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

## STEP 2: Classify Changes by Risk Level

Categorize every changed file by the risk its changes introduce. Present high-risk changes first so reviewers allocate attention accordingly.


**Read:** `references/classify-changes-by-risk-level.md` for detailed step 2: classify changes by risk level reference material.

### 2.2 Security Pattern Scan

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


**Read:** `references/detect-breaking-changes.md` for detailed step 3: detect breaking changes reference material.

## STEP 4: Annotate Diff with Intent

For each significant change, explain WHY it was made, not just what changed. This saves reviewers from having to reverse-engineer your reasoning.


**Read:** `references/annotate-diff-with-intent.md` for detailed step 4: annotate diff with intent reference material.

## STEP 5: Generate Review Questions

Create specific, actionable questions about areas where you have the least confidence. Generic "please review" wastes reviewer time.


**Read:** `references/generate-review-questions.md` for detailed step 5: generate review questions reference material.

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

### 9.1 Verify Prerequisites

```bash
# Verify gh CLI is available
if ! command -v gh &>/dev/null; then
  echo "ERROR: gh CLI not found. Install from https://cli.github.com/"
  echo "Falling back to manual PR creation — printing PR body to stdout."
fi

# Verify gh is authenticated
gh auth status 2>/dev/null || echo "WARNING: gh not authenticated. Run: gh auth login"
```

If `gh` is not available, print the generated PR title, body, and suggested reviewers to stdout so the user can create the PR manually.

### 9.2 Build and Submit the PR

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

### 9.3 Post-Creation Steps

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

### 10.2 Cross-Service Impact

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
