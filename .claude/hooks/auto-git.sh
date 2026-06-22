#!/usr/bin/env bash
# Autonomous git handler — so the user never touches git.
#
# Wired into SessionStart + Stop. Runs after each completed task and at session start.
# Behaviour: if the working tree has changes, secret-scan -> stage -> commit with a
# generated message -> push the current branch -> open a PR if one is missing and the branch
# is ahead of main (CREATE only; auto-pr.sh still arms CI-gated auto-merge at SessionEnd, so
# work never merges mid-session). This keeps long / `/clear`-reset sessions from leaving work
# un-PR'd until a clean session close that may never come.
#
# FAIL-SAFE: always exits 0 (a git hiccup must never block the session).
# GUARDRAILS:
#   1. Never auto-commits onto main/master — moves the work to a fresh branch first.
#   2. Secret-scans before staging; aborts the commit if it is not confirmed clean.
#   3. Pushes the current branch only, never --force.
# OFF-SWITCHES:
#   AUTO_GIT_DISABLE=1  -> do nothing at all.
#   AUTO_GIT_PUSH=0     -> commit locally but do not push.

set -uo pipefail

[ "${AUTO_GIT_DISABLE:-0}" = "1" ] && exit 0

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
cd "$ROOT" || exit 0

LOG="$ROOT/.claude/.auto-git.log"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" >> "$LOG" 2>/dev/null; }

# Nothing to do on a clean tree — this naturally limits commits to real changes.
[ -z "$(git status --porcelain 2>/dev/null)" ] && exit 0

branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)" || exit 0

# Guardrail 1: keep main/master clean — carry uncommitted work onto a new branch.
if [ "$branch" = "main" ] || [ "$branch" = "master" ]; then
  newb="auto/work-$(date '+%Y%m%d-%H%M%S')"
  if git checkout -b "$newb" >/dev/null 2>&1; then
    log "moved uncommitted work off '$branch' onto '$newb'"
    branch="$newb"
  else
    log "on '$branch' but could not create a work branch; skipping (will not commit to $branch)"
    exit 0
  fi
fi

# Guardrail 1b: don't stack NEW work onto an already-MERGED branch — once its PR squash-merges
# (and GitHub deletes the remote), commits here can never land cleanly (gap G4). Detect this two
# ways, because `gh pr view <branch>` often CANNOT resolve a branch whose remote was pruned:
#   (a) gh still reports the PR as MERGED, OR
#   (b) the branch has commits ahead of origin/main by SHA but ZERO net content diff — the
#       signature of a squash-merge whose content already landed on main. This signal is
#       network-independent and catches the pruned-remote case (a) misses.
# Both are true-merged signals (content is provably/authoritatively on main), so rotating the
# new work onto a fresh branch cut from latest main is always safe. A fresh branch has 0 commits
# ahead, so it never false-triggers.
if [ "$branch" != "main" ] && [ "$branch" != "master" ]; then
  git fetch origin main >/dev/null 2>&1 || true
  merged=""
  if command -v gh >/dev/null 2>&1 \
     && gh pr view "$branch" --json state --jq '.state' 2>/dev/null | grep -q MERGED; then
    merged="gh-reports-MERGED"
  elif git rev-parse --verify -q origin/main >/dev/null 2>&1; then
    ahead="$(git rev-list --count origin/main..HEAD 2>/dev/null || echo 0)"
    if [ "${ahead:-0}" -gt 0 ] && git diff --quiet origin/main..HEAD 2>/dev/null; then
      merged="content-already-on-main (squash-merged)"
    fi
  fi
  if [ -n "$merged" ]; then
    newb="auto/work-$(date '+%Y%m%d-%H%M%S')"
    if git checkout -b "$newb" origin/main >/dev/null 2>&1 || git checkout -b "$newb" >/dev/null 2>&1; then
      log "branch '$branch' already merged ($merged); moved new work onto fresh '$newb' off main"
      branch="$newb"
    fi
  fi
fi

# Guardrail 2: secret-scan must confirm clean before anything is staged.
if command -v python >/dev/null 2>&1; then
  scan="$(PYTHONPATH=. python scripts/dedup_check.py --secret-scan 2>&1)"
  if ! printf '%s' "$scan" | grep -qi "No secrets found"; then
    log "ABORT: secret-scan not confirmed clean — left changes uncommitted. Output: ${scan:0:200}"
    exit 0
  fi
fi

git add -A 2>/dev/null
staged="$(git diff --cached --name-only 2>/dev/null | wc -l | tr -d ' ')"
[ "$staged" = "0" ] && exit 0

msg="auto: checkpoint $(date '+%Y-%m-%d %H:%M') ($staged files on $branch)"
if git commit -q \
    -m "$msg" \
    -m "Autonomous checkpoint by the auto-git hook (commit gated by secret-scan)." \
    -m "Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>" \
    -m "Claude-Session: https://claude.ai/code/session_01Usg88wTauUmpxmttv3JVwz" 2>/dev/null; then
  log "committed $staged files: $msg"
else
  log "commit failed; changes remain staged"
  exit 0
fi

# Guardrail 3: push current branch (never --force, never main — handled above).
if [ "${AUTO_GIT_PUSH:-1}" = "1" ] && git remote get-url origin >/dev/null 2>&1; then
  if git push -u origin "HEAD:$branch" >/dev/null 2>&1; then
    log "pushed '$branch' to origin"
  else
    log "push failed (no creds/network?) — commit is safe locally on '$branch'"
  fi
fi

# Ensure a PR exists once the branch is ahead of main, so a long session (or one reset with
# `/clear`) never leaves work un-PR'd waiting on SessionEnd. CREATE only — NO `--auto` here:
# merge-arming stays owned by auto-pr.sh at SessionEnd, so work never merges mid-session.
if command -v gh >/dev/null 2>&1; then
  ahead="$(git rev-list --count origin/main..HEAD 2>/dev/null || echo 0)"
  if [ "${ahead:-0}" -gt 0 ] && ! gh pr view "$branch" --json number >/dev/null 2>&1; then
    gh pr create --base main --head "$branch" --fill >/dev/null 2>&1 \
      && log "opened PR for '$branch' (merge NOT armed — auto-pr.sh arms it at SessionEnd)"
  fi
fi

exit 0
