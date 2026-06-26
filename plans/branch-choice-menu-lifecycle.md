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

- **A hub-only SKILL** (`.claude/skills/branch-choice/SKILL.md`) holds the menu + reaper-approval
  procedure. (Hub rules are capped to a lean approved set of 6 by `test_rule_organization.py`;
  verbose procedure belongs in a skill, same as `git-branch-lifecycle`.) The reaper prints a
  `BRANCH-CHOICE:` SessionStart nudge so the model runs the skill before the first edit; the skill
  gates on the marker `.claude/.branch-choice-active` (gitignored) for once-per-session.
- **`auto-git.sh` changes:** stop the silent Guardrail-1b rotation; instead RESPECT the branch the
  model selected. KEEP Guardrail 1 ("never commit to main") as a pure safety net — if the model
  ever forgets to ask and we're on main, it still creates a branch rather than dirtying main.
- **Reaper:** a script (`.claude/hooks/stale-branch-reaper.sh`) run at SessionStart REPORTS stale
  branches with metadata; the rule tells Claude to present that report for batched approval, then
  call `session-git-landing.sh` to land the approved ones.

## Files to change

| File | Change | Done |
|---|---|---|
| `.claude/skills/branch-choice/SKILL.md` | NEW — model-layer "ask at first edit" menu + reaper-approval procedure (hub-only skill) | ✅ |
| `.claude/hooks/stale-branch-reaper.sh` | NEW — SessionStart: reset marker + `BRANCH-CHOICE:` nudge + read-only report of branches idle >24h with metadata | ✅ |
| `.claude/hooks/session-git-landing.sh` (+ core synced copy) | Add a `merge-one <branch>` path (CI-gated) used by option 4 + reaper approvals | ✅ |
| `.gitignore` | ignore `.claude/.branch-choice-active` marker | ✅ |
| `.claude/settings.json` | wire `stale-branch-reaper.sh` at SessionStart | ✅ |
| registry/patterns.json | resync `session-git-landing` hash + last_updated (reaper + skill are hub-only → not registered, per the `auto-pr-reconcile` precedent) | ✅ |
| `scripts/tests/test_stale_branch_reaper.py` | NEW — 16 guards (report-only, marker reset, 24h threshold, off-switch, skill once-per-session/new-from-main/approval, merge-one CI-gated, core-synced) | ✅ |

**auto-git.sh left unchanged** (KISS): its Guardrail-1b only rotates off *already-merged* branches
(always safe), and the skill now front-runs the branch decision, so the silent path never conflicts
with an owner choice. Guardrail 1 ("never commit to main") stays as the backstop.

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

## Follow-ups (built after owner flagged the goal was only partially met)

- ✅ **PreToolUse enforcement** — `branch-choice-gate.sh` (Edit|Write|MultiEdit) re-injects the menu
  reminder at the exact first edit, marker-gated, non-blocking. Closes the "SessionStart nudge can rot" gap.
- ✅ **Concurrency guard** — `session-concurrency-guard.sh` (SessionStart) warns when another session
  (by `session_id`, lock-file heuristic, < `CONCURRENCY_STALE_MIN`) shares the working tree → recommends a worktree.
- ✅ **Reaper-as-scheduler (#7) — RESOLVED (owner decided 2026-06-26): DECLINED.** Do NOT fire the
  24h sweep from outside a Claude session. It runs ONLY from a session (SessionStart) and therefore
  stays free — no scheduled cloud agent, no recurring spend. This is the final, intended behavior.

## Status: COMPLETE. All agreed parts built + merged (#217, #218); #7 is an explicit owner decision, not a gap.
