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
at the model layer (this skill). The companion hooks are the unattended safety net: `auto-git.sh`
still refuses to commit onto `main` (carries work to a fresh branch as a backstop), and
`stale-branch-reaper.sh` (SessionStart) clears the per-session marker + reports stale branches and
prints a `BRANCH-CHOICE:` nudge so you run this skill before the first edit.

## STEP 1: Gate — ask ONCE per session

Before the FIRST `Edit`/`Write`/`MultiEdit` of a session (read-only / question / analysis turns
NEVER trigger this), check the marker `.claude/.branch-choice-active`:

- **Marker present** → a choice was already made this session. Proceed on the current branch; do NOT re-ask.
- **Marker absent** → run STEP 2, then create the marker: `touch .claude/.branch-choice-active`
  (gitignored). `stale-branch-reaper.sh` deletes it at every SessionStart, so each new session re-asks.

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

- MUST present the menu at the first file-edit of a session when `.claude/.branch-choice-active`
  is absent; MUST then create the marker so it is asked ONCE per session.
- MUST cut every NEW branch from fresh `origin/main` (fetch first), never from another feature branch.
- MUST hide "keep existing" when that branch is already merged.
- MUST NOT trigger on read-only / question / analysis turns — only on a real file change.
- MUST get explicit owner approval before landing any stale branch; MUST NOT merge red/unfinished work.
- Honors pre-authorization: if the owner delegated ("you decide" / silent mode), pick option 1
  (new from `main`) with a derived name and state the choice as an assumption — do not block.
