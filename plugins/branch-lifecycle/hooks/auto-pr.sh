#!/usr/bin/env bash
# Autonomous PR + auto-merge handler — so closing a session lands the work without touching git.
# (branch-lifecycle PLUGIN version — self-contained.)
#
# Wired into SessionEnd (fires when the session closes). Companion to auto-git.sh:
#   auto-git.sh (SessionStart+Stop) — commits + pushes each turn's work to a task branch.
#   auto-pr.sh  (SessionEnd)        — opens a PR for that branch and ARMS native auto-merge,
#                                     so GitHub squash-merges it the moment the project's required
#                                     CI checks go green, then deletes the remote branch.
#
# PREREQUISITES (configure once, per repo): GitHub branch protection on main with required
# status checks, repo-level auto-merge enabled, and delete-branch-on-merge enabled. Without a
# required check, `--auto` merges immediately (no green-gate) — so set at least one required check.
#
# Why SessionEnd, not Stop: arming auto-merge after every turn would merge work mid-session.
#
# FAIL-SAFE: always exits 0 (a gh/network hiccup must never block session close).
# GUARDRAILS:
#   1. Never opens a PR for main/master or a detached HEAD.
#   2. Only arms auto-merge — GitHub still gates the actual merge on the required CI checks.
#   3. Idempotent — re-running reuses the existing PR; never opens duplicates.
# OFF-SWITCHES (env, or branch-lifecycle-settings.json -> _settings.sh):
#   AUTO_PR_DISABLE=1 -> do nothing at all.
#   AUTO_MERGE=0      -> open/refresh the PR but do NOT arm auto-merge (you click merge yourself).

set -uo pipefail

SELFDIR="${CLAUDE_PLUGIN_ROOT:+$CLAUDE_PLUGIN_ROOT/hooks}"
SELFDIR="${SELFDIR:-$(cd "$(dirname "$0")" && pwd)}"

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
cd "$ROOT" || exit 0

PROJECT_ROOT="$ROOT"
# shellcheck source=/dev/null
[ -f "$SELFDIR/_settings.sh" ] && . "$SELFDIR/_settings.sh"

[ "${AUTO_PR_DISABLE:-0}" = "1" ] && exit 0

mkdir -p "$ROOT/.claude" 2>/dev/null || true   # state dir may not exist in a downstream repo
LOG="$ROOT/.claude/.auto-git.log"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] auto-pr: $*" >> "$LOG" 2>/dev/null; }

command -v gh >/dev/null 2>&1 || { log "gh not installed; skipping"; exit 0; }

# Fast-exit: if we're on main/master AND it's the ONLY local branch, there is nothing to land or
# prune — skip the slow network I/O. Anything genuinely pending is still swept by
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

# Land the current branch via the bundled SSOT (session-git-landing.sh in this same hooks dir):
# push + open PR + arm native auto-merge, all CI-gated. SessionEnd must NOT block, so this arms and
# RETURNS (no --wait). The lib handles the main/master/detached-HEAD skip and the AUTO_MERGE=0 switch.
log "$(bash "$SELFDIR/session-git-landing.sh" land 2>&1)"

exit 0
