---
name: continue
description: >
  Resume work from a previous session. Reads continuation state, workflow progress,
  git state, and recent test evidence to produce a briefing with suggested next action.
  Use when starting a new conversation or returning after a break.
allowed-tools: "Bash Read Grep Glob"
argument-hint: ""
version: "1.1.0"
type: workflow
---

# Continue — Resume Previous Work

Resume work from where the last session left off.

---

## STEP 1: Gather State

Read the following (skip any that don't exist):

1. **Continuation docs** — Look for `CONTINUE_PROMPT.md`, `docs/CONTINUE_PROMPT.md`, or similar handoff documents
2. **Git state** — `git status`, `git log --oneline -5`, `git stash list`
3. **Recent changes** — `git diff --stat HEAD~3..HEAD`
4. **Open issues** — `gh issue list --assignee @me --state open --limit 5` (if gh is available)
5. **Task/TODO files** — Check for TODO.md, tasks.md, or similar
6. **Saved sessions** — Check if `.claude/sessions/` exists with `.md` files. If found, note the most recent session and suggest: "Saved session found: `{name}` ({date}). Use `/start-session` to restore full context, or continue with this general briefing."

## STEP 2: Assess Priority

Based on gathered state, determine the highest priority action:

| State | Priority | Action |
|-------|----------|--------|
| Uncommitted changes | High | Review and commit or continue work |
| Failing tests | High | Run tests, fix failures |
| Open PR with review comments | High | Address review feedback |
| In-progress feature | Medium | Continue implementation |
| Stashed changes | Medium | Review stash and apply or drop |
| No clear state | Low | Ask user what to work on |

## STEP 3: Briefing

Present a concise briefing:

```markdown
## Session Briefing

### Current State
[One-line summary]

### Recent Activity
- [Last 3-5 meaningful changes]

### Pending Work
1. [Highest priority item]
2. [Next priority]

### Suggested Next Action
> [Specific actionable suggestion]
```

---

## RULES

- Do NOT modify any files — this skill is read-only
- Keep the briefing concise — under 30 lines
- Always include a specific suggested next action
