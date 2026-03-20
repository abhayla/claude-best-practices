---
name: handover
description: >
  Generate a structured handover document when ending a session, designed for a
  completely fresh session to pick up exactly where you left off. Scans conversation
  history, pulls from scratchpad and learn-n-improve, and produces a curated summary
  covering decisions, pitfalls, current state, and prioritized next steps.
triggers:
  - handover
  - session-end
  - wrap-up
allowed-tools: "Bash Read Grep Glob Write Edit Skill"
argument-hint: "<optional: focus area or notes for next session>"
version: "1.0.0"
type: workflow
---

# Session Handover

Generate a comprehensive handover document so the next session can resume with full context.

**Focus/Notes:** $ARGUMENTS

---

## STEP 1: Detect Handover Context

Before generating, determine what context is available:

### 1.1 Check for Previous Handover

```bash
# Check for existing handover document
cat .claude/handover.md 2>/dev/null
```

If a previous handover exists:
1. Read it to understand what was planned
2. Track which "Next Steps" from that handover were completed
3. Identify what changed since the last session
4. Prepare a "Since Last Handover" diff section

### 1.2 Check for Scratchpad

```bash
# Check for scratchpad in common locations
cat scratchpad.md 2>/dev/null
cat .claude/scratchpad.md 2>/dev/null
```

If a scratchpad exists:
1. Extract gotchas, judgment calls, and open questions
2. Pull any file-discovery notes or architecture observations
3. Mark which scratchpad entries are session-specific vs persistent
4. Deduplicate against what will go in the decision log and pitfalls sections

### 1.3 Check for Learnings

```bash
# Check for learn-n-improve artifacts
ls .claude/memory/ 2>/dev/null
cat .claude/memory/fix-patterns.md 2>/dev/null
cat .claude/memory/testing-lessons.md 2>/dev/null
cat .claude/memory/skill-gaps.md 2>/dev/null
```

If learning files exist:
1. Extract entries timestamped from today's session
2. Include key learnings in the handover
3. Note any skill-gap entries that affect next steps
4. Reference the memory files for full history

## STEP 2: Review the Session

Systematically scan the conversation to extract what happened during this session.


**Read:** `references/review-the-session.md` for detailed step 2: review the session reference material.

## STEP 3: Build the Decision Log

Record every non-trivial decision made during the session. A "non-trivial" decision is anything where an alternative existed and reasoning was required.


**Read:** `references/build-the-decision-log.md` for detailed step 3: build the decision log reference material.

# ADR-<number>: <Title>

**Date:** <YYYY-MM-DD>
**Status:** Accepted | Superseded by ADR-<N> | Deprecated

## Context
<What is the problem or situation that requires a decision?>

## Options Considered
1. **<Option A>** — <brief description>
   - Pro: <advantage>
   - Con: <disadvantage>
2. **<Option B>** — <brief description>
   - Pro: <advantage>
   - Con: <disadvantage>

## Decision
We chose **<Option X>** because <reasoning>.

## Consequences
- <What changes as a result>
- <What becomes easier>
- <What becomes harder>
- <What risks are accepted>
```

**When to use ADR vs. summary table:**
- ADR: technology choices, database selection, API design patterns, service boundaries, auth strategy — decisions that affect multiple sessions and multiple developers
- Summary table: variable naming, library version pinning, workaround choices — decisions scoped to this session

If any ADRs are created during the session, save them to `docs/decisions/adr-<number>-<slug>.md` and reference them in the handover.


**Read:** `references/consequences.md` for detailed consequences reference material.

## STEP 4: Document Pitfalls

Traps, gotchas, and "things that wasted time" discovered during the session. These are the highest-value items in a handover — they prevent the next session from hitting the same walls.


**Read:** `references/document-pitfalls.md` for detailed step 4: document pitfalls reference material.

## STEP 5: Capture Current State Snapshot

Gather the exact state of the project RIGHT NOW so the next session knows what it is working with.

### 5.1 Git State

Run these commands and record the output:

```bash
# Current branch and its relationship to main
git branch --show-current
git log --oneline main..HEAD 2>/dev/null | head -20

# Modified files (staged and unstaged)
git status --short

# Uncommitted changes summary
git diff --stat
git diff --cached --stat

# Most recent commits on current branch
git log --oneline -10

# Stashed changes
git stash list
```

Record all output in a structured format:

```markdown
### 5.2 Test Status

Run the project's test suite and record results:

```bash
# Run the targeted test suite (adjust command to project)
# Record: total, passed, failed, skipped, errors
```

Record in structured format:

```markdown
### 5.3 Environment State

Capture anything about the current environment that matters:

```markdown
### Environment
- **Running processes:** dev server on port 8080, Postgres on 5432
- **Pending PRs:** PR #45 (draft — user auth), PR #43 (ready for review — logging)
- **Open issues being worked:** #67 (token refresh), #70 (rate limiting)
- **Dependencies changed:** Added `pyjwt==2.8.0` to requirements.txt (not yet pip installed)
- **Config changes:** Updated `.env.development` with new API key (DO NOT commit)
```

## STEP 6: Build Next Steps Queue

Create a prioritized, actionable list of what to do next. Each item must have enough context that a fresh session can start immediately without re-reading the conversation.


**Read:** `references/build-next-steps-queue.md` for detailed step 6: build next steps queue reference material.

## STEP 7: Integrate External Sources


**Read:** `references/integrate-external-sources.md` for detailed step 7: integrate external sources reference material.

## STEP 8: Generate the Handover Document

Compile all gathered information into a structured markdown document.

### 8.1 Document Template

```markdown
# Session Handover — {date}

## Summary
- {3-5 bullet point overview of the session}
- {What was the main goal and how far did we get}
- {Any critical blockers or decisions that need attention}

## Since Last Handover
{Only include if a previous handover existed}
- Completed: {N}/{M} next steps from previous handover
- New decisions: {count}
- New pitfalls: {count}
- Items carried forward: {list}

## Decisions Made

| # | Decision | Reasoning | Alternatives Considered | Reversible? |
|---|----------|-----------|------------------------|-------------|
| 1 | {decision} | {why} | {alternatives} | {yes/no} |
| 2 | {decision} | {why} | {alternatives} | {yes/no} |

### Active Workarounds
{List any workarounds with context, proper fix, and tracking info}

## Pitfalls Discovered
- **{pitfall}** — {context and prevention}
- **{pitfall}** — {context and prevention}

## Current State

### Git
- **Branch:** `{branch_name}`
- **Ahead of main by:** {N} commits
- **Uncommitted changes:** {summary}
- **Stash:** {stash info or "empty"}

### Modified Files
| File | Change | State | Safe to Commit? |
|------|--------|-------|-----------------|
| {file} | {type} | {state} | {yes/no + reason} |

### Tests
- **Result:** {passed}/{total} passed, {failed} failed, {skipped} skipped
- **Failing:** {list with reasons}

### Environment
- {Running processes, pending PRs, open issues, etc.}

## Next Steps (Priority Order)

1. **[P{n}] {title}** [{complexity}]
   - **Context:** {what the next session needs to know}
   - **What to do:** {specific, actionable instructions}
   - **Test:** {how to verify}
   - **Dependencies:** {what must be done first}

2. **[P{n}] {title}** [{complexity}]
   ...

### Dependency Graph
{Visual or textual representation of dependencies between next steps}

## Learnings
- {Key insight from this session}
- {Pattern discovered}
- {Process improvement identified}

## Handoff Mail
{Free-form message from the outgoing session to the incoming session. Use this for
anything that doesn't fit neatly into the structured sections above — warnings,
hunches, morale notes, or "I was about to try X when time ran out."}

## References
- **Scratchpad:** {path, if exists}
- **Spec/Issue:** {link or path}
- **PR:** {link, if applicable}
- **Learning files:** {paths in .claude/memory/}
- **Plan companion files:** {paths to findings.md, progress.md if they exist}
- **Key files touched:** {list of important file paths}
```


**Read:** `references/references.md` for detailed references reference material.

## STEP 9: Land the Plane

Before saving the handover, ensure all work is safely persisted. Unpushed work blocks other agents and developers from continuing.

### 9.0 Pre-Handover Checklist

Run through this checklist and resolve each item:

```bash
# 1. Check for uncommitted changes
git status --short

# 2. Check if current branch is pushed
git log --oneline @{u}..HEAD 2>/dev/null | head -5
```

| Check | Action if Failing |
|-------|-------------------|
| Uncommitted changes exist | Ask user: "Commit these changes before handover?" Stage and commit with a WIP message if approved. |
| Unpushed commits exist | Ask user: "Push to remote before ending session?" Push if approved. |
| Tests are failing | Record in handover state — do NOT block handover, but flag clearly. |
| Stashed changes exist | List in handover document — easy to forget about stashes. |

**Why this matters:** If work is not pushed, the next session (or another developer/agent) cannot access it. The handover document will reference commits and branches that only exist locally, making it useless for anyone else.

If the user declines to commit or push, note it prominently in the handover:

```markdown
> ⚠ WARNING: Uncommitted changes exist that are NOT pushed to remote.
> The next session MUST be on this same machine to access this work.
```

### 9.1 Default Save Location

Save to `.claude/handover.md` in the project root:

```bash
# Ensure directory exists
mkdir -p .claude

# Write the handover document
# (Use Write tool to create .claude/handover.md)
```

### 9.2 Archive Previous Handover

If a previous handover exists and the user wants history:

```bash
# Create archive directory
mkdir -p .claude/handovers

# Archive the existing handover with its date
# Extract date from the first line of the existing handover
mv .claude/handover.md ".claude/handovers/$(date +%Y-%m-%d).md"
```

If the user does NOT explicitly request archiving, simply overwrite `.claude/handover.md`.
One current handover is sufficient for most workflows.

### 9.3 Gitignore Consideration

The handover file contains session-specific state that is typically not committed:

```bash
# Check if .claude/ is already gitignored
grep -q '.claude/handover' .gitignore 2>/dev/null
```

Suggest adding to `.gitignore` if not already present:
```
# Session handover (machine-specific, not for version control)
.claude/handover.md
.claude/handovers/
```

However, some teams may WANT to commit handovers for async collaboration. Ask the user
if unsure.

---

## STEP 10: Handover Consumption (New Session Start)

When starting a new session, check for and consume any existing handover.

### 10.1 Detection

At the beginning of a new session, check:

```bash
# Check for handover document
test -f .claude/handover.md && echo "HANDOVER EXISTS" || echo "NO HANDOVER"
```

### 10.2 Recovery from Companion Files

Even if no handover document exists (e.g., after `/clear` or a crash), check for persistent working-memory files that may contain recoverable context:

```bash
# Check for plan companion files
ls docs/plans/*-findings.md docs/plans/*-progress.md 2>/dev/null

# Check for scratchpad
ls scratchpad.md .claude/scratchpad.md 2>/dev/null

# Check for active plan files (most recently modified)
ls -t docs/plans/*-plan.md 2>/dev/null | head -3
```

If companion files exist but no handover:
1. Read the most recently modified plan, findings, and progress files
2. Cross-reference with `git log --oneline -10` to understand recent work
3. Present a reconstructed summary to the user:

> No handover document found, but I recovered context from working files:
>
> **Active plan:** `docs/plans/{name}-plan.md` (last modified {date})
> **Findings:** {count} entries in `{name}-findings.md`
> **Progress:** Last entry: "{last progress line}"
>
> Would you like to continue from where this left off?

This is a fallback — a proper `/handover` document is always preferred.

## STEP 11: Diff from Previous Handover

When generating a new handover and a previous one exists, compute and present the delta.

### 11.1 Progress Tracking

Compare previous handover's next steps against current session's completed work:

```markdown
## Since Last Handover ({previous_date})


**Read:** `references/since-last-handover-previousdate.md` for detailed since last handover ({previous_date}) reference material.

## CRITICAL RULES

### MUST DO

- Always gather CURRENT git state and test results — never rely on memory from earlier in the session
- Always include enough context in each next-step item that a fresh session can start immediately
- Always deduplicate across sections — a pitfall should not also appear verbatim in decisions
- Always check for a previous handover and compute the diff if one exists
- Always ask the user before generating — never auto-generate without confirmation
- Always include file paths as absolute or repo-relative — never use vague references like "the auth file"
- Always record failed approaches — knowing what DIDN'T work is as valuable as knowing what did
- Always include the branch name and its relationship to main
- Always verify file paths exist before referencing them in the handover
- Always run tests if feasible to capture current test state accurately

### MUST NOT DO

- MUST NOT dump raw conversation history — curate and summarize instead
- MUST NOT include sensitive data (API keys, passwords, tokens) in the handover — reference `.env` files by path only
- MUST NOT make the handover longer than necessary — a 200-line handover with high signal beats a 500-line handover with noise
- MUST NOT skip the next-steps section — this is the most critical section for session continuity
- MUST NOT assume the next session has any context beyond this document and the codebase
- MUST NOT include code snippets longer than 10 lines — reference the file and line numbers instead
- MUST NOT generate a handover if no meaningful work was done — tell the user "No significant work to hand over"
- MUST NOT overwrite a previous handover without reading it first — the diff section requires it
- MUST NOT include timestamps more granular than the date — session start/end times are noise
- MUST NOT treat the handover as a commit message or changelog — it is a CONTEXT TRANSFER document, not a record of changes

