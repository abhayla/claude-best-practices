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
version: "1.0.0"
type: workflow
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

## STEP 3: Built-in Default Rules

These rules apply when no `.pr-standards.yml` exists, or alongside custom rules unless explicitly excluded. They represent universally applicable code hygiene standards.


**Read:** `references/built-in-default-rules.md` for detailed step 3: built-in default rules reference material.

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

## STEP 5: Classify Violations by Severity

Categorize every violation and determine the overall PR verdict.


**Read:** `references/classify-violations-by-severity.md` for detailed step 5: classify violations by severity reference material.

## STEP 6: Generate Auto-Fixes

For each violation marked as auto-fixable, generate a concrete code fix.


**Read:** `references/generate-auto-fixes.md` for detailed step 6: generate auto-fixes reference material.

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


**Read:** `references/generate-standards-report.md` for detailed step 7: generate standards report reference material.

## STEP 8: Diff-Aware Analysis Patterns

Apply smart detection strategies based on how files changed.


**Read:** `references/diff-aware-analysis-patterns.md` for detailed step 8: diff-aware analysis patterns reference material.

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


**Read:** `references/pipeline-integration.md` for detailed step 9: pipeline integration reference material.

## STEP 10: Team Standards Evolution

Track which rules catch real issues over time to refine the standards.


**Read:** `references/team-standards-evolution.md` for detailed step 10: team standards evolution reference material.

## Common Scenarios


**Read:** `references/common-scenarios.md` for detailed common scenarios reference material.

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
