#!/usr/bin/env bash
# Stale-branch reaper — REPORT-ONLY — wired into SessionStart.
#
# Two jobs, both safe and non-destructive:
#   1. Reset the per-session branch-choice marker (.claude/.branch-choice-active) + print the
#      BRANCH-CHOICE nudge, so the branch-choice skill asks ONCE at the first file-edit of every
#      new session. (Done UNCONDITIONALLY — even when staleness reporting is switched off — so
#      the once-per-session menu never silently stops re-asking.)
#   2. List local branches whose LAST COMMIT is older than STALE_BRANCH_HOURS (default 24h),
#      with metadata (age, ahead/behind main, CI/PR state, last subject) so the branch-choice
#      skill can present them to the owner for BATCHED, APPROVED landing.
#
# This hook NEVER merges, pushes, deletes, checks out, or fetches — it has zero git side-effects.
# The actual landing is owner-approved and delegated to session-git-landing.sh `merge-one <branch>`
# (CI-gated), invoked by the branch-choice skill — never by this hook.
#
# FAIL-SAFE: always exits 0 (never blocks session start).
# OFF-SWITCH: STALE_REAPER_DISABLE=1  -> skip the staleness LISTING (marker reset + nudge still run).
# TUNABLE:   STALE_BRANCH_HOURS=<n>   -> staleness threshold in hours (default 24).
set -uo pipefail

SELFDIR="${CLAUDE_PLUGIN_ROOT:+$CLAUDE_PLUGIN_ROOT/hooks}"
SELFDIR="${SELFDIR:-$(cd "$(dirname "$0")" && pwd)}"

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
cd "$ROOT" || exit 0

# Map branch-lifecycle-settings.json -> env off-switches (a pre-set env var still wins).
PROJECT_ROOT="$ROOT"
# shellcheck source=/dev/null
[ -f "$SELFDIR/_settings.sh" ] && . "$SELFDIR/_settings.sh"

mkdir -p "$ROOT/.claude" 2>/dev/null || true   # state dir may not exist in a downstream repo

# (1) Always: nudge the once-per-session branch menu. Markers are now per-SESSION
# (.claude/.branch-choice-active.<session_id>), so a new session re-asks automatically (its marker
# does not exist yet) — no shared marker to wipe. We only GC stale per-session markers so they do
# not accumulate, plus clear any legacy bare marker left from before session-scoping.
rm -f "$ROOT/.claude/.branch-choice-active" 2>/dev/null || true   # legacy bare marker (pre session-scoping)
find "$ROOT/.claude" -maxdepth 1 -type f -name '.branch-choice-active.*' -mmin "+$(( ${STALE_BRANCH_HOURS:-24} * 60 ))" -delete 2>/dev/null || true
echo "BRANCH-CHOICE: before your FIRST file edit this session, run the /branch-choice skill"
echo "  to pick the branch — unless this session's"
echo "  .claude/.branch-choice-active.<session_id> marker exists."

# (2) The staleness LISTING is the part the off-switch silences.
[ "${STALE_REAPER_DISABLE:-0}" = "1" ] && exit 0

HOURS="${STALE_BRANCH_HOURS:-24}"
now="$(date +%s)"
cutoff=$(( HOURS * 3600 ))

# Use the EXISTING origin/main ref — do NOT fetch (a SessionStart report must not add a network
# stall or mutate remote-tracking refs). ahead/behind are best-effort metadata, not safety gates.
has_main=0
git rev-parse --verify -q origin/main >/dev/null 2>&1 && has_main=1

reported=0
while read -r br; do
  [ -z "$br" ] && continue
  case "$br" in main|master) continue;; esac

  last="$(git log -1 --format=%ct "$br" 2>/dev/null || echo "$now")"
  age=$(( now - last ))
  [ "$age" -lt "$cutoff" ] && continue
  age_h=$(( age / 3600 ))

  subject="$(git log -1 --format=%s "$br" 2>/dev/null)"
  ahead='?'; behind='?'
  if [ "$has_main" = 1 ]; then
    ahead="$(git rev-list --count origin/main.."$br" 2>/dev/null || echo '?')"
    behind="$(git rev-list --count "$br"..origin/main 2>/dev/null || echo '?')"
  fi
  ci='unknown'
  if command -v gh >/dev/null 2>&1; then
    ci="$(gh pr view "$br" --json state,statusCheckRollup \
            --jq '(.state) + " " + ((.statusCheckRollup // []) | map(.conclusion // "PENDING") | join(","))' \
            2>/dev/null || echo 'no-PR')"
    [ -z "$ci" ] && ci='no-PR'
  fi

  if [ "$reported" = 0 ]; then
    echo "=== STALE BRANCHES (> ${HOURS}h since last commit) — owner approval needed to land ==="
    echo "    Rule: offer to merge ONLY green+clean branches (session-git-landing.sh merge-one <br>); FLAG red/unfinished."
  fi
  echo "STALE_BRANCH | ${br} | age=${age_h}h | ahead=${ahead} behind=${behind} | ci=${ci} | last: ${subject}"
  reported=$(( reported + 1 ))
done < <(git for-each-ref --format='%(refname:short)' refs/heads/ 2>/dev/null)

[ "$reported" = 0 ] && echo "stale-branch-reaper: no branches older than ${HOURS}h"
exit 0
