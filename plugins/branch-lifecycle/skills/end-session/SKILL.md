---
name: end-session
description: >
  End and close a work session — round up everything: state the session goal + assess it,
  save a resumable checkpoint (working files, git state, decisions, task progress), LAND the
  work (CI-gated auto-merge), and confirm the session is closeable. Use when finishing, wrapping
  up, or closing a session (also covers a mid-work "save my progress" checkpoint).
type: workflow
triggers:
  - end session
  - close session
  - wrap up
  - finish session
  - round up and close
  - save session
  - checkpoint
allowed-tools: "Bash Read Write Grep Glob"
argument-hint: "[session-name]"
version: "2.2.0"
---

# End Session — Round Up & Close

Close out a work session cleanly: round up everything into a resumable checkpoint, **land the
work** (so "session ended" = "merged when green"), and confirm the session can be closed.
Restore later with `/start-session`.

**Key distinction:** `/end-session` captures file-level working state for exact resumption. `/continue` is a lightweight git-state briefing. These serve different needs — use both as appropriate.

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

1. Read the template from this plugin's bundled references directory:
   `${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel)/.claude/plugins/branch-lifecycle}/skills/end-session/references/session-template.md`.
   If the template is not found, use the structure from memory (the template format is documented in this skill).

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

## STEP 5: Land the Session's Work — WAIT for CI, then merge (CLOSE the branch)

"Session ended" must mean "the work is merged and the branch is **CLOSED**" — not "a PR was armed
and left open." So this step **waits for the required CI checks to conclude, then merges
synchronously**. This runs on the CURRENT branch (the one thing `/start-session` STEP 0 skips).

**Why the wait is the whole point (the root cause it fixes):** a freshly-pushed PR's CI has not run
yet, so its `mergeStateStatus` is never `CLEAN` at push time. A naive "if CLEAN merge, else arm"
check therefore ALWAYS arms-and-returns — leaving the branch open while the merge happens
*asynchronously, after* `/end-session` already declared the session closed. Waiting for CI to finish
is what makes the close real and synchronous.

Skip silently if `gh` is unavailable, the repo has no GitHub remote, on `main`/`master`/detached
HEAD, or `AUTO_MERGE=0`.

```bash
# Single source of truth for the landing logic: the plugin's bundled hooks/session-git-landing.sh
# (shared with /start-session's reconcile and the auto-pr hooks — fix landing in ONE place).
# `land --wait` arms GitHub's native auto-merge (gated on the REQUIRED checks only) and then BLOCKS
# until the PR is MERGED, so the branch is genuinely CLOSED before this step returns. It prints one
# of: "merged ... CLOSED" / "NOT CLOSED ..." / "skipped ...". Report that verbatim in STEP 6.
# If CLAUDE_PLUGIN_ROOT is unset, run the plugin's bundled hooks/session-git-landing.sh directly.
bash "${CLAUDE_PLUGIN_ROOT:-$(git rev-parse --show-toplevel)/.claude/plugins/branch-lifecycle}/hooks/session-git-landing.sh" land --wait
```

MUST NOT force-merge past failing CI, and MUST NOT report the session as closed while the branch is
still open — STEP 5 either merges+closes the branch (after CI passes) or surfaces the CI failure.
Report which happened in STEP 6.

---

## STEP 6: Post-Save Summary

After saving, present:

1. **Confirmation:** "Session saved to `.claude/sessions/{name}.md`"
1b. **Landing:** what STEP 5 did — "merged '<branch>' → main and CLOSED the branch (CI passed)", "NOT closed — CI failed (armed as fallback); investigate <check>", or "skipped (why — e.g. on main / no remote)".
2. **Gitignore suggestion:** If `.claude/sessions/` is not in `.gitignore`, suggest adding it:
   ```
   # Session files (local working state)
   .claude/sessions/
   ```
   Note: Teams that want to share session state can skip this.
3. **Resume command:** "To restore this session later, run: `/start-session {name}`"
4. **Quick stats:** Number of working files captured, completed/in-progress/blocked counts
5. **Session closeable:** state the session goal + whether it was met (distinguish PARKED external blockers from PENDING work). Confirm "the session is complete and can be closed" ONLY if STEP 5 actually merged + closed the branch (or cleanly skipped). If STEP 5 reported "NOT closed" (CI failed), the session is NOT cleanly closeable — say so and name the failing check; do not declare it closed with an open branch.

---

## CRITICAL RULES

- MUST NOT hardcode project-specific paths — use generic discovery (`ls`, `find`) for docs
- MUST NOT include self-improvement or learnings sections — leave that to a dedicated learning/self-improvement skill if the project has one
- MUST NOT overwrite an existing session file without explicit user confirmation
- MUST create `.claude/sessions/` directory if it does not exist
- MUST sanitize session names to filesystem-safe kebab-case
- MUST NOT delegate context gathering to subagents — gather inline in this skill
- MUST read the session template from this plugin's `skills/end-session/references/session-template.md` when available
- MUST automatically purge session files older than 5 days — no user confirmation required
- MUST NOT log or display individual file deletions during purge — silent cleanup only
- MUST, in STEP 5, **arm GitHub native auto-merge (gated on the REQUIRED checks only) and WAIT for the PR to reach `MERGED`** — so the branch is genuinely CLOSED when the skill returns, not armed-and-left-open. A fresh PR is never `CLEAN` at push time, so checking merge-state (or returning) without waiting leaves the branch open (the root cause). MUST NOT gate on ALL checks (e.g. `--watch --fail-fast`) — a noisy non-required workflow would false-fail while the required `validate` passes.
- MUST NOT force-merge past failing CI, and MUST NOT declare the session "closed/closeable" while its branch is still open. If CI fails, arm as a fallback, report "NOT closed" + the failing check, and do NOT claim the session is cleanly closeable. Skip on `main`/detached HEAD/no-`gh`/no-remote/`AUTO_MERGE=0`.
