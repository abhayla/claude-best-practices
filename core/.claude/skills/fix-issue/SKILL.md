---
name: fix-issue
description: >
  Analyze and implement a fix for a specific GitHub Issue. Fetches issue details
  via `gh`, explores codebase for root cause, plans minimal fix, implements,
  verifies with tests, and runs post-fix-pipeline. Use when user says "fix
  issue #N" or references a GitHub Issue. For general feature work without a
  GitHub Issue, use /implement instead. For iterative test fixing, use /fix-loop.
  For bugs without a GitHub Issue, use /debugging-loop or /systematic-debugging.
type: workflow
triggers:
  - fix issue #
  - fix #
  - resolve issue #
  - work on issue #
  - investigate issue #
  - gh issue fix
allowed-tools: "Bash Read Grep Glob Write Edit Skill"
argument-hint: "<issue-number or issue-url>"
version: "2.5.0"
---

# Fix GitHub Issue

Fetch a GitHub Issue, diagnose root cause, implement a minimal fix, verify with tests, and finalize via post-fix-pipeline.

**Critical:** This skill requires `gh` CLI authenticated. If $ARGUMENTS is empty, ask the user for the issue number. Always fetch the issue first — never guess what the issue is about. Delegate test failures to `/fix-loop`, not manual retry.

**Issue:** $ARGUMENTS

---

## STEP 1: Fetch and Parse Issue

**Extract issue number** from `$ARGUMENTS`:
- `#42` or `42` → use `42`
- `https://github.com/owner/repo/issues/42` → extract `42`
- If no number found, ask the user

```bash
gh issue view $ISSUE_NUMBER --json title,body,labels,assignees,comments,state
```

**Error handling:**

| Condition | Action |
|-----------|--------|
| `gh` not authenticated | Report: "Run `gh auth login` first" → STOP |
| Issue not found | Report: "Issue #N not found in this repo" → STOP |
| Issue state is `CLOSED` | Confirm with user: "Issue #N is already closed. Continue anyway?" |
| No repro steps for a bug | Derive repro hypothesis from description; flag as assumption |

**Parse the issue into a structured brief:**
```markdown
**Title:** <issue title>
**Type:** bug | feature | enhancement | chore
**Repro steps:** <from body, or derived hypothesis>
**Expected:** <expected behavior>
**Actual:** <current behavior>
**Mentioned files/components:** <extracted from body and comments>
**Labels:** <issue labels>
```

## STEP 2: Explore and Diagnose

Search the codebase for root cause (bugs) or implementation location (features):

1. **Grep** for keywords, error messages, and component names from the issue brief
2. **Read** the 2-3 most relevant source files identified by search
3. **Read** existing tests in the affected area to understand current coverage
4. **Check** git blame on suspected lines to understand recent changes

**Decision point:**

| Situation | Action |
|-----------|--------|
| Root cause is clear after exploration | Proceed to Step 3 |
| Root cause unclear after 10+ minutes of exploration | Escalate: `Skill("systematic-debugging", args="<issue brief>")` and use its diagnosis output |
| Issue is a feature request with complex requirements | Escalate: `Skill("implement", args="<parsed requirements from issue>")` then skip to Step 4 |

## STEP 3: Implement and Test

1. **Write a failing test** that reproduces the bug (or defines the feature behavior)
2. **Implement the minimal fix** — change only what the issue requires
3. **Run targeted tests** for the changed area
4. **If tests fail**, delegate: `Skill("fix-loop", args="<failure output> retest_command: <cmd>")`
5. **Run broader test suite** for regression check

**Scope guard:** If the fix requires changes to > 3 files, confirm approach with user before proceeding. Large fixes often indicate a misdiagnosed root cause.

## STEP 4: Finalize

Run the post-fix pipeline to commit, document, and capture learnings:

```
Skill("post-fix-pipeline", args="fixes_applied: [summary of changes] issue: #$ISSUE_NUMBER")
```

If `post-fix-pipeline` is not available, manually:
1. Commit with conventional message: `fix: resolve #N — <description>`
2. Update docs if behavior changed
3. Capture learnings via `Skill("learn-n-improve", args="session")`

## STEP 5: Summarize

```markdown
## Fix Summary: Issue #N — <title>

**Root cause:** <1-2 sentences>
**Fix:** <what was changed and why>
**Files changed:** <list>
**Tests:** <added/modified/verified>
**Follow-up:** <items or "none">
```

---

## Failure Modes

| Failure | Prevention |
|---------|-----------|
| `gh` not installed or authenticated | Check in Step 1 before any code exploration |
| Issue body is vague or missing repro steps | Derive hypothesis and flag as assumption — do not guess silently |
| Root cause misdiagnosed → fix doesn't resolve issue | Write reproducing test FIRST (Step 3) — if test doesn't fail, diagnosis is wrong |
| Fix touches too many files → scope creep | Enforce 3-file scope guard; escalate to user if exceeded |
| Post-fix-pipeline unavailable | Graceful fallback to manual commit + docs + learnings |

---

## CRITICAL RULES

- MUST fetch the GitHub Issue via `gh issue view` before any code changes — Why: the issue body is the source of truth; guessing from title alone leads to wrong fixes
- MUST write a failing test before implementing the fix — Why: a test that doesn't fail before the fix proves nothing; TDD catches misdiagnosed root causes
- MUST verify with tests before declaring done — Why: untested fixes create false confidence and break in production
- MUST confirm approach with user if fix requires > 3 files — Why: large fixes usually indicate misdiagnosed root cause or scope creep
- MUST NOT guess issue content from the title alone — Why: titles are often misleading; the body and comments contain the real context
- MUST NOT implement unrelated improvements while fixing — Why: scope discipline prevents regressions and keeps PRs reviewable. Use a separate PR instead
- MUST NOT skip post-fix-pipeline — Why: uncommitted fixes are lost fixes; learnings not captured repeat as future mistakes
