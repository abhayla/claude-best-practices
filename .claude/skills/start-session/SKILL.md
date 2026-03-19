---
name: start-session
description: >
  Restore a previously saved session checkpoint. Reads a session file from .claude/sessions/,
  loads working files into context, and presents a structured briefing with task progress
  and resume notes. Use when starting a new conversation to pick up where you left off.
type: workflow
allowed-tools: "Bash Read Grep Glob"
argument-hint: "[session-name | --list]"
version: "1.0.0"
---

# Start Session — Restore a Saved Checkpoint

Load a session file created by `/save-session` and restore working context for seamless resumption.

**Key distinction:** `/start-session` restores file-level context from a structured checkpoint. `/continue` gives a lightweight git-state briefing without session files. Use `/start-session` when you have a saved session; use `/continue` for a quick orientation.

---

## STEP 1: Find Session

Determine which session to load based on the argument:

### If `--list` is provided:
```bash
ls -lt .claude/sessions/*.md 2>/dev/null
```
Present a numbered list of available sessions with dates and names. Ask the user to pick one. If no sessions exist, inform the user and suggest running `/save-session` first.

### If a session name is provided:
Look for `.claude/sessions/{name}.md`. If not found:
1. Try fuzzy match — list sessions containing the provided name
2. If exactly one match, confirm and use it
3. If multiple matches, present them and ask the user to pick
4. If no matches, inform the user and list available sessions

### If no argument is provided:
Load the most recent session file (by filesystem modification time):
```bash
ls -t .claude/sessions/*.md 2>/dev/null | head -1
```
If no sessions exist, inform the user and suggest `/save-session`.

---

## STEP 2: Parse Session File

Read the session file and extract these sections:
- **Working Files** — file paths, statuses, and notes
- **Git State** — branch, recent commits, uncommitted changes
- **Key Decisions** — architectural choices and rationale
- **Task Progress** — completed, in-progress, and blocked items
- **Resume Notes** — what to do first, gotchas, context needed

Handle missing sections gracefully — if a section is absent, note it as "not captured" rather than failing.

---

## STEP 3: Restore Context

Load working files into context in priority order:

### Priority order:
1. **Modified files** — most likely to need immediate attention
2. **Created files** — new code that needs continuation
3. **Read files with specific lines noted** — targeted context
4. **Read files without specific lines** — background context

### Constraints:
- **Limit to 10 files maximum** — if more than 10 working files are listed, load the top 10 by priority and note the remainder
- **Verify files exist** — before reading each file, check it exists. If a file is missing, warn: "File `{path}` from session no longer exists (may have been renamed or deleted)"
- **Check branch match** — compare the current branch to the session's branch:
  ```bash
  git branch --show-current
  ```
  If branches differ, warn: "Session was on branch `{session-branch}` but you're on `{current-branch}`. Some files may have different content."

Read each existing file using the Read tool.

---

## STEP 4: Present Briefing

Present a structured briefing — do NOT auto-start any work.

```markdown
## Session Restored: {session-name}

**Saved:** {date}
**Branch:** {session-branch} {⚠️ current: {current-branch} if different}

### Working Files Loaded
- {file} ({status}) — {notes}
- ... ({N} of {total} files loaded)

### Task Progress
**Completed:** {count}
**In Progress:** {count}
- {in-progress item 1}
- {in-progress item 2}
**Blocked:** {count}
- {blocked item} — {blocker}

### Key Decisions
- {decision summary}

### Resume Notes
> {what to do first}
> {watch out for}

### Suggested Action
> {specific next step based on in-progress/blocked items}
```

---

## CRITICAL RULES

- MUST NOT modify any files — this skill is strictly read-only
- MUST NOT auto-start work after presenting the briefing — wait for user direction
- MUST warn if the current branch differs from the session's branch
- MUST handle missing files gracefully — warn and continue, do not fail
- MUST limit file reads to 10 maximum to avoid context overload
- MUST handle missing sections in session files without errors
- MUST inform the user if no sessions exist and suggest `/save-session`
