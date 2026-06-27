#!/usr/bin/env bash
# Session concurrency guard — SessionStart, ADVISORY only.
#
# Git keeps ONE checked-out branch per working tree, so two concurrent Claude sessions on the same
# folder would fight over the branch + commits (the #1 edge case from the branch-choice design). This
# guard WARNS when another session appears active on this working tree and recommends a git worktree
# for true parallel isolation. Heuristic: a lock file holding a DIFFERENT session_id, refreshed less
# than CONCURRENCY_STALE_MIN minutes ago (a crashed session's lock simply goes stale and is reclaimed).
#
# It NEVER blocks, checks out, merges, or deletes anything — it only prints advice and claims the lock.
# FAIL-SAFE: always exits 0. OFF-SWITCH: CONCURRENCY_GUARD_DISABLE=1. TUNABLE: CONCURRENCY_STALE_MIN.
set -uo pipefail

[ "${CONCURRENCY_GUARD_DISABLE:-0}" = "1" ] && exit 0

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0

input="$(cat 2>/dev/null || true)"
sid="$(printf '%s' "$input" | jq -r '.session_id // empty' 2>/dev/null || true)"
[ -z "$sid" ] && sid="unknown"
# SessionStart `source`: startup | resume | clear. Resuming or /clear is the SAME operator
# continuing in the SAME terminal — NOT a second concurrent session. Only a fresh `startup`
# (e.g. a new terminal) can be a genuine collision, so only `startup` is allowed to warn.
src="$(printf '%s' "$input" | jq -r '.source // empty' 2>/dev/null || true)"

LOCK="$ROOT/.claude/.session-active.lock"   # matches the gitignored `.claude/*.lock` pattern
STALE_MIN="${CONCURRENCY_STALE_MIN:-30}"
now="$(date +%s)"

if [ -f "$LOCK" ] && [ "$src" != "resume" ] && [ "$src" != "clear" ]; then
  prev_sid="$(awk 'NR==1{print $1}' "$LOCK" 2>/dev/null)"
  prev_ts="$(awk 'NR==1{print $2}' "$LOCK" 2>/dev/null)"
  case "$prev_ts" in ''|*[!0-9]*) prev_ts=0;; esac
  age_min=$(( (now - prev_ts) / 60 ))
  if [ -n "$prev_sid" ] && [ "$prev_sid" != "$sid" ] && [ "$age_min" -lt "$STALE_MIN" ]; then
    echo "CONCURRENCY: another Claude session ($prev_sid, active ~${age_min}m ago) shares this working tree."
    echo "  Two sessions share ONE checked-out branch and WILL collide on commits. For parallel work, isolate"
    echo "  in a git worktree:  /git-branch-lifecycle work <name>   (or: git worktree add ../<dir> -b <branch>)."
  fi
fi

printf '%s %s\n' "$sid" "$now" > "$LOCK" 2>/dev/null || true   # claim/refresh the lock for THIS session
exit 0
