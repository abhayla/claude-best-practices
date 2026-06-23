#!/usr/bin/env bash
# TaskCompleted hook (agent teams) — completion AUDIT logger.
#
# ORIGINAL INTENT was to extend the "reproduce the gate before accepting a done-claim"
# doctrine (supervisor-verification.md) to the teammate boundary by blocking completions
# that carry no verification evidence. The LIVE-CAPTURED payload (2026-06-23, see
# plans/agent-teams-incorporation.md §11) proved that infeasible:
#
#   TaskCompleted payload = { session_id, transcript_path, cwd, hook_event_name,
#     task_id, task_subject, task_description, teammate_name, team_name }
#
# There is NO work-product / result / summary field — the teammate's actual output is
# NOT in the payload. So a payload-only evidence gate is impossible; true verification
# must stay with the lead reproducing the gate (out of band). Rather than pretend to
# enforce something it cannot see, this hook now serves the honest, still-useful role of
# an AUDIT TRAIL: it records who completed which task, which is exactly what a later
# lead/human reproduction needs.
#
# Contract: TaskCompleted exit 2 would block completion; this hook NEVER blocks (exit 0).
# stderr is left un-redirected for consistency with the sibling hooks.

PAYLOAD="$(cat 2>/dev/null || true)"

task_id="" ; subject="" ; teammate="" ; team=""
if command -v jq >/dev/null 2>&1 && [ -n "$PAYLOAD" ]; then
  task_id="$(printf  '%s' "$PAYLOAD" | jq -r '(.task_id // "")'       2>/dev/null)"
  subject="$(printf  '%s' "$PAYLOAD" | jq -r '(.task_subject // "")'  2>/dev/null)"
  teammate="$(printf '%s' "$PAYLOAD" | jq -r '(.teammate_name // "")' 2>/dev/null)"
  team="$(printf     '%s' "$PAYLOAD" | jq -r '(.team_name // "")'     2>/dev/null)"
fi

# Append to a project-local audit trail when a .claude dir is present; else no-op.
base="${CLAUDE_PROJECT_DIR:-$PWD}"
if [ -d "$base/.claude" ]; then
  ts="$(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || echo '?')"
  printf '%s\tTaskCompleted\tteam=%s\ttask=%s\tby=%s\tsubject=%s\n' \
    "$ts" "${team:-?}" "${task_id:-?}" "${teammate:-?}" "${subject:-?}" \
    >> "$base/.claude/.team-activity.log" 2>/dev/null || true
fi
exit 0
