---
name: implement
description: >
  Implement a feature or fix following a structured workflow: requirements analysis,
  test creation, implementation, test execution, fix-loop delegation, and verification.
  Use when user requests new functionality or structured bug fixes.
allowed-tools: "Bash Read Grep Glob Write Edit Skill"
argument-hint: "<feature-description>"
---

# Implement Feature/Fix

Implement the requested feature or fix following a structured workflow.

**Request:** $ARGUMENTS

---

## STEP 1: Analyze Requirements

1. Read the feature request / issue description carefully
2. Identify affected files and components
3. Check existing tests and code patterns in the area
4. Review any related documentation

## STEP 2: Create/Update Tests

Before implementing, write or update tests that define the expected behavior:

1. Identify the appropriate test file(s)
2. Write tests that will FAIL before implementation (TDD approach)
3. Follow existing test patterns and conventions in the project

## STEP 3: Implement the Feature

1. Make minimal, focused changes
2. Follow existing code patterns and conventions
3. Keep changes reversible where possible
4. Add comments only where logic isn't self-evident

## STEP 4: Run Tests

Run the relevant test suite to verify implementation:

1. Run targeted tests for the changed area first
2. If targeted tests pass, run broader test suite
3. If tests fail, proceed to fix-loop

## STEP 5: Fix Loop (if tests fail)

Delegate to `/fix-loop` with the failing test command:

```
Skill("fix-loop", args="retest_command: <the failing test command>")
```

Continue until all tests pass.

## STEP 6: Verification

1. Run full test suite to check for regressions
2. Review changes with `/post-fix-pipeline` if significant changes were made
3. Summarize what was implemented and any decisions made

## STEP 7: Post-Implementation

1. Invoke `/learn-n-improve session` to capture learnings
2. Provide summary of changes to the user

---

## CRITICAL RULES

- Always write tests before or alongside implementation
- Follow existing project conventions (check CLAUDE.md and .claude/rules/)
- Make minimal changes — don't refactor unrelated code
- If stuck after 3 fix-loop iterations, ask the user for guidance
