#!/usr/bin/env bash
# Autonomous PR + auto-merge handler — so closing a session lands the work without touching git.
#
# Wired into SessionEnd (fires when the session closes). Companion to auto-git.sh:
#   auto-git.sh (SessionStart+Stop) — commits + pushes each turn's work to a task branch.
#   auto-pr.sh  (SessionEnd)        — opens a PR for that branch and ARMS native auto-merge,
#                                     so GitHub squash-merges it the moment CI (validate+test)
#                                     goes green, then deletes the remote branch.
#
# Why SessionEnd, not Stop: arming auto-merge after every turn would merge work mid-session.
# Arming on close matches "close the session and forget about the branch".
#
# FAIL-SAFE: always exits 0 (a gh/network hiccup must never block session close).
# GUARDRAILS:
#   1. Never opens a PR for main/master or a detached HEAD.
#   2. Only arms auto-merge — GitHub still gates the actual merge on the required CI checks.
#      A red or pending CI leaves the PR open and unmerged (no lost work, nothing forced).
#   3. Idempotent — re-running reuses the existing PR; never opens duplicates.
# OFF-SWITCHES:
#   AUTO_PR_DISABLE=1 -> do nothing at all.
#   AUTO_MERGE=0      -> open/refresh the PR but do NOT arm auto-merge (you click merge yourself).

set -uo pipefail

[ "${AUTO_PR_DISABLE:-0}" = "1" ] && exit 0

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
cd "$ROOT" || exit 0

LOG="$ROOT/.claude/.auto-git.log"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] auto-pr: $*" >> "$LOG" 2>/dev/null; }

command -v gh >/dev/null 2>&1 || { log "gh not installed; skipping"; exit 0; }

# Fast-exit: if we're on main/master AND it's the ONLY local branch, there is nothing to land or
# prune — skip the slow network I/O (git fetch + gh calls). This is the common "ended the session on
# main, everything already merged" case; doing network work there only races the SessionEnd shutdown
# window and surfaces a benign "Hook cancelled". Anything genuinely pending is still swept by
# auto-pr-reconcile.sh at the reliably-firing SessionStart. (Pure local check — no network.)
_cur="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
if [ "$_cur" = "main" ] || [ "$_cur" = "master" ]; then
  _other="$(git for-each-ref --format='%(refname:short)' refs/heads/ 2>/dev/null \
            | grep -vxE 'main|master' | head -1)"
  [ -z "$_other" ] && { log "on '$_cur', no other local branches — nothing to land/prune; fast-exit"; exit 0; }
fi

# Prune merged branches so they never accumulate. `fetch --prune` drops stale remote refs (safe);
# a LOCAL branch is hard-deleted ONLY when gh confirms its PR is MERGED — its content is already on
# main, so this can never lose work (squash-merge hides it from `git branch -d`, hence the gh check).
git fetch --prune >/dev/null 2>&1 || true
cur_for_prune="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
git for-each-ref --format '%(refname:short) %(upstream:track)' refs/heads/ 2>/dev/null \
  | awk '$2=="[gone]"{print $1}' \
  | while read -r b; do
      [ "$b" = "$cur_for_prune" ] && continue
      if gh pr view "$b" --json state --jq '.state' 2>/dev/null | grep -q MERGED; then
        git branch -D "$b" >/dev/null 2>&1 && log "pruned merged branch '$b'"
      fi
    done

# Land the current branch via the shared SSOT (.claude/hooks/session-git-landing.sh): push +
# open PR + arm native auto-merge, all CI-gated. SessionEnd must NOT block, so this arms and
# RETURNS (no --wait) — GitHub merges when the required CI passes. The lib handles the main/master/
# detached-HEAD skip and the AUTO_MERGE=0 off-switch. Keeps the landing logic in ONE place
# (shared with /end-session STEP 5 + /start-session reconcile).
log "$(bash "$ROOT/.claude/hooks/session-git-landing.sh" land 2>&1)"

exit 0
