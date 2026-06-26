# Plan: Interactive branch-choice menu + stale-branch reaper

**Status:** spec locked, awaiting owner go-ahead to implement
**Owner:** Abhay
**Date:** 2026-06-26

## Goal

Replace the current *silent* branch auto-rotation (auto-git Guardrails 1/1b) with an
**owner-driven, once-per-session interactive menu** shown at the first file-changing edit,
plus a **24h stale-branch reaper** that offers (with approval) to land long-idle branches.
Grounded in trunk-based development: one logical change = one short-lived branch off `main`.

## Locked behaviour (agreed with owner)

1. **Open a session, make no edits → no branch is created or touched.**
2. **At the first file-changing edit of a session** (read-only/question turns never trigger it),
   if a branch decision has not yet been made this session, **present a menu and act on the answer.**
   Asked **once per session**, then remembered for the rest of the session.
3. **Menu options:**
   1. New branch from `main` *(recommended for new/unrelated work)*
   2. Keep using the existing branch *(continue same work)* — hidden if that branch is already merged
   3. Switch to another existing branch (pick from a list)
   4. Merge the existing branch to `main` (re-checked CI-green first), then new branch from `main`
   5. Stash current changes and decide first
4. **Every new branch is cut from fresh `origin/main`** (fetch first).
5. **Decorate the menu** with each branch's age · last commit msg · CI status · ahead/behind main.
6. **Propose a meaningful branch name** (from the work), owner can accept/rename.
7. **24h stale-branch reaper** at session start: any branch whose last commit is >24h old:
   - finished + CI-green-against-current-main → **ask** owner → CI-gated merge + delete
   - unfinished / CI-red / conflicts → **flag only**, never merge
   - batched into ONE summary prompt (no per-branch spam)
8. **Optional silent mode** (off by default): a setting to auto-pick "new from main" without prompting.

## KEY IMPLEMENTATION CONSTRAINT (discovered during design)

A Stop-hook shell script (`auto-git.sh`) runs **non-interactively** — it CANNOT show a menu and
wait for the owner. Therefore the **ASK lives at the model/rule layer**, not in the shell:

- **A new rule** (`.claude/rules/branch-choice.md`, `# Scope: global`) instructs Claude: before the
  first file edit of a session, if no branch-choice marker exists, present the menu, act on the
  answer, then write a session-scoped marker `.claude/.branch-choice-<sessionid>` (gitignored).
- **`auto-git.sh` changes:** stop the silent Guardrail-1b rotation; instead RESPECT the branch the
  model selected. KEEP Guardrail 1 ("never commit to main") as a pure safety net — if the model
  ever forgets to ask and we're on main, it still creates a branch rather than dirtying main.
- **Reaper:** a script (`.claude/hooks/stale-branch-reaper.sh`) run at SessionStart REPORTS stale
  branches with metadata; the rule tells Claude to present that report for batched approval, then
  call `session-git-landing.sh` to land the approved ones.

## Files to change

| File | Change |
|---|---|
| `.claude/rules/branch-choice.md` | NEW — the model-layer "ask at first edit" + reaper-approval rule |
| `.claude/hooks/auto-git.sh` | Remove silent 1b rotation; respect model's branch choice; keep main-safety net; read session marker |
| `.claude/hooks/stale-branch-reaper.sh` | NEW — list branches with last-commit-age >24h + metadata (read-only report) |
| `.claude/hooks/session-git-landing.sh` | Add a `merge-one <branch>` path used by option 4 + reaper (re-checks CI-green vs current main) |
| `.claude/skills/start-session/SKILL.md` | STEP 0: also surface the reaper report for approval |
| `.gitignore` | ignore `.claude/.branch-choice-*` markers |
| `.claude/settings.json` | wire `stale-branch-reaper.sh` at SessionStart |
| registry/patterns.json + tests | register the new rule/hook; add unit tests |

## Edge cases + rulings (from adversarial review)

- **Concurrency (two sessions, one folder):** *Assumption* — detect another active session and
  recommend a git worktree for the 2nd; never two writers on one checked-out branch.
- **Reaper timing:** *Assumption* — session-start-only for now (no paid daemon); documented limitation.
- **Stale-green ≠ safe:** option 4 + reaper always re-fetch + re-check CI vs current `main` before merging.
- **Green ≠ finished:** reaper never auto-merges on green alone — always owner-approved, shows diff summary.
- **Stale local main:** always `git fetch` before cutting a new branch.
- **Carried uncommitted edits:** moved onto the chosen new branch; if they fail to apply cleanly, stash + warn.
- **Human-made branches (`feat/...`):** menu offers "keep" but never force-rotates off a non-`auto/*` branch silently.
- **Read-only turns:** the menu fires only when there is a real file diff to commit.

## Verification plan

- Unit tests for `stale-branch-reaper.sh` (age detection, metadata, red/green classification).
- Unit tests for `session-git-landing.sh merge-one` (refuses red/stale; merges green).
- Dry-run the rule against scenarios: open+no-edit (no branch), first-edit menu, option 1–5 each,
  reaper with mixed green/red branches.
- Full local CI (dedup, secret-scan, pattern-gate, pytest) before PR.

## Open (recommended defaults applied unless owner overrides)

- Concurrency → worktree for 2nd session (vs hard-refuse).
- Reaper timing → session-start-only (vs scheduled cloud agent later).
