---
name: save-session
description: >
  Save a structured session checkpoint capturing working files, git state, key decisions,
  and task progress. Creates a resumable session file in .claude/sessions/ that
  /start-session can restore in a future conversation. Use when pausing work, before
  long breaks, or when the session-reminder hook fires.
type: workflow
allowed-tools: "Bash Read Write Grep Glob"
argument-hint: "[session-name]"
version: "1.1.0"
---

# Save Session — Checkpoint Your Progress

Capture the current working state into a structured session file for later resumption via `/start-session`.

**Key distinction:** `/save-session` captures file-level working state for exact resumption. `/handover` produces a narrative handoff document for broader context transfer. `/continue` is a lightweight git-state briefing. These serve different needs — use all three as appropriate.

---

## STEP 1: Determine Session Name

If the user provided a session name argument, use it. Otherwise, auto-generate one:

1. Get the current date: `date +%Y-%m-%d`
2. Get the current branch name: `git branch --show-current`
3. Get recent commit messages: `git log --oneline -3`
4. Derive a 2-4 word task summary from the branch name or recent commits
5. Format: `{YYYY-MM-DD}-{task-summary}` (e.g., `2026-03-19-add-session-skills`)

**Collision check:** If `.claude/sessions/{name}.md` already exists:
- Ask the user: overwrite, append a numeric suffix (`-2`, `-3`), or choose a different name
- MUST NOT silently overwrite

**Sanitization:** Convert the name to filesystem-safe kebab-case:
- Lowercase, replace spaces and underscores with hyphens
- Remove characters not in `[a-z0-9-]`
- Collapse consecutive hyphens

---

## STEP 2: Gather Context

Collect all context inline (no subagent delegation).

### 2.1: Working Files

```bash
git status --short
git diff --name-status HEAD
```

Classify each file:
- **modified** — existing file with changes (staged or unstaged)
- **created** — new untracked or newly added file
- **deleted** — removed file
- **read** — files that were read during the session but not changed (scan conversation history for Read tool calls on files not in the diff)

For modified/created files, note a brief context of what changed (1 line).

### 2.2: Git State

```bash
git branch --show-current
git log --oneline -5
git diff --stat
git stash list
```

Record: current branch, last 5 commits, uncommitted change summary, stash entries.

### 2.3: Key Decisions

Scan the conversation for architectural choices, design decisions, or trade-offs discussed. Look for:
- Choices between approaches ("went with X because...")
- Rejected alternatives
- Constraints discovered during implementation

Format as bullet points with rationale.

### 2.4: Task Progress

Categorize work items from the conversation into:
- **Completed** — finished and verified
- **In Progress** — started but not finished
- **Blocked** — waiting on something (specify the blocker)

### 2.5: Relevant Docs

Scan the project for documentation files that are relevant to the current work:

```bash
# Check for common doc locations (skip if they don't exist)
ls README.md docs/ ARCHITECTURE.md CONTRIBUTING.md 2>/dev/null
```

Only include docs that are directly relevant to the work in this session.

---

## STEP 3: Generate Session File

1. Read the template from the skill's references directory. If running from a project that copied this skill, the template is at `.claude/skills/save-session/references/session-template.md`. If the template is not found, use the structure from memory (the template format is documented in this skill).

2. Populate the template with gathered context from Step 2.

3. Create the sessions directory if it doesn't exist:
   ```bash
   mkdir -p .claude/sessions
   ```

4. Write the populated session file:
   ```
   .claude/sessions/{session-name}.md
   ```

---

## STEP 4: Purge Expired Sessions

Automatically delete session files older than 5 days. This runs silently with no user interaction.

```bash
find .claude/sessions -name "*.md" -mtime +5 -delete 2>/dev/null
```

On Windows (Git Bash / MSYS2 may not support `-mtime`), use this fallback:

```bash
python3 -c "
import os, time, glob
cutoff = time.time() - 5 * 86400
for f in glob.glob('.claude/sessions/*.md'):
    if os.path.getmtime(f) < cutoff:
        os.remove(f)
" 2>/dev/null || true
```

MUST NOT prompt the user or log individual deletions. If no expired sessions exist, this step is a silent no-op.

---

## STEP 5: Post-Save Summary

After saving, present:

1. **Confirmation:** "Session saved to `.claude/sessions/{name}.md`"
2. **Gitignore suggestion:** If `.claude/sessions/` is not in `.gitignore`, suggest adding it:
   ```
   # Session files (local working state)
   .claude/sessions/
   ```
   Note: Teams that want to share session state can skip this.
3. **Resume command:** "To restore this session later, run: `/start-session {name}`"
4. **Quick stats:** Number of working files captured, completed/in-progress/blocked counts

---

## CRITICAL RULES

- MUST NOT hardcode project-specific paths — use generic discovery (`ls`, `find`) for docs
- MUST NOT include self-improvement or learnings sections — `/learn-n-improve` handles that
- MUST NOT overwrite an existing session file without explicit user confirmation
- MUST create `.claude/sessions/` directory if it does not exist
- MUST sanitize session names to filesystem-safe kebab-case
- MUST NOT delegate context gathering to subagents — gather inline in this skill
- MUST read the session template from `references/session-template.md` when available
- MUST automatically purge session files older than 5 days — no user confirmation required
- MUST NOT log or display individual file deletions during purge — silent cleanup only
