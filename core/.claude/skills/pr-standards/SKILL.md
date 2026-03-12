---
name: pr-standards
description: >
  Proactively enforce team standards against PR diffs before requesting human review.
  Extracts changed lines, checks them against project rules and custom standards,
  categorizes violations by severity, generates auto-fixes where possible, and produces
  a structured standards report. Sits between /implement and /request-code-review in
  the development pipeline.
triggers:
  - pr-standards
  - standards-check
  - pr-lint
  - check standards
  - enforce standards
  - pre-review check
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "[PR-number] [--fix] [--strict] [--rules-file <path>]"
---

# PR Standards Check

Enforce team standards against the current PR diff before requesting human review. This skill analyzes only changed lines, checks them against project rules and custom standards, categorizes violations by severity, offers auto-fixes, and produces a structured report.

**Request:** $ARGUMENTS

---

## STEP 0: Parse Arguments and Determine Mode

Determine how to extract the diff and which options are active.

### 0.1 Argument Parsing

| Argument | Effect |
|----------|--------|
| `<PR-number>` | Use `gh pr diff <number>` to get the diff from an existing PR |
| `--fix` | Automatically apply all auto-fixable violations (with confirmation) |
| `--strict` | Treat warnings as critical — all violations must be fixed |
| `--rules-file <path>` | Load custom rules from the specified YAML file |
| *(no arguments)* | Use `git diff main...HEAD` for the current branch diff |

### 0.2 Determine Diff Source

```bash
# If PR number provided:
gh pr diff $PR_NUMBER

# If no PR number — use branch diff against base:
BASE_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")
git diff "$BASE_BRANCH"...HEAD
```

### 0.3 Validate Preconditions

Before proceeding, verify the environment is ready:

```bash
# Ensure we are on a feature branch, not main
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
  echo "ERROR: You are on $CURRENT_BRANCH. Switch to a feature branch first."
  exit 1
fi

# Ensure there is a diff to analyze
DIFF_LINES=$(git diff "$BASE_BRANCH"...HEAD | wc -l)
if [ "$DIFF_LINES" -eq 0 ]; then
  echo "No changes detected between $CURRENT_BRANCH and $BASE_BRANCH. Nothing to check."
  exit 0
fi

# Show summary of what will be analyzed
git diff --stat "$BASE_BRANCH"...HEAD
```

---

## STEP 1: Extract and Parse the PR Diff

Get only the changed lines for analysis. Focus analysis on what was actually modified — never scan entire files unless they are new.

### 1.1 Collect Changed Files

```bash
BASE_BRANCH=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | sed 's@^refs/remotes/origin/@@' || echo "main")

# Get changed files with change type
git diff --name-status "$BASE_BRANCH"...HEAD
```

Categorize each file by its change type:

| Status | Meaning | Analysis Scope |
|--------|---------|----------------|
| `A` | Added (new file) | Check full file against all standards |
| `M` | Modified | Check only changed lines + 3 lines of surrounding context |
| `D` | Deleted | Verify no dangling references in other changed files |
| `R` | Renamed/moved | Verify imports updated in other changed files; skip content check |
| `C` | Copied | Check full file (same as Added) |

### 1.2 Extract Changed Lines Per File

For each modified file, extract only the added and changed lines with their line numbers:

```bash
# Get per-file diffs with line numbers
for file in $(git diff --name-only "$BASE_BRANCH"...HEAD); do
  echo "=== $file ==="
  # Show added lines with line numbers (lines starting with +, excluding +++ header)
  git diff "$BASE_BRANCH"...HEAD -- "$file" | grep -n "^+" | grep -v "^[0-9]*:+++" || true
done
```

### 1.3 Build the Analysis Manifest

Construct a manifest of what to analyze:

```
ANALYSIS MANIFEST
=================

New files (full scan):
  src/services/UserService.py (245 lines)
  src/models/Role.py (89 lines)

Modified files (changed lines only):
  src/routes/users.py (+45, -12) — 45 added lines to check
  src/middleware/auth.py (+8, -3) — 8 added lines to check
  tests/test_users.py (+120, -5) — 120 added lines to check

Deleted files (reference check):
  src/utils/old_validator.py — check for dangling imports

Renamed files (import check):
  src/helpers/format.py -> src/utils/format.py — verify imports updated

Total lines to analyze: 507 (added/changed only)
```

---

## STEP 2: Load Standards and Rules

Load all applicable rules from project configuration and custom definitions.

### 2.1 Rule Sources (Priority Order)

Load rules from these sources, with later sources overriding earlier ones:

| Priority | Source | Description |
|----------|--------|-------------|
| 1 (lowest) | Built-in defaults | Sensible defaults that apply to any project (see Step 3) |
| 2 | `.claude/rules/` | Project rules files — all `.md` files in the rules directory |
| 3 | `CLAUDE.md` | Project-level conventions and standards |
| 4 | `.pr-standards.yml` | Custom team rules (see Step 2.3) |
| 5 (highest) | `--rules-file` flag | Explicit override file from CLI argument |

```bash
# Check for project rules
ls .claude/rules/*.md 2>/dev/null || echo "No .claude/rules/ found"

# Check for CLAUDE.md
cat CLAUDE.md 2>/dev/null | head -50 || echo "No CLAUDE.md found"

# Check for custom standards file
cat .pr-standards.yml 2>/dev/null || echo "No .pr-standards.yml found — using defaults"
```

### 2.2 Parse Project Rules

Read each rule file in `.claude/rules/` and extract actionable constraints:

1. Scan for RFC 2119 keywords: MUST, MUST NOT, NEVER, ALWAYS, SHOULD
2. Extract patterns that can be checked against code (naming conventions, required patterns, forbidden patterns)
3. Note any file-scoped rules (rules with `globs:` frontmatter that apply only to specific paths)

### 2.3 Custom Rule Definition Format

Users define team-specific rules in `.pr-standards.yml`:

```yaml
# .pr-standards.yml — Team-specific PR standards
version: 1

settings:
  fail-on-warning: false          # Set to true to treat warnings as critical
  max-violations: 50              # Stop scanning after this many violations
  exclude-paths:                  # Paths to skip entirely
    - "vendor/"
    - "generated/"
    - "*.min.js"
    - "*.lock"
  exclude-rules: []               # Rule names to disable

rules:
  # Custom rule with regex pattern
  - name: rate-limiting-required
    description: All API endpoints must have rate limiting
    severity: critical
    languages: [python]
    pattern: "@app\\.route|@router\\.(get|post|put|delete|patch)"
    check: "Verify rate_limit decorator exists on the same function"
    auto-fix: false
    message: "API endpoint missing rate limiting. Add @rate_limit decorator."

  # Custom rule with simple string match
  - name: no-raw-sql
    description: No raw SQL queries — use the ORM
    severity: warning
    pattern: "execute.*(?:SELECT|INSERT|UPDATE|DELETE)"
    auto-fix: false
    message: "Raw SQL detected. Use ORM query methods instead."

  # Custom rule with auto-fix
  - name: no-print-statements
    description: No print() calls in production code
    severity: warning
    languages: [python]
    pattern: "^\\s*print\\("
    exclude-paths: ["tests/", "scripts/"]
    auto-fix: true
    fix-pattern: "print("
    fix-replacement: "logger.debug("
    message: "Use logger instead of print()."

  # Custom rule checking for required content
  - name: docstring-required
    description: Public functions must have docstrings
    severity: info
    languages: [python]
    pattern: "^\\s*def [a-z]\\w*\\(.*\\):$"
    check: "Next non-blank line should be a docstring (triple quotes)"
    auto-fix: false
    message: "Public function missing docstring."

  # Custom rule with context-aware check
  - name: error-handling-required
    description: External API calls must have error handling
    severity: critical
    pattern: "requests\\.(get|post|put|delete|patch)\\("
    check: "Call must be inside a try/except block"
    auto-fix: false
    message: "External API call without error handling. Wrap in try/except."
```

### 2.4 Rule Schema

Each rule (custom or built-in) has these fields:

| Field | Required | Type | Description |
|-------|----------|------|-------------|
| `name` | Yes | string | Unique rule identifier (kebab-case) |
| `description` | Yes | string | Human-readable explanation |
| `severity` | Yes | `critical` / `warning` / `info` | Violation severity level |
| `pattern` | Yes | regex string | Pattern to search for in changed lines |
| `check` | No | string | Additional context-aware check to perform |
| `auto-fix` | No | boolean | Whether this violation can be auto-fixed |
| `fix-pattern` | No | string | Regex pattern to match for replacement (required if auto-fix) |
| `fix-replacement` | No | string | Replacement text (required if auto-fix) |
| `languages` | No | list | Limit rule to specific file extensions |
| `exclude-paths` | No | list | Paths where this rule does not apply |
| `message` | Yes | string | Message shown when violation is detected |

---

## STEP 3: Built-in Default Rules

These rules apply when no `.pr-standards.yml` exists, or alongside custom rules unless explicitly excluded. They represent universally applicable code hygiene standards.

### 3.1 Debug and Development Artifacts

| Rule | Severity | Pattern | Auto-fix |
|------|----------|---------|----------|
| `no-console-log` | Warning | `console\.log\(` | Yes: remove line |
| `no-print-debug` | Warning | `^\s*print\(` (in non-test Python files) | Yes: replace with `logger.debug(` |
| `no-debugger` | Critical | `debugger;` or `debugger\b` | Yes: remove line |
| `no-pdb` | Critical | `pdb\.set_trace\(\)` or `breakpoint\(\)` | Yes: remove line |
| `no-binding-pry` | Critical | `binding\.pry` | Yes: remove line |
| `no-var-dump` | Warning | `var_dump\(` or `dd\(` | Yes: remove line |

### 3.2 Code Quality

| Rule | Severity | Pattern | Auto-fix |
|------|----------|---------|----------|
| `no-todo-without-ticket` | Warning | `TODO\|FIXME\|HACK\|XXX` without `(#\d+)` or `([A-Z]+-\d+)` | No |
| `no-commented-code` | Info | 3+ consecutive commented-out lines that look like code | No |
| `no-magic-numbers` | Info | Numeric literals > 1 in logic (excluding 0, 1, common HTTP codes) | No |
| `no-empty-catch` | Warning | `catch.*\{[\s]*\}` or `except.*:[\s]*pass` | No |
| `no-swallowed-errors` | Warning | Catch/except blocks without logging or re-raising | No |

### 3.3 Security

| Rule | Severity | Pattern | Auto-fix |
|------|----------|---------|----------|
| `no-hardcoded-secrets` | Critical | `(api_key\|password\|secret\|token\|private_key)\s*=\s*["'][^"']+["']` | No |
| `no-hardcoded-ip` | Warning | `\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}` (not in tests/config) | No |
| `no-eval` | Critical | `eval\(` (in JS/Python) | No |
| `no-inner-html` | Warning | `innerHTML\s*=` or `dangerouslySetInnerHTML` | No |
| `no-sql-injection` | Critical | String concatenation/interpolation in SQL queries | No |
| `no-disabled-security` | Critical | `verify=False`, `checkServerIdentity: null`, `rejectUnauthorized: false` | No |

### 3.4 Test Coverage

| Rule | Severity | Pattern | Auto-fix |
|------|----------|---------|----------|
| `new-function-needs-test` | Warning | New `def`/`function`/`func` declaration in non-test file without corresponding test | No |
| `new-endpoint-needs-test` | Warning | New route/endpoint without corresponding test | No |
| `no-skip-test` | Info | `@skip`, `@ignore`, `xit(`, `xdescribe(`, `test.skip(` without issue reference | No |

### 3.5 Import and Dependency Hygiene

| Rule | Severity | Pattern | Auto-fix |
|------|----------|---------|----------|
| `no-wildcard-import` | Warning | `from X import *` or `import * from` | No |
| `no-relative-parent-import` | Info | `from ../../` deep relative imports (3+ levels) | No |
| `no-unused-import` | Info | Import statement where the imported name does not appear in the file | No |

---

## STEP 4: Run Standards Engine

Execute each rule against the extracted diff. Only check changed lines (plus surrounding context for context-aware rules).

### 4.1 Execution Strategy

For each changed file in the analysis manifest:

1. **Determine applicable rules** — filter by language, exclude-paths, and file change type
2. **For new files (status `A`)** — run all applicable rules against the full file content
3. **For modified files (status `M`)** — run rules only against added/changed lines
4. **For deleted files (status `D`)** — run only reference-check rules (dangling imports)
5. **For renamed files (status `R`)** — run only import-update checks

### 4.2 Rule Execution

For each applicable rule against each file:

```bash
# Example: Check for debug statements in changed lines of a specific file
git diff "$BASE_BRANCH"...HEAD -- "$FILE" | grep -n "^+" | grep -v "^[0-9]*:+++" | grep -E "$PATTERN"
```

### 4.3 Context-Aware Checks

Some rules require understanding the surrounding code, not just individual lines:

| Check Type | Method |
|------------|--------|
| "Must be inside try/except" | Read the full function containing the matched line; verify enclosing block |
| "Must have decorator" | Check the 5 lines preceding the matched function definition |
| "Must have corresponding test" | Search test files for a function name matching the new function |
| "Must log or re-raise" | Check the body of the catch/except block for logger calls or raise statements |
| "Next line should be docstring" | Read the line immediately following the function definition |

For context-aware checks:

```bash
# Read surrounding context for a matched line
# Get the actual line number in the file (not the diff line number)
git diff "$BASE_BRANCH"...HEAD -- "$FILE" | grep -B3 -A10 "$MATCHED_LINE"

# Or read the file directly for full context
sed -n "${LINE_START},${LINE_END}p" "$FILE"
```

### 4.4 Violation Deduplication

Before recording a violation, check:

1. **Same rule, same line** — keep only one instance
2. **Same rule, adjacent lines (within 3 lines)** — group into a single violation with a range
3. **Rule superseded by a stricter rule** — if `no-hardcoded-secrets` (critical) and `no-magic-numbers` (info) both match the same line, report only the critical violation

### 4.5 Track Violations

Maintain a structured list of all violations found:

```
violation:
  id: V001
  rule: no-debugger
  severity: critical
  file: src/routes/users.py
  line: 45
  column: 5
  matched_text: "    debugger"
  message: "Debugger statement found. Remove before merging."
  auto_fixable: true
  fix_description: "Remove the debugger line"
  context:
    before: "    user = get_user(user_id)"
    matched: "    debugger"
    after: "    return jsonify(user)"
```

---

## STEP 5: Classify Violations by Severity

Categorize every violation and determine the overall PR verdict.

### 5.1 Severity Definitions

| Severity | Icon | Action Required | Blocks PR | Examples |
|----------|------|----------------|-----------|----------|
| **Critical** | `[C]` | MUST fix before merge | Yes | Security vulnerability, debugger statement, hardcoded secret, broken API contract, disabled security check |
| **Warning** | `[W]` | Should fix, flag to author | Only in `--strict` mode | Missing error handling, no test for new function, TODO without ticket, debug print statement |
| **Info** | `[I]` | Optional improvement | No | Naming suggestion, missing docstring, magic number, deep relative import |

### 5.2 PR Verdict Logic

```
IF critical_count > 0:
  verdict = "FAIL"
  message = "PR has {critical_count} critical violation(s) that must be fixed."
ELIF strict_mode AND warning_count > 0:
  verdict = "FAIL"
  message = "Strict mode: PR has {warning_count} warning(s) that must be fixed."
ELIF warning_count > 10:
  verdict = "WARN"
  message = "PR has many warnings ({warning_count}). Consider addressing before review."
ELSE:
  verdict = "PASS"
  message = "PR meets team standards."
```

### 5.3 Violation Summary

```
VIOLATION SUMMARY
=================

Critical: {count} — MUST fix before merge
Warning:  {count} — Should fix before review
Info:     {count} — Optional improvements

Auto-fixable: {count} of {total} violations
```

---

## STEP 6: Generate Auto-Fixes

For each violation marked as auto-fixable, generate a concrete code fix.

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
# Apply each accepted fix using sed or direct file editing
# Track which fixes were applied vs. skipped

# After applying all fixes, verify the code still works:
# 1. Check syntax (language-specific)
# 2. Run linter if configured
# 3. Run tests if quick (<30 seconds)
```

### 6.4 Fix Tracking

```
AUTO-FIX RESULTS
================

Applied: 2 fixes
  [C] Removed debugger statement (src/routes/users.py:45)
  [W] Removed console.log (src/components/UserForm.tsx:112)

Skipped: 1 fix
  [W] print -> logger replacement requires import setup (src/services/user_service.py:23)

Remaining violations after auto-fix: {count}
```

---

## STEP 7: Generate Standards Report

Produce the full structured report for the user.

### 7.1 Report Format

```
=========================================
  PR STANDARDS CHECK: {PASS / FAIL / WARN}
=========================================

Branch: {current_branch} -> {base_branch}
Files analyzed: {count}
Lines analyzed: {count} (changed lines only)
Rules applied: {count} ({built_in_count} built-in + {custom_count} custom)

-----------------------------------------
  CRITICAL (must fix before merge): {count}
-----------------------------------------

[C1] no-debugger — Debugger statement found
     File: src/routes/users.py, line 45
     Code: `    debugger`
     Fix:  Remove the debugger line (auto-fixable)

[C2] no-hardcoded-secrets — Hardcoded API key detected
     File: src/services/payment.py, line 12
     Code: `    api_key = "sk_live_abc123def456"`
     Fix:  Move to environment variable. Use `os.getenv("STRIPE_API_KEY")`

[C3] rate-limiting-required — API endpoint missing rate limiting
     File: src/routes/users.py, line 30
     Code: `@router.post("/api/users")`
     Fix:  Add `@rate_limit(max=100, per=60)` decorator before route handler

-----------------------------------------
  WARNING (should fix): {count}
-----------------------------------------

[W1] new-function-needs-test — New function has no tests
     File: src/services/user_service.py, line 23
     Code: `def create_user(email: str, role: str) -> User:`
     Fix:  Add test in tests/test_user_service.py for create_user()

[W2] no-swallowed-errors — Error silently swallowed in catch block
     File: src/routes/users.py, line 67
     Code: `    except Exception: pass`
     Fix:  Log the error or re-raise: `except Exception as e: logger.error(f"Failed: {e}"); raise`

[W3] no-todo-without-ticket — TODO without issue reference
     File: src/services/user_service.py, line 45
     Code: `    # TODO: add email validation`
     Fix:  Create an issue and reference it: `# TODO(#123): add email validation`

-----------------------------------------
  INFO (optional improvements): {count}
-----------------------------------------

[I1] no-magic-numbers — Magic number in logic
     File: src/services/user_service.py, line 34
     Code: `    if retry_count > 3:`
     Fix:  Extract to named constant: `MAX_RETRIES = 3`

[I2] docstring-required — Public function missing docstring
     File: src/services/user_service.py, line 23
     Code: `def create_user(email: str, role: str) -> User:`
     Fix:  Add docstring describing parameters and return value

=========================================
  TOTALS
=========================================

| Severity | Count | Auto-fixable |
|----------|-------|-------------|
| Critical | 3     | 1           |
| Warning  | 3     | 0           |
| Info     | 2     | 0           |
| **Total**| **8** | **1**       |

Auto-fixable: 1 of 8 violations
Run with --fix to apply auto-fixes.
```

### 7.2 Per-File Summary

Additionally, provide a per-file violation count for quick scanning:

```
PER-FILE SUMMARY
================

| File | Critical | Warning | Info | Total |
|------|----------|---------|------|-------|
| src/routes/users.py | 2 | 1 | 0 | 3 |
| src/services/user_service.py | 0 | 2 | 2 | 4 |
| src/services/payment.py | 1 | 0 | 0 | 1 |
| tests/test_users.py | 0 | 0 | 0 | 0 |
| **Total** | **3** | **3** | **2** | **8** |
```

---

## STEP 8: Diff-Aware Analysis Patterns

Apply smart detection strategies based on how files changed.

### 8.1 New Files (Added)

For files with status `A`:

1. **Full file scan** — apply all applicable rules to every line
2. **Structure check** — verify the file follows project conventions:
   - Has required file header/license if project uses one
   - Follows naming convention (file name matches class/module name)
   - Has appropriate imports organized per project convention
3. **Boilerplate check** — if the file looks like it was copied from another file, flag unchanged placeholder text (e.g., "TODO: replace this")

### 8.2 Modified Files (Changed Lines Only)

For files with status `M`:

1. **Changed lines only** — apply pattern rules to added/modified lines only
2. **Context-aware rules** — for rules that need surrounding code (e.g., "must be in try/except"), read 10 lines of context around each changed line
3. **Removed code check** — if a function/class was removed, verify no other changed files still reference it
4. **Changed signature check** — if a function signature was modified, verify all callers in changed files use the new signature

### 8.3 Deleted Files

For files with status `D`:

1. **Dangling reference check** — search all other changed files for imports or references to the deleted file
2. **No content analysis** — do not apply code quality rules to deleted files

```bash
# Check for dangling references to a deleted file
DELETED_MODULE=$(basename "$DELETED_FILE" | sed 's/\.[^.]*$//')
for file in $(git diff --name-only --diff-filter=AM "$BASE_BRANCH"...HEAD); do
  grep -n "$DELETED_MODULE" "$file" 2>/dev/null && echo "WARNING: $file references deleted module $DELETED_MODULE"
done
```

### 8.4 Renamed/Moved Files

For files with status `R`:

1. **Import update check** — verify all changed files that imported the old path now import the new path
2. **Skip content check** — if the file was only renamed (no content change), do not apply code quality rules
3. **If content also changed** — apply modified-file rules to the content changes

```bash
# For renamed files, check if imports were updated
OLD_PATH="$OLD_FILE"
NEW_PATH="$NEW_FILE"
OLD_MODULE=$(echo "$OLD_PATH" | sed 's/\//./g; s/\.[^.]*$//')
NEW_MODULE=$(echo "$NEW_PATH" | sed 's/\//./g; s/\.[^.]*$//')

for file in $(git diff --name-only --diff-filter=AM "$BASE_BRANCH"...HEAD); do
  grep -n "$OLD_MODULE" "$file" 2>/dev/null && echo "WARNING: $file still imports old path $OLD_MODULE — update to $NEW_MODULE"
done
```

---

## STEP 9: Pipeline Integration

Clear handoff points between /implement, /pr-standards, and /request-code-review.

### 9.1 Input: From /implement or /executing-plans

This skill expects a completed implementation — code is written, tests pass, branch is committed. The input is the branch diff against main.

Prerequisites:
- All implementation work is committed
- Tests pass (verified by /implement Step 6)
- Branch is ready for review

### 9.2 Output: Standards Report + Next Step

Based on the verdict, provide a clear next action:

| Verdict | Critical | Warnings | Action |
|---------|----------|----------|--------|
| **FAIL** | > 0 | any | "Fix {N} critical violations before proceeding. Run `/pr-standards` again after fixing." |
| **FAIL (strict)** | 0 | > 0 | "Strict mode: fix {N} warnings before proceeding. Run `/pr-standards` again after fixing." |
| **WARN** | 0 | > 5 | "Consider addressing {N} warnings before review. Proceed with `/request-code-review`? Warnings will be included in the PR description." |
| **PASS** | 0 | <= 5 | "Standards check passed. Proceed with `/request-code-review`." |

### 9.3 Handoff to /request-code-review

When the standards check passes (or the user chooses to proceed with warnings), include the standards report in the PR review workflow:

```
Standards Check: PASS (2 warnings, 1 info)
Warnings:
  [W1] New function create_user() has no tests
  [W2] TODO without ticket reference on line 45

These will be noted in the PR description for reviewer awareness.
Proceed with /request-code-review.
```

### 9.4 Feedback Loop: Fix and Re-Check

If the standards check fails:

1. Fix all critical violations (manually or via auto-fix)
2. Commit the fixes
3. Re-run `/pr-standards` to verify
4. Repeat until the check passes
5. Then proceed to `/request-code-review`

```
Standards check FAILED. 3 critical violations found.

After fixing, run:
  /pr-standards

Or apply auto-fixes and re-check:
  /pr-standards --fix
```

---

## STEP 10: Team Standards Evolution

Track which rules catch real issues over time to refine the standards.

### 10.1 Violation Logging

After each standards check, log a summary to `.pr-standards-log.json` (gitignored):

```json
{
  "timestamp": "2026-03-12T14:30:00Z",
  "branch": "feature/user-roles",
  "verdict": "FAIL",
  "violations": {
    "critical": 3,
    "warning": 3,
    "info": 2
  },
  "rules_triggered": [
    {"rule": "no-debugger", "count": 1, "severity": "critical"},
    {"rule": "no-hardcoded-secrets", "count": 1, "severity": "critical"},
    {"rule": "rate-limiting-required", "count": 1, "severity": "critical"},
    {"rule": "new-function-needs-test", "count": 1, "severity": "warning"},
    {"rule": "no-swallowed-errors", "count": 1, "severity": "warning"},
    {"rule": "no-todo-without-ticket", "count": 1, "severity": "warning"},
    {"rule": "no-magic-numbers", "count": 1, "severity": "info"},
    {"rule": "docstring-required", "count": 1, "severity": "info"}
  ],
  "auto_fixes_applied": 1,
  "auto_fixes_skipped": 0
}
```

### 10.2 Trend Analysis

When the log file exists and contains 10+ entries, provide trend insights:

```
STANDARDS TREND ANALYSIS
========================

Most triggered rules (last 30 days):
  1. no-todo-without-ticket — 23 violations across 8 PRs
  2. new-function-needs-test — 18 violations across 12 PRs
  3. no-print-debug — 15 violations across 6 PRs
  4. no-swallowed-errors — 12 violations across 5 PRs
  5. no-magic-numbers — 8 violations across 7 PRs

Recommendations:
  - PROMOTE: no-swallowed-errors (warning -> critical)
    Reason: Triggered in 5 PRs, 3 led to production issues
  - RETIRE: no-commented-code
    Reason: 0 violations in last 30 days — rule may be unnecessary
  - NEW RULE CANDIDATE: "require type hints on public functions"
    Reason: Review feedback pattern — reviewers requested type hints in 4 PRs

Never-triggered rules (candidates for removal):
  - no-binding-pry (team does not use Ruby)
  - no-var-dump (team does not use PHP)
```

### 10.3 Rule Lifecycle

| Phase | Criteria | Action |
|-------|----------|--------|
| **Proposed** | Pattern observed in 2+ reviews | Add as `info` severity |
| **Active** | Catches real issues regularly | Promote to `warning` |
| **Critical** | Violations have caused production issues | Promote to `critical` |
| **Retiring** | Zero triggers for 60+ days | Suggest removal |
| **Retired** | Confirmed unused by team | Remove from rule set |

### 10.4 Feeding Insights Back

After trend analysis, suggest actionable improvements:

1. **Frequent warnings -> critical**: If a warning-level rule triggers in 50%+ of PRs and the violations are always fixed, promote it
2. **Frequent info -> warning**: If an info-level rule triggers often and reviewers also flag the same issue, promote it
3. **Never-triggered rules**: Suggest removing rules for languages/frameworks the team does not use
4. **New rule candidates**: When the same manual review comment appears across 3+ PRs, propose a new automated rule

---

## Common Scenarios

### Scenario 1: First Run (No Custom Rules)

When `.pr-standards.yml` does not exist:

1. Apply all built-in default rules (Step 3)
2. Report results with a note: "Using built-in defaults. Create `.pr-standards.yml` to customize rules for your team."
3. Offer to generate a starter `.pr-standards.yml` based on the project's tech stack

### Scenario 2: Large Diff (500+ Changed Lines)

When the diff is large:

1. Note the size: "Large diff detected (X lines). Analysis may take longer."
2. Prioritize critical rules first — report critical violations immediately
3. Run warning and info rules after critical scan completes
4. Consider suggesting PR splitting (reference `/request-code-review` Step 1.3)

### Scenario 3: Only Test Files Changed

When only test files are modified:

1. Skip most code quality rules (debug statements in tests are sometimes acceptable)
2. Apply test-specific rules: no `@skip` without ticket, test naming conventions
3. Report with a note: "Only test files changed. Reduced rule set applied."

### Scenario 4: Configuration/Build Files Only

When only config files changed (`.yml`, `.json`, `.toml`, `Dockerfile`, etc.):

1. Apply security rules (no hardcoded secrets, no disabled security)
2. Skip code quality rules (no magic numbers, no empty catch, etc.)
3. Report with a note: "Configuration changes only. Security rules applied."

### Scenario 5: Migration Files

When database migration files are changed:

1. Apply security rules (no hardcoded secrets)
2. Flag irreversible operations: `DROP TABLE`, `DROP COLUMN`, `ALTER COLUMN ... NOT NULL` without default
3. Note: "Migration file detected. Verify rollback plan exists."

---

## CRITICAL RULES

- **Analyze only changed lines** — NEVER scan entire files for modified files. This keeps the check fast and focused on what the developer actually changed. New files are the only exception.
- **Load all rule sources** — ALWAYS check `.claude/rules/`, `CLAUDE.md`, and `.pr-standards.yml`. Missing any source means missing applicable rules.
- **Critical violations block the PR** — NEVER suggest proceeding to `/request-code-review` when critical violations exist. They must be fixed first.
- **Show the actual code** — ALWAYS include the matched code snippet in the violation report, not just the rule name and line number. Developers need to see what triggered the rule.
- **Deduplicate violations** — NEVER report the same violation twice for the same line. Group adjacent violations from the same rule.
- **Respect exclude paths** — NEVER report violations in excluded paths (vendor, generated, minified files).
- **Auto-fix requires confirmation** — NEVER apply auto-fixes without user confirmation unless `--fix` flag is explicitly passed.
- **Track context for context-aware rules** — ALWAYS read surrounding code when a rule requires context (e.g., "must be in try/except"). Do not guess based on the single matched line.

## MUST NOT DO

- MUST NOT scan the entire codebase — only analyze the diff between the current branch and base
- MUST NOT treat warnings as blocking unless `--strict` is passed
- MUST NOT apply auto-fixes silently — always show before/after and get confirmation
- MUST NOT skip built-in rules when custom rules exist — both apply unless a rule is explicitly excluded
- MUST NOT report violations in deleted lines — only check added/modified lines
- MUST NOT create the `.pr-standards.yml` file without the user asking — only offer to generate it
- MUST NOT ignore the `exclude-paths` setting — always filter out excluded paths before analysis
- MUST NOT proceed to `/request-code-review` when critical violations remain unresolved
- MUST NOT modify the `.pr-standards-log.json` format without backward compatibility — append-only logging
- MUST NOT run the full test suite as part of standards checking — that is the responsibility of `/implement`
