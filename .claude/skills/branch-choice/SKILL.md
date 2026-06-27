---
name: branch-choice
description: >
  Present the once-per-session branch menu at the FIRST file edit of a session
  (new from main / keep existing / switch / merge-then-new / stash) and handle
  owner-approved landing of stale (>24h) branches reported by the stale-branch
  reaper. Use before the first file change of a session, or when the reaper
  reports STALE_BRANCH lines needing approval.
type: workflow
allowed-tools: "Bash Read"
argument-hint: "(auto-triggered; no arguments)"
version: "1.0.0"
triggers:
  - branch choice
  - branch menu
  - which branch
  - first edit branch
  - stale branch approval
---

# Branch Choice — owner-driven, once-per-session

A Stop-hook shell script cannot pause for an interactive answer, so the branch decision lives
at the model layer (this skill). Four companion hooks form the unattended safety net:
- `auto-git.sh` still refuses to commit onto `main` (carries work to a fresh branch as a backstop).
- `stale-branch-reaper.sh` (SessionStart) clears the per-session marker + reports stale branches + prints the `BRANCH-CHOICE:` nudge.
- `branch-choice-gate.sh` (PreToolUse Edit|Write|MultiEdit) re-injects this reminder at the EXACT first file edit (deterministic — survives a long session where the SessionStart nudge rots), non-blocking, silent once the marker exists.
- `session-concurrency-guard.sh` (SessionStart) warns when another session shares the working tree and recommends a worktree (two sessions = one checked-out branch = collisions).

## STEP 1: Gate — ask ONCE per session

Before the FIRST `Edit`/`Write`/`MultiEdit` of a session (read-only / question / analysis turns
NEVER trigger this), check THIS session's marker `.claude/.branch-choice-active.<session_id>` — the
gate hook (`branch-choice-gate.sh`) prints the exact path in its reminder. The marker is keyed by
session id so concurrent sessions sharing one working tree never silence each other's menu:

- **This session's marker present** → a choice was already made this session. Proceed on the current branch; do NOT re-ask.
- **Marker absent** → run STEP 2, then create it: `touch .claude/.branch-choice-active.<session_id>`
  (gitignored) using the exact filename from the gate's reminder. A new session has a new id, so it
  re-asks automatically; `stale-branch-reaper.sh` GCs old markers.
- **Gate flags another live session** (its reminder carries a `CONCURRENCY:` note) → two sessions
  share ONE checked-out branch and WILL collide. Isolate this work in a git worktree first
  (`/git-branch-lifecycle work <name>`), then pick the branch there.

## STEP 2: Present the menu

Show the existing branch (if any) WITH context — age · last commit subject · CI/PR state ·
ahead/behind `main` — then offer:

1. **New branch from `main`** *(recommended for new / unrelated work)* — `git fetch origin main`
   then `git checkout -b <name> origin/main`. Propose a meaningful `<name>` from the work
   (`feat/...`, `fix/...`); the owner may accept or rename. Avoid a bare timestamp when a
   descriptive name is derivable.
2. **Keep the existing branch** *(continue the same work)* — stay on it. **Hide this option when
   that branch is already merged** (reusing a dead branch is invalid → only option 1 applies).
3. **Switch to another existing branch** — list open branches; checkout the chosen one.
4. **Merge the existing branch to `main`, then new branch** — land it via
   `session-git-landing.sh merge-one <branch>` (CI-gated; refuses red/stale), then option 1.
5. **Stash current changes and decide first** — `git stash` the edits, present state, wait.

If there is NO existing non-main branch, the menu collapses to option 1 (cut a fresh branch from
`main`) — still confirm the name unless pre-authorized.

Carry any uncommitted edits onto the chosen branch; if they fail to apply cleanly, stash + warn.
Only auto-suggest rotating off `auto/work-*` branches — never silently yank the owner off a
hand-named branch (`feat/...`); offer "keep" for those.

## STEP 3: Stale-branch approval (reaper)

At SessionStart, `stale-branch-reaper.sh` prints `STALE_BRANCH | <br> | age | ahead/behind | ci | last`
lines for branches idle > `STALE_BRANCH_HOURS` (default 24h). When such lines appear, present them
to the owner as ONE batched prompt:

- **Green + clean** (CI passed, no conflicts vs current `main`) → offer to land via
  `session-git-landing.sh merge-one <br>` on the owner's approval.
- **Red / unfinished / conflicted** → FLAG only with the reason; NEVER merge broken work to `main`,
  even if asked — surface the failing check and let the owner resume or drop it.

Merging stale work to `main` is consequential → it is ALWAYS owner-approved, never silent.

## CRITICAL RULES

- MUST present the menu at the first file-edit of a session when THIS session's
  `.claude/.branch-choice-active.<session_id>` marker is absent; MUST then create it so it is asked ONCE per session.
- MUST, when the gate flags a concurrent live session, isolate in a git worktree rather than two sessions sharing one checked-out branch.
- MUST cut every NEW branch from fresh `origin/main` (fetch first), never from another feature branch.
- MUST hide "keep existing" when that branch is already merged.
- MUST NOT trigger on read-only / question / analysis turns — only on a real file change.
- MUST get explicit owner approval before landing any stale branch; MUST NOT merge red/unfinished work.
- Honors pre-authorization: if the owner delegated ("you decide" / silent mode), pick option 1
  (new from `main`) with a derived name and state the choice as an assumption — do not block.
