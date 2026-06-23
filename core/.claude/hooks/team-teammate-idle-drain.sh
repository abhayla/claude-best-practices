#!/usr/bin/env bash
# TeammateIdle hook (agent teams) — extends the hub's decide-don't-ask / don't-
# narrate-and-stop doctrine to the teammate boundary: a teammate should DRAIN the
# shared task list (claim the next unblocked task) before going idle, rather than
# stopping with reversible work still queued.
#
# Contract (per docs/claude-references/agent-teams.md): TeammateIdle runs when a teammate
# is about to go idle; **exit code 2 sends the stderr text as feedback and keeps it
# working**. Any other exit code lets it go idle.
#
# DESIGN (loop-safe, fail-open):
#   - CRITICAL: never exit 2 unless we can POSITIVELY detect pending unblocked work.
#     An unconditional exit 2 would re-engage a teammate with an empty queue forever.
#   - Hard-keep-working (exit 2) ONLY when TEAM_GOVERNANCE_STRICT=1 AND the payload shows
#     a pending/unclaimed task count > 0. Otherwise allow idle (exit 0).
#   - SHIPS UNWIRED. TeammateIdle payload schema unconfirmed; the pending-count field name
#     is a defensive guess. Confirm on a live run before enabling strict mode, else the
#     re-engage signal is a no-op (fail-open) — which is the safe default.
#
# NOTE: stderr is intentionally NOT redirected — the exit-2 feedback to a teammate is
# delivered via stderr. Helper-command noise is suppressed inline (2>/dev/null) instead.

PAYLOAD="$(cat 2>/dev/null || true)"

pending=""
if command -v jq >/dev/null 2>&1 && [ -n "$PAYLOAD" ]; then
  pending="$(printf '%s' "$PAYLOAD" | jq -r '
    (.pending_tasks // .tasks_pending // .unblocked_pending // .queue.pending // empty)
  ' 2>/dev/null)"
fi

# Only act on a clean positive integer > 0. Anything else → allow idle (loop-safe).
case "$pending" in
  ''|*[!0-9]*) exit 0 ;;
esac

if [ "${TEAM_GOVERNANCE_STRICT:-0}" = "1" ] && [ "$pending" -gt 0 ]; then
  printf 'Do not go idle: %s unblocked task(s) remain in the shared list. ' "$pending" >&2
  printf 'Claim the next one and keep working until the queue is drained ' >&2
  printf '(decide-don'\''t-ask / drain-the-queue). See plans/agent-teams-incorporation.md.' >&2
  exit 2
fi

[ "$pending" -gt 0 ] && printf '[team-governance] note: %s pending task(s) remain at idle.\n' "$pending"
exit 0
