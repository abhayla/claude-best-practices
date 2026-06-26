#!/usr/bin/env bash
# Autonomous PR reconcile — the SessionStart catch-up that makes the branch lifecycle self-healing.
#
# Wired into SessionStart. Closes the gap that left CLEAN PRs open with no action:
#   auto-pr.sh runs ONLY at SessionEnd and only for the CURRENT branch. When SessionEnd is
#   missed (a killed/crashed/abruptly-closed session, sleep/shutdown, or an environment that
#   doesn't emit it), that branch's PR is never armed and never pruned — it sits CLEAN-but-open
#   forever, because nothing revisits it. SessionStart fires reliably on EVERY session, so this
#   hook sweeps ALL open PRs at the start of each session and recovers the orphans.
#
# What it does (idempotent, fail-safe, CI-gated):
#   1. fetch --prune; hard-delete LOCAL branches whose PR gh confirms is MERGED (never loses work).
#   2. Arm native auto-merge (squash) on every OPEN, non-draft PR that doesn't already have it —
#      EXCEPT the current HEAD branch (active work must not be merged out from under the session).
#      GitHub still gates the actual merge on the required `validate` check, so a red/pending PR
#      simply stays open. A genuinely CI-red or conflicted PR is left for a human.
#
# FAIL-SAFE: always exits 0 (a gh/network hiccup must never block session start).
# OFF-SWITCHES (shared with auto-pr.sh):
#   AUTO_PR_DISABLE=1 -> do nothing at all.
#   AUTO_MERGE=0      -> prune only; do NOT arm auto-merge (you click merge yourself).

set -uo pipefail

[ "${AUTO_PR_DISABLE:-0}" = "1" ] && exit 0

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
cd "$ROOT" || exit 0

LOG="$ROOT/.claude/.auto-git.log"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] auto-pr-reconcile: $*" >> "$LOG" 2>/dev/null; }

command -v gh >/dev/null 2>&1 || { log "gh not installed; skipping"; exit 0; }

current="$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"

# 1. Prune merged branches (same safe rule as auto-pr.sh: delete a local branch only when gh
#    confirms its PR is MERGED — squash-merge hides it from `git branch -d`, hence the gh check).
git fetch --prune >/dev/null 2>&1 || true
git for-each-ref --format '%(refname:short) %(upstream:track)' refs/heads/ 2>/dev/null \
  | awk '$2=="[gone]"{print $1}' \
  | while read -r b; do
      [ "$b" = "$current" ] && continue
      if gh pr view "$b" --json state --jq '.state' 2>/dev/null | grep -q MERGED; then
        git branch -D "$b" >/dev/null 2>&1 && log "pruned merged branch '$b'"
      fi
    done

[ "${AUTO_MERGE:-1}" = "0" ] && { log "AUTO_MERGE=0 — prune only, no arming"; exit 0; }

# 2. Reconcile leftover PRs via the shared SSOT (.claude/hooks/session-git-landing.sh): arm native
#    auto-merge on every open, non-draft PR EXCEPT the current branch (CI-gated). Same single source
#    of truth that /start-session STEP 0 and /end-session use — the landing logic lives in ONE place.
log "$(bash "$ROOT/.claude/hooks/session-git-landing.sh" reconcile 2>&1)"

exit 0
