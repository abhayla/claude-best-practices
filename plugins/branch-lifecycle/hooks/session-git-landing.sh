#!/usr/bin/env bash
# Shared SSOT for session git-landing — the single place the merge/reconcile logic lives.
# Called by /end-session (`land --wait`), /start-session (`reconcile`), and the auto-pr /
# auto-pr-reconcile hooks (`land` / `reconcile`). Keeping it here (instead of duplicating the
# shell in each skill + hook) means a landing fix is a ONE-file edit, correct everywhere.
#
# Usage:
#   session-git-landing.sh land [--wait]   # land the CURRENT branch
#   session-git-landing.sh reconcile       # sweep leftover open PRs (except the current branch)
#
# Design notes:
# - Arms GitHub's NATIVE auto-merge, which merges exactly when the REQUIRED status checks pass
#   (same gate as branch protection). Do NOT watch ALL checks (e.g. `gh pr checks --watch
#   --fail-fast`): a noisy NON-required workflow would false-fail while the required check passes.
# - `land --wait` then polls until the PR reaches MERGED, so the branch is CLOSED before the caller
#   returns (the root cause of "branch left open" was returning before the async merge happened).
#   The hooks call `land` WITHOUT --wait (a SessionEnd hook must not block for minutes).
# - Honors AUTO_MERGE=0 (off-switch) and skips on main/master/detached HEAD / no gh / no remote.
set -u

_guard() { command -v gh >/dev/null 2>&1; }   # gh present (AUTO_MERGE gates only the *arm*, below)

_sync_local_after_merge() {
  # ROOT-CAUSE fix for "the branch looks unmerged locally after /end-session": land --wait merged
  # the PR REMOTELY but never reconciled the LOCAL clone, leaving the caller ON the now-dead branch
  # with a stale local `main` and an un-pruned local branch. (Squash-merge compounds it: the local
  # commits are not ancestors of origin/main, so `git branch -d`/`merge-base` both say "unmerged".)
  # Called ONLY after the caller has CONFIRMED the PR state is MERGED, so pruning is safe.
  # Skips on a dirty tree so it can never clobber uncommitted work.
  local merged_branch="$1"
  case "$merged_branch" in main|master|HEAD|"") return 0;; esac
  if [ -n "$(git status --porcelain 2>/dev/null)" ]; then
    echo "  (local NOT reconciled: working tree dirty — switch to main + prune '$merged_branch' manually)"; return 0
  fi
  git checkout main >/dev/null 2>&1 || { echo "  (local NOT reconciled: could not checkout main)"; return 0; }
  git fetch origin main >/dev/null 2>&1
  git merge --ff-only origin/main >/dev/null 2>&1
  # -D (not -d): a squash merge means the local branch is not an ancestor of main, so -d would
  # refuse. Safe because the caller already confirmed the PR is MERGED (content is on main).
  git branch -D "$merged_branch" >/dev/null 2>&1
  echo "  (local reconciled: on main, fast-forwarded to origin/main, pruned '$merged_branch')"
}

land() {
  local wait_mode="${1:-}"
  _guard || { echo "land: skipped (no gh)"; return 0; }
  local branch; branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
  case "$branch" in main|master|HEAD|"") echo "land: skipped (on '$branch')"; return 0;; esac
  git push -u origin "HEAD:$branch" >/dev/null 2>&1 || { echo "land: push failed for '$branch' (creds/network?)"; return 0; }
  gh pr view "$branch" >/dev/null 2>&1 || gh pr create --base main --head "$branch" --fill >/dev/null 2>&1
  # AUTO_MERGE=0 -> open/refresh the PR but do NOT arm (you click merge yourself).
  if [ "${AUTO_MERGE:-1}" = "0" ]; then echo "AUTO_MERGE=0 — PR opened for '$branch', not armed"; return 0; fi
  # Arm native auto-merge (gated on the REQUIRED checks only).
  gh pr merge "$branch" --auto --squash --delete-branch >/dev/null 2>&1
  if [ "$wait_mode" != "--wait" ]; then
    echo "armed auto-merge on '$branch' (lands when required CI passes)"; return 0
  fi
  # --wait: block until the PR is actually MERGED (or terminally closed), so the branch is closed.
  local st="" i=0
  while [ "$i" -lt 90 ]; do                       # up to ~15 min (90 x 10s)
    st="$(gh pr view "$branch" --json state --jq '.state' 2>/dev/null)"
    if [ "$st" = "MERGED" ] || [ "$st" = "CLOSED" ]; then break; fi
    sleep 10; i=$((i + 1))
  done
  case "$st" in
    MERGED) echo "merged '$branch' -> main and CLOSED the branch (required CI passed)"; _sync_local_after_merge "$branch";;
    CLOSED) echo "NOT closed cleanly: the PR for '$branch' was closed without merging — investigate";;
    *)      echo "NOT CLOSED: '$branch' is still OPEN after waiting — the required check is failing or stuck; investigate and re-run, do NOT declare the session closed";;
  esac
}

merge_one() {
  # Land ONE specific branch — invoked by the branch-choice SKILL (option 4 "merge then new", and
  # the owner-approved landing of a reaper-reported stale branch). The current branch IS a valid
  # target (option 4 merges the branch you're on, then cuts a fresh one). Arms GitHub NATIVE
  # auto-merge, so the merge is still CI-GATED on the required checks (a red/stale branch can never
  # sneak in). Never switches the working tree. NOTE: the reaper hook never calls this — only the skill does.
  local br="${1:-}"
  _guard || { echo "merge-one: skipped (no gh)"; return 0; }
  [ -z "$br" ] && { echo "merge-one: no branch given"; return 0; }
  case "$br" in main|master) echo "merge-one: refusing to merge '$br' into itself"; return 0;; esac
  [ "${AUTO_MERGE:-1}" = "0" ] && { echo "merge-one: skipped (AUTO_MERGE=0)"; return 0; }
  gh pr view "$br" >/dev/null 2>&1 || { echo "merge-one: no PR for '$br' (push/open it first)"; return 0; }
  if gh pr merge "$br" --auto --squash --delete-branch >/dev/null 2>&1; then
    echo "armed auto-merge on '$br' (lands when its REQUIRED CI passes; red/stale never merges)"
  else
    echo "merge-one: could not arm '$br' (already merged/closed, or no perms)"
  fi
}

reconcile() {
  _guard || { echo "reconcile: skipped (no gh)"; return 0; }
  [ "${AUTO_MERGE:-1}" = "0" ] && { echo "reconcile: skipped (AUTO_MERGE=0)"; return 0; }
  local cur; cur="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
  local any=0
  while read -r num br; do
    [ -z "$num" ] && continue
    [ "$br" = "$cur" ] && continue                # never the active branch
    gh pr merge "$num" --auto --squash --delete-branch >/dev/null 2>&1 && { echo "armed #$num ($br — lands when required CI passes)"; any=1; }
  done < <(gh pr list --state open --json number,headRefName,isDraft,autoMergeRequest \
            --jq '.[] | select(.isDraft==false) | select(.autoMergeRequest==null) | "\(.number) \(.headRefName)"' 2>/dev/null)
  [ "$any" = 0 ] && echo "reconcile: no leftover PRs to land"
  return 0
}

# Only dispatch when EXECUTED, not when SOURCED (tests source this file to call the helpers
# directly, e.g. _sync_local_after_merge, without triggering the usage/exit path).
if [ "${BASH_SOURCE[0]:-$0}" = "$0" ]; then
  case "${1:-}" in
    land)      shift; land "$@";;
    reconcile) reconcile;;
    merge-one) shift; merge_one "$@";;
    *) echo "usage: session-git-landing.sh {land [--wait]|reconcile|merge-one <branch>}" >&2; exit 2;;
  esac
fi
