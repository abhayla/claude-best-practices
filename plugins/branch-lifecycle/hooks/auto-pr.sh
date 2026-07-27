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

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
cd "$ROOT" || exit 0

mkdir -p "$ROOT/.claude" 2>/dev/null || true   # state dir may not exist in a downstream repo
LOG="$ROOT/.claude/.auto-git.log"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] auto-pr: $*" >> "$LOG" 2>/dev/null; }

# Fast-exit on main/master/detached HEAD: there is nothing to LAND here — session-git-landing.sh's
# `land` skips those outright — so the only work left would be janitorial branch pruning, which
# auto-pr-reconcile.sh already does at the reliably-firing SessionStart. Doing it HERE instead races
# the SessionEnd shutdown window: `git fetch --prune` plus one `gh pr view` per stale branch is
# multi-second network I/O, and the platform kills the hook when the session process exits —
# surfacing "Hook cancelled" to the user. Nothing is lost; reconcile sweeps it next session.
# (An earlier version only fast-exited when main was the ONLY local branch, so a single leftover
# branch was enough to re-enter the network path and trigger the cancel. Pure local check.)
#
# This check runs FIRST — before the coexistence grep and before sourcing _settings.sh — because
# on Windows the ~15 subprocesses they spawn (jq per settings key, basename, grep) cost ~2s of
# wall clock (measured 2026-07-27, gorefer), enough for the SessionEnd shutdown window to cancel
# the hook even though the script was about to exit 0 on this very fast-exit path.
_cur="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
case "$_cur" in
  main|master|HEAD|"")
    log "on '$_cur' — nothing to land; pruning deferred to auto-pr-reconcile.sh; fast-exit"
    exit 0
    ;;
esac

# -- Coexistence stand-down (hub lesson, calculatekaro migration 2026-07-12; mirrors the
# enhance-process-guard precedent, PR #309): when the HOST project wires its OWN copy of this
# hook in .claude/settings.json, the project's copy wins and this plugin copy stands down --
# otherwise both fire (double gates/PRs/reminders). Downstream projects with no local copy
# are unaffected. (${0##*/} instead of basename: saves a fork on the latency-critical path.)
_std_self="${0##*/}"
if [ -f "$ROOT/.claude/hooks/$_std_self" ] && grep -q "$_std_self" "$ROOT/.claude/settings.json" 2>/dev/null; then
  exit 0
fi

SELFDIR="${CLAUDE_PLUGIN_ROOT:+$CLAUDE_PLUGIN_ROOT/hooks}"
SELFDIR="${SELFDIR:-$(cd "$(dirname "$0")" && pwd)}"

PROJECT_ROOT="$ROOT"
# shellcheck source=/dev/null
[ -f "$SELFDIR/_settings.sh" ] && . "$SELFDIR/_settings.sh"

[ "${AUTO_PR_DISABLE:-0}" = "1" ] && exit 0

command -v gh >/dev/null 2>&1 || { log "gh not installed; skipping"; exit 0; }

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
