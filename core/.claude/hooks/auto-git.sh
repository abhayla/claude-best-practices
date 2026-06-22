#!/usr/bin/env bash
# Autonomous git handler — so you never touch git.
#
# Wired into SessionStart + Stop (see settings.json). If the working tree has changes:
# secret-scan -> stage -> commit with a generated message -> push the current branch ->
# open a PR if one is missing and the branch is ahead of main (CREATE only).
# Companion: auto-pr.sh (SessionEnd) arms CI-gated auto-merge on that PR. Opening the PR
# per-turn (not arming) keeps long / `/clear`-reset sessions from leaving work un-PR'd.
#
# FAIL-SAFE: always exits 0 (a git hiccup must never block the session).
# GUARDRAILS:
#   1. Never auto-commits onto main/master — moves the work to a fresh branch first.
#   2. Secret-scans before staging; aborts the commit if it is not confirmed clean.
#   3. Pushes the current branch only, never --force.
# OFF-SWITCHES:
#   AUTO_GIT_DISABLE=1  -> do nothing at all.
#   AUTO_GIT_PUSH=0     -> commit locally but do not push.
# SECRET SCAN (pluggable, in priority order):
#   SECRET_SCAN_CMD="<cmd>"  -> run it; a non-zero exit aborts the commit (set this to your
#                               project's scanner, e.g. "gitleaks protect --staged --no-banner").
#   else `gitleaks` if installed; else commit proceeds WITH A WARNING (no scanner found).

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
# (and the remote branch is deleted), commits here can never land cleanly. Detect this two ways,
# because `gh pr view <branch>` often CANNOT resolve a branch whose remote was pruned:
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

# Guardrail 2: secret-scan must confirm clean before anything is staged (pluggable — see header).
if [ -n "${SECRET_SCAN_CMD:-}" ]; then
  if ! eval "$SECRET_SCAN_CMD" >/dev/null 2>&1; then
    log "ABORT: SECRET_SCAN_CMD reported not clean — left changes uncommitted."
    exit 0
  fi
elif command -v gitleaks >/dev/null 2>&1; then
  if ! gitleaks detect --no-banner --no-git >/dev/null 2>&1; then
    log "ABORT: gitleaks flagged potential secrets — left changes uncommitted."
    exit 0
  fi
else
  log "WARN: no secret scanner (set SECRET_SCAN_CMD or install gitleaks) — committing WITHOUT a secret scan."
fi

git add -A 2>/dev/null
staged="$(git diff --cached --name-only 2>/dev/null | wc -l | tr -d ' ')"
[ "$staged" = "0" ] && exit 0

msg="auto: checkpoint $(date '+%Y-%m-%d %H:%M') ($staged files on $branch)"
if git commit -q \
    -m "$msg" \
    -m "Autonomous checkpoint by the auto-git hook (commit gated by secret-scan)." 2>/dev/null; then
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
