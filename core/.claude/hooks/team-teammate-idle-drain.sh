#!/usr/bin/env bash
# TeammateIdle hook (agent teams) — idle AUDIT logger + loop-safe drain stub.
#
# ORIGINAL INTENT was to extend decide-don't-ask / drain-the-queue to teammates by
# keeping a teammate working while unblocked tasks remain. The LIVE-CAPTURED payload
# (2026-06-23, see plans/agent-teams-incorporation.md §11) showed the idle payload does
# NOT carry a pending-task count:
#
#   TeammateIdle payload = { session_id, transcript_path, cwd, permission_mode,
#     hook_event_name, teammate_name, team_name }
#
# So the queue depth cannot be read from the payload — re-engaging would be guessing, and
# an unconditional exit 2 would loop a teammate forever on an empty queue. This hook
# therefore stays LOOP-SAFE (never re-engages on unknown queue state) and records the idle
# event to the audit trail.
#
# FUTURE ENHANCEMENT (documented, not yet implemented): the payload DOES carry team_name,
# and the shared task list lives on disk at ~/.claude/tasks/{team_name}/. A future version
# can read that directory to count pending/unblocked tasks and, under
# TEAM_GOVERNANCE_STRICT=1, exit 2 to keep the teammate working. Deferred until the
# on-disk task-list format is pinned from a live run (YAGNI — no guessing the format).
#
# Contract: exit 2 keeps a teammate working; this hook stays at exit 0 (loop-safe).
# stderr left un-redirected for consistency with the sibling hooks.

PAYLOAD="$(cat 2>/dev/null || true)"

teammate="" ; team=""
if command -v jq >/dev/null 2>&1 && [ -n "$PAYLOAD" ]; then
  teammate="$(printf '%s' "$PAYLOAD" | jq -r '(.teammate_name // "")' 2>/dev/null)"
  team="$(printf     '%s' "$PAYLOAD" | jq -r '(.team_name // "")'     2>/dev/null)"
fi

base="${CLAUDE_PROJECT_DIR:-$PWD}"
if [ -d "$base/.claude" ]; then
  ts="$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || echo '?')"
  printf '%s\tTeammateIdle\tteam=%s\tteammate=%s\n' \
    "$ts" "${team:-?}" "${teammate:-?}" >> "$base/.claude/.team-activity.log" 2>/dev/null || true
fi
exit 0
