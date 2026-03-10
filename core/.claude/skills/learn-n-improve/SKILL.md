---
name: learn-n-improve
description: >
  Learning system analysis and self-modification. Analyzes session outcomes, updates
  memory topics (testing-lessons, fix-patterns, skill-gaps). Four modes: session
  (recent work), deep (modify skills), meta (learning effectiveness), test-run (dry run).
allowed-tools: "Bash Read Grep Glob Write Edit"
argument-hint: "<mode: session|deep|meta|test-run>"
---

# Learn & Improve — Session Reflection

Analyze session outcomes and update learning files for future sessions.

**Mode:** $ARGUMENTS

---

## Modes

| Mode | When to Use | What it Does |
|------|-------------|-------------|
| `session` | After completing work | Capture outcomes, update memory topics |
| `deep` | After recurring failures | Analyze patterns, suggest skill/rule modifications |
| `meta` | Periodically | Evaluate if learning system is effective |
| `test-run` | Before committing changes | Dry run — show what would be updated |

---

## STEP 1: Gather Session Evidence

Read recent session artifacts:
- Git log (recent commits)
- Test results (if any)
- Fix-loop outcomes (if any)
- Files modified

## STEP 2: Analyze Outcomes

Categorize session work:
- **Successes** — What worked well, patterns to reinforce
- **Failures** — What went wrong, root causes identified
- **Workarounds** — Temporary fixes that should become permanent
- **Knowledge gaps** — Areas where more context was needed

## STEP 3: Update Memory Topics

Update files in the project's memory directory:

| File | Content |
|------|---------|
| `fix-patterns.md` | Recurring fix patterns with file references |
| `testing-lessons.md` | Testing insights and fixture knowledge |
| `skill-gaps.md` | Areas where skills need improvement |

For each update:
1. Read existing file
2. Check for duplicates
3. Append new entries with date stamps
4. Remove outdated entries

## STEP 4: Report

```
Learning Update:
  Mode: [session/deep/meta/test-run]
  New entries: N
  Updated entries: M
  Topics affected: [list]
```

---

## RULES

- Never delete historical entries without evidence they're wrong
- Date-stamp all new entries
- Cross-reference with existing patterns before adding
- In `test-run` mode, only show what would change — don't write
