---
name: fix-issue
description: >
  Analyze and implement a fix for a specific GitHub Issue. Fetches issue details,
  explores codebase, plans implementation, implements fix, verifies with tests,
  and runs post-fix-pipeline. Use when user says "fix issue #N".
allowed-tools: "Bash Read Grep Glob Write Edit Skill"
argument-hint: "<issue-number or issue-url>"
version: "1.0.0"
type: workflow
---

# Fix GitHub Issue

Analyze and implement a fix for a specific GitHub Issue.

**Issue:** $ARGUMENTS

---

## STEP 1: Fetch Issue Details

```bash
gh issue view $ISSUE_NUMBER --json title,body,labels,assignees,comments
```

Parse the issue to understand:
- What's broken or requested
- Steps to reproduce (if bug)
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

If changes were significant, run the post-fix pipeline:

```
Skill("post-fix-pipeline", args="fixes_applied: [summary of changes]")
```

## STEP 7: Summary

Provide a summary of:
- Root cause (for bugs) or approach (for features)
- Files changed
- Tests added/modified
- Any follow-up items

---

## CRITICAL RULES

- Always understand the issue before coding
- Make minimal, focused changes
- Verify with tests before declaring done
- If fix requires > 3 files changed, confirm approach with user first
