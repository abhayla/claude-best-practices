---
name: fix-issue
description: >
  Analyze and implement a fix for a specific GitHub Issue. Fetches issue details
  via `gh`, explores codebase for root cause, plans minimal fix, implements,
  verifies with tests, and runs post-fix-pipeline. Use when user says "fix
  issue #N" or references a GitHub Issue. For general feature work, use
  /implement instead. For iterative test fixing, use /fix-loop directly.
type: workflow
triggers:
  - fix issue #
  - fix github issue
  - resolve issue #
  - close issue #
  - fix bug from issue
  - work on issue #
  - look at issue #
  - address issue #
  - fix #
  - gh issue fix
  - tackle issue #
  - handle issue #
  - investigate issue #
allowed-tools: "Bash Read Grep Glob Write Edit Skill"
argument-hint: "<issue-number or issue-url>"
version: "2.4.0"
---

# Fix GitHub Issue

Analyze and implement a fix for a specific GitHub Issue.

**Critical:** This skill requires `gh` CLI authenticated. If $ARGUMENTS is empty, ask the user for the issue number. Always fetch the issue first — never guess what the issue is about. Delegate test failures to `/fix-loop`, not manual retry.

**Issue:** $ARGUMENTS

---

## STEP 1: Extract Issue Number and Fetch Details

**Extract issue number** from `$ARGUMENTS`:
- `#42` or `42` → use `42`
- `https://github.com/owner/repo/issues/42` → extract `42`
- If no number found, ask the user

```bash
gh issue view $ISSUE_NUMBER --json title,body,labels,assignees,comments,state
```

**Error handling:**
- If `gh` returns error ("Could not resolve to an issue") → report to user and STOP
- If issue `state` is `CLOSED` → confirm with user before proceeding ("Issue #N is already closed. Continue anyway?")

Parse the issue to understand:
- What's broken or requested
- Steps to reproduce (if bug) — if missing for a bug, attempt to derive from description
- Expected vs actual behavior
- Related files or components mentioned

## STEP 2: Explore Codebase

1. Search for files related to the issue keywords
2. Read relevant source files and tests
3. Understand the current behavior
4. Identify root cause (for bugs) or implementation location (for features)

## STEP 3: Plan Implementation

1. List the files that need to change
2. Describe the minimal fix/implementation
3. Identify which tests need updating or creation
4. Note any risks or side effects

## STEP 4: Implement Fix

1. Make the code changes
2. Create or update tests
3. Follow existing project conventions

## STEP 5: Verify with Tests

Run tests to verify the fix:

1. Run targeted tests for the changed area
2. If tests fail, delegate to `/fix-loop`
3. Run broader test suite for regression check

## STEP 6: Post-Fix Pipeline

Run the post-fix pipeline to finalize verified changes:

```
Skill("post-fix-pipeline", args="fixes_applied: [summary of changes]")
```

If `post-fix-pipeline` is not available in this project, manually: update docs if behavior changed, commit with conventional message referencing the issue (`fix: resolve #N — description`), and capture learnings.

## STEP 7: Summary

```markdown
## Fix Summary: Issue #N — <title>

**Root cause:** <1-2 sentences>
**Fix:** <what was changed and why>
**Files changed:** <list>
**Tests:** <added/modified/verified>
**Follow-up:** <items or "none">
```

---

## CRITICAL RULES

- MUST fetch the GitHub Issue via `gh issue view` before any code changes — never assume issue content
- MUST make minimal, focused changes — fix only what the issue describes
- MUST verify with tests before declaring done — delegate failures to `/fix-loop`
- MUST confirm approach with user if fix requires changes to > 3 files
- MUST NOT skip Step 1 (issue fetch) — the issue body is the source of truth
- MUST NOT guess the issue content from the title alone — read the full body and comments
- MUST NOT implement unrelated improvements while fixing — scope discipline
