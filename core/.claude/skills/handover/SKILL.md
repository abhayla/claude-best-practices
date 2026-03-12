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

### 1.4 Auto-Detection of Session End

Watch for signals that the user is wrapping up:

| Signal | Example Phrases |
|--------|----------------|
| **Explicit stop** | "let's stop", "that's enough", "let's wrap up", "I'm done for today" |
| **Time reference** | "continue tomorrow", "pick this up later", "next session" |
| **Parking** | "let's park this", "save progress", "bookmark where we are" |
| **Handover request** | "handover", "session summary", "what should I tell the next session" |

When any of these signals are detected, suggest:

> "Would you like me to generate a handover document before we stop? This will help the next session pick up exactly where we left off."

Do NOT generate automatically — always ask first. The user may want to do more work before stopping.

---

## STEP 2: Review the Session

Systematically scan the conversation to extract what happened during this session.

### 2.1 Catalog All Work Attempted

Review the full conversation history and categorize every task:

```
Session Work Catalog:
  COMPLETED:
    - [task description] — [outcome summary]
    - [task description] — [outcome summary]

  IN PROGRESS:
    - [task description] — [current state, what remains]

  FAILED / ABANDONED:
    - [task description] — [why it failed, what was tried]

  DEFERRED:
    - [task description] — [why deferred, prerequisites]
```

Be thorough. Scan from the beginning of the conversation. Include:
- Feature implementations
- Bug investigations and fixes
- Configuration changes
- Research and exploration
- Refactoring
- Test additions or modifications
- Documentation updates
- Failed attempts (these are especially valuable for the next session)

### 2.2 Extract Key Interactions

Identify conversation moments that carry context the next session needs:

| Type | What to Capture | Example |
|------|----------------|---------|
| **User corrections** | When the user redirected your approach | "User said: don't modify that file, it's auto-generated" |
| **Scope changes** | When requirements shifted mid-session | "Originally asked for X, pivoted to Y because of Z" |
| **Blocked moments** | When progress stalled and why | "Blocked on API response format — docs were wrong" |
| **Explicit preferences** | User preferences revealed during work | "User prefers integration tests over unit tests for this module" |
| **Rejected approaches** | Approaches considered but not taken | "Considered using Redis but user wants to keep deps minimal" |

### 2.3 Measure Progress

If working from a spec, issue, or previous handover's next-steps list:

```
Progress Against Plan:
  Original items: N
  Completed: X
  Partially done: Y
  Not started: Z
  New items added: W

  Completion rate: X/N (percentage)
```

This gives the next session a clear sense of momentum and what remains.

---

## STEP 3: Build the Decision Log

Record every non-trivial decision made during the session. A "non-trivial" decision is anything where an alternative existed and reasoning was required.

### 3.1 Decision Categories

| Category | Examples |
|----------|---------|
| **Architecture** | "Used event-driven approach instead of polling" |
| **Library/Tool choice** | "Chose pydantic over dataclasses for validation" |
| **Algorithm** | "Used binary search instead of linear scan — data is always sorted" |
| **Workaround** | "Used env var override because config system doesn't support per-env values yet" |
| **Scope** | "Skipped edge case X — not in the current requirements" |
| **Testing strategy** | "Mocked the external API instead of using the sandbox — sandbox is unreliable" |
| **Trade-off** | "Accepted O(n) memory for O(1) lookup — dataset is small enough" |

### 3.2 Decision Record Format

For session-level decisions (tactical), use the summary table:

```markdown
| Decision | Reasoning | Alternatives Considered | Reversible? |
|----------|-----------|------------------------|-------------|
| Used SQLite for local cache | Low overhead, no server needed | Redis (overkill), file-based JSON (too slow for queries) | Yes — swap storage backend |
| Pinned dependency X to v2.3 | v3.0 has breaking change in API we use | Upgrade and refactor (too risky mid-sprint) | Yes — upgrade later |
```

### 3.3 Architecture Decision Records (ADR)

For architecture-level decisions (strategic, long-lasting), use the full ADR format. These persist beyond a single session and should be saved to `docs/decisions/` for the team.

```markdown
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

### 3.4 Workaround Registry

Workarounds deserve special attention because they are technical debt with context:

```markdown
### Active Workarounds

1. **What:** Hardcoded timeout to 30s in API client
   **Why:** Upstream service has undocumented rate limiting at ~100 req/min
   **Proper fix:** Implement exponential backoff with retry
   **Tracked in:** Issue #789
   **Risk if forgotten:** Silent failures when request volume increases

2. **What:** Disabled SSL verification for staging environment
   **Why:** Staging cert expired, renewal blocked on ops team
   **Proper fix:** Renew the staging certificate
   **Tracked in:** Ops ticket INFRA-234
   **Risk if forgotten:** Security vulnerability if accidentally enabled in production
```

---

## STEP 4: Document Pitfalls

Traps, gotchas, and "things that wasted time" discovered during the session. These are the highest-value items in a handover — they prevent the next session from hitting the same walls.

### 4.1 Pitfall Categories

| Category | Description | Example |
|----------|-------------|---------|
| **Environment** | Setup/config surprises | "Docker must be running before test suite — no helpful error if it isn't" |
| **Documentation lies** | Docs that are wrong or misleading | "API docs say rate limit is 1000/min — actual limit is 100/min" |
| **Hidden dependencies** | Implicit requirements | "Build script assumes Node 18+ — fails silently on Node 16" |
| **Ordering traps** | Things that must happen in sequence | "Must run migrations before seeding — seed script doesn't check" |
| **Naming confusion** | Misleading names in codebase | "`user.active` doesn't mean currently online — it means account not deleted" |
| **Side effects** | Unexpected consequences of actions | "Don't modify config.yml directly — overwritten by build script on deploy" |
| **Timing issues** | Race conditions or sequencing bugs | "CI flakes if test A and test B run in parallel — shared temp directory" |
| **Data quirks** | Unexpected data characteristics | "Customer names can contain emoji — breaks CSV export if not handled" |

### 4.2 Pitfall Format

For each pitfall:

```markdown
**Pitfall:** [Short description]
**Context:** [When/how you encountered it]
**Impact:** [What went wrong or how much time was wasted]
**Prevention:** [How to avoid it next time]
**Permanent fix:** [If applicable — how to fix the root cause so it's not a pitfall anymore]
```

### 4.3 Real-World Examples

Here are examples of well-documented pitfalls to use as templates:

```markdown
## Pitfalls Discovered

- **Don't modify `config/settings.yml` directly** — it is overwritten by the
  build script (`scripts/build.sh:47`). Edit `config/settings.template.yml`
  instead and run `scripts/generate-config.sh`.

- **API rate limit is 100/min, not 1000/min** — the official docs at
  `docs.example.com/limits` are outdated. Discovered by hitting 429 errors
  during integration testing. Workaround: added 600ms delay between requests
  in `src/api/client.py:89`.

- **Test suite requires Docker running locally** — the `test_integration_*`
  tests connect to a Postgres container. No helpful error message if Docker
  is down — tests just hang for 30s then fail with "connection refused."
  Run `docker compose up -d` before testing.

- **The `user.email` field can be null** — despite the schema saying NOT NULL,
  legacy users imported from the old system have null emails. The migration
  (`migrations/005_import_legacy.py`) skipped email validation.
  Always null-check `user.email` before using it in notifications.

- **Branch `feature/auth-v2` has diverged significantly from main** — do NOT
  rebase, it will create 47 conflicts. Merge main into the branch instead.
  Last tested merge: clean as of commit `abc1234`.

- **`npm install` fails on Apple Silicon without Rosetta** — native dependency
  `better-sqlite3` needs `arch -x86_64` prefix. Or install from source with
  `npm install --build-from-source`.
```

---

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
### Git State
- **Branch:** `feature/user-auth`
- **Ahead of main by:** 3 commits
- **Uncommitted changes:** 2 files modified, 1 file untracked
- **Staged:** `src/auth/handler.py` (modified)
- **Unstaged:** `tests/test_auth.py` (modified)
- **Untracked:** `src/auth/tokens.py` (new file)
- **Stash:** 1 entry — "WIP: experimental caching approach"
```

### 5.2 Test Status

Run the project's test suite and record results:

```bash
# Run the targeted test suite (adjust command to project)
# Record: total, passed, failed, skipped, errors
```

Record in structured format:

```markdown
### Test Status
- **Suite:** `pytest tests/ -v`
- **Result:** 47 passed, 2 failed, 3 skipped
- **Failing tests:**
  - `test_auth_token_refresh` — expects 200, gets 401 (known issue, in progress)
  - `test_email_notification` — SMTP mock not configured (pre-existing)
- **Skipped tests:**
  - `test_integration_db` — requires Docker (skipped in local dev)
```

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

### 5.4 Uncommitted Work Assessment

For each uncommitted change, assess its state:

| File | Change Type | State | Safe to Commit? | Notes |
|------|------------|-------|-----------------|-------|
| `src/auth/handler.py` | Modified | Working, tested | Yes | Token refresh logic |
| `tests/test_auth.py` | Modified | Incomplete | No | Missing edge case tests |
| `src/auth/tokens.py` | New | Untested | No | Needs unit tests first |

---

## STEP 6: Build Next Steps Queue

Create a prioritized, actionable list of what to do next. Each item must have enough context that a fresh session can start immediately without re-reading the conversation.

### 6.1 Priority Framework

| Priority | Criteria | Examples |
|----------|----------|---------|
| **P0 — Blocking** | Must be done before anything else works | Fix broken build, resolve merge conflict |
| **P1 — Critical** | Core functionality, test failures | Complete the feature, fix failing tests |
| **P2 — Important** | Quality, robustness, edge cases | Add error handling, write missing tests |
| **P3 — Nice to Have** | Cleanup, optimization, documentation | Refactor, update docs, optimize query |

### 6.2 Next Step Format

Each item must include:

```markdown
1. **[P1] Complete token refresh endpoint** [medium]
   - **Context:** Handler is implemented in `src/auth/handler.py:45-80` but
     missing error handling for expired refresh tokens.
   - **What to do:** Add try/catch around `jwt.decode()` call. Return 401 with
     `{"error": "refresh_token_expired"}` body. See existing pattern in
     `src/auth/login.py:30`.
   - **Test:** `pytest tests/test_auth.py::test_token_refresh -v`
   - **Dependencies:** None
   - **Blockers:** None

2. **[P1] Fix failing test `test_auth_token_refresh`** [quick]
   - **Context:** Test expects 200 but gets 401 because refresh endpoint
     is not yet handling the happy path correctly.
   - **What to do:** This will auto-resolve when item #1 is completed.
   - **Dependencies:** Depends on #1

3. **[P2] Add edge case tests for token expiry** [medium]
   - **Context:** Current tests only cover happy path. Need tests for:
     expired token, malformed token, missing token, revoked token.
   - **What to do:** Add 4 test cases in `tests/test_auth.py`. Use the
     `expired_token_fixture` in `tests/conftest.py:15`.
   - **Dependencies:** Complete after #1

4. **[P3] Refactor auth middleware to use dependency injection** [complex]
   - **Context:** Currently hardcoded to use `JWTValidator`. Should accept
     any validator implementing `AuthValidator` protocol.
   - **What to do:** Define protocol in `src/auth/protocols.py`, update
     middleware constructor, update all call sites.
   - **Dependencies:** Complete after #1-3
   - **Blockers:** Need user input on whether to use Protocol or ABC
```

### 6.3 Complexity Estimates

| Estimate | Meaning | Typical Time |
|----------|---------|-------------|
| **quick** | Single file change, clear path | < 15 minutes |
| **medium** | Multiple files, some investigation needed | 15-60 minutes |
| **complex** | Architecture decisions, multiple components | 1+ hours |

### 6.4 Dependency Graph

If next steps have dependencies, make them explicit:

```
Dependency Graph:
  #1 (token refresh) ──→ #2 (fix test) ──→ #3 (edge case tests)
                                                    │
  #4 (DI refactor) ←────────────────────────────────┘

  Independent: #5, #6 can be done in any order
```

---

## STEP 7: Integrate External Sources

### 7.1 Scratchpad Integration

If `scratchpad.md` or `.claude/scratchpad.md` exists:

1. **Read the scratchpad** and identify entries from this session
2. **Extract and deduplicate:**
   - Gotchas → merge into Pitfalls section (avoid duplication)
   - Judgment calls → merge into Decisions section
   - Questions answered → include answer in relevant section
   - Questions unanswered → add to Next Steps as research items
   - File discovery notes → include in Current State if relevant
3. **Reference for depth:** Add a pointer to the scratchpad for raw details:
   > "For full exploration notes and intermediate findings, see `scratchpad.md`"
4. **Do NOT copy the entire scratchpad** — curate and summarize. The handover
   should be a refined distillation, not a raw dump.

### 7.2 Learn-n-Improve Integration

If `/learn-n-improve` was run during this session or learning files exist:

1. **Extract session learnings** from memory files (entries with today's date)
2. **Categorize learnings:**

   | Type | Example | Action |
   |------|---------|--------|
   | **Fix pattern** | "Null check needed before `.email` access on legacy users" | Include in Pitfalls + Learnings |
   | **Testing lesson** | "Mock SMTP server with `smtplib.SMTP` not `aiosmtplib`" | Include in Learnings |
   | **Skill gap** | "Need to learn project's migration framework" | Include in Next Steps as research |
   | **Process improvement** | "Run integration tests before pushing — CI is slow" | Include in Learnings |

3. **Reference learning files:**
   > "Session learnings have been saved to `.claude/memory/`. Key entries:
   > - `fix-patterns.md`: 2 new patterns added
   > - `testing-lessons.md`: 1 new lesson added"

### 7.3 Specification / Issue Integration

If working from a spec, issue, or ticket:

1. **Link to the source:** Include the issue URL, spec file path, or ticket ID
2. **Map progress:** Which requirements/acceptance criteria are met vs remaining
3. **Note deviations:** Where the implementation differs from the spec and why

```markdown
### Spec Progress: Issue #67 — Token Refresh
- [x] Implement refresh endpoint (`POST /auth/refresh`)
- [x] Validate refresh token signature
- [ ] Handle expired refresh tokens (in progress)
- [ ] Rate limit refresh requests (not started)
- [ ] Add audit logging for refresh events (not started)

**Deviation:** Spec says "return 403 for expired tokens" but the team convention
(see `src/auth/login.py`) uses 401. Using 401 for consistency — flag for review.
```

---

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

### 8.2 Quality Checklist

Before saving, verify the handover passes these checks:

| Check | Criteria |
|-------|----------|
| **Actionable next steps** | Can a fresh session start item #1 immediately without asking questions? |
| **No orphan references** | Every file path, issue number, and URL referenced actually exists? |
| **Decision completeness** | Every non-trivial decision has reasoning documented? |
| **Pitfall specificity** | Each pitfall has enough detail to prevent the next session from repeating it? |
| **State accuracy** | Git state, test results, and env state are current (not stale from earlier in session)? |
| **Deduplication** | No information repeated across sections? |
| **Concise summaries** | Summary section is 3-5 bullets, not a wall of text? |
| **Complexity estimates** | Every next step has a complexity tag? |

### 8.3 Length Guidelines

| Section | Target Length | Notes |
|---------|-------------|-------|
| Summary | 3-5 lines | High-level only |
| Since Last Handover | 3-8 lines | Skip if no previous handover |
| Decisions | 1 row per decision | Include all non-trivial decisions |
| Workarounds | 1 block per workaround | Include risk if forgotten |
| Pitfalls | 2-3 lines each | Specific and preventive |
| Current State | As needed | Accuracy over brevity |
| Next Steps | 4-8 items typical | Each must be self-contained |
| Learnings | 3-6 items | Only actionable insights |
| References | All relevant paths/links | Completeness matters |

---

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

### 10.3 Resumption Protocol

If a handover exists:

1. **Read the handover document**
2. **Read the Handoff Mail section first** — it contains the outgoing session's most important unstructured context
3. **Present a brief summary to the user:**

   > Resuming from handover dated {date}.
   >
   > **Last session:** {summary in 1-2 sentences}
   >
   > **Next steps queued:**
   > 1. [P1] {first item} [complexity]
   > 2. [P1] {second item} [complexity]
   > 3. [P2] {third item} [complexity]
   >
   > **Active pitfalls:** {count} — will avoid these.
   > **Active workarounds:** {count} — aware of these.
   >
   > Continue from next steps, or would you like to start fresh?

3. **Wait for user direction** — do NOT auto-start work. The user may:
   - Continue from the queued next steps
   - Reprioritize the next steps
   - Start something entirely different
   - Ask for details on a specific section

### 10.4 Stale Handover Detection

A handover may be stale if:

| Signal | Threshold | Action |
|--------|-----------|--------|
| **Age** | > 7 days old | Warn: "This handover is {N} days old — the codebase may have changed." |
| **Branch mismatch** | Handover branch != current branch | Warn: "Handover was written on branch `X`, but you are on branch `Y`." |
| **Git state mismatch** | Files listed in handover no longer modified | Warn: "Some changes listed in the handover appear to have been committed or reverted." |

For stale handovers:
1. Read the handover for context (decisions and pitfalls are still valuable)
2. Re-gather current state (git, tests, env) instead of trusting the handover's state section
3. Cross-reference next steps against what has changed

### 10.5 Multi-Developer Handover

If the handover was written by a different developer or agent session:

1. Treat decisions and pitfalls as authoritative context
2. Verify current state independently (git status, run tests)
3. Treat next steps as suggestions, not directives — the new developer may have
   different priorities
4. Note any user-preference entries (these are specific to the original user)

---

## STEP 11: Diff from Previous Handover

When generating a new handover and a previous one exists, compute and present the delta.

### 11.1 Progress Tracking

Compare previous handover's next steps against current session's completed work:

```markdown
## Since Last Handover ({previous_date})

### Next Steps Progress
| # | Item | Status | Notes |
|---|------|--------|-------|
| 1 | Complete token refresh endpoint | DONE | Implemented in commit `abc1234` |
| 2 | Fix failing test | DONE | Auto-resolved by #1 |
| 3 | Add edge case tests | PARTIAL | 2/4 cases covered |
| 4 | Refactor auth middleware | NOT STARTED | Deferred — user wants to ship first |

### New Items This Session
- 2 new decisions added
- 3 new pitfalls discovered
- 1 workaround added (API timeout)

### Carried Forward
- Edge case tests (2 remaining)
- Auth middleware refactor
- SMTP mock configuration (from 2 sessions ago)
```

### 11.2 Decision Evolution

Track how decisions evolved across sessions:

```markdown
### Decision Updates
- **Decision #3 (Auth approach):** Previously "use JWT only" →
  Updated to "JWT + session fallback for legacy clients" (reason: legacy
  mobile app cannot handle JWT refresh flow)
```

### 11.3 Pitfall Resolution

Track which pitfalls from previous sessions have been resolved:

```markdown
### Pitfall Status
- **RESOLVED:** "Docker must be running for tests" → Added Docker health
  check to test setup (`conftest.py:5`) with helpful error message
- **STILL ACTIVE:** "API rate limit is 100/min not 1000/min"
- **NEW:** "Don't run `make clean` in CI — deletes cached test fixtures"
```

---

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

### FORMAT RULES

- Use markdown tables for structured data (decisions, file states, progress tracking)
- Use bullet points for lists (pitfalls, learnings, references)
- Use numbered lists only for ordered sequences (next steps, priority queues)
- Use code blocks for commands, file paths, and code references
- Use bold for emphasis on key terms, not for decoration
- Keep the Summary section to 3-5 bullets maximum
- Keep each pitfall to 2-4 lines maximum
- Keep each next-step item self-contained — it should make sense without reading other items
