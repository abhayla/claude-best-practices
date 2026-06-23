#!/usr/bin/env bash
# TaskCreated hook (agent teams) — extends the hub's "size tasks appropriately"
# best practice to the teammate boundary: a shared-task-list item must name a
# clear, self-contained DELIVERABLE, not a vague directive.
#
# Contract (per docs/claude-references/agent-teams.md): TaskCreated runs when a task
# is being created; **exit code 2 prevents creation + sends the stderr text back as
# feedback**. Any other exit code allows creation.
#
# DESIGN (matches the hub's telemetry-first governance, see verifier-edge-guard.sh):
#   - FAIL-OPEN by default — exit 0 (allow) on any parse uncertainty. A wrongly-blocked
#     task is worse than a permissive one for an experimental feature.
#   - Hard-block (exit 2) ONLY when TEAM_GOVERNANCE_STRICT=1 AND the task clearly lacks
#     a deliverable. Otherwise emit an advisory note to stdout and allow.
#   - SHIPS UNWIRED. The exact TaskCreated stdin payload schema is not yet confirmed on a
#     live run; field names below are defensive guesses. Confirm on a real team run, then
#     tighten. Precedent: the hub's subagent-verifier-edge.sh (ready-but-unwired).
#
# NOTE: stderr is intentionally NOT redirected — the exit-2 feedback to a teammate is
# delivered via stderr. Noise from helper commands is suppressed inline (2>/dev/null) instead.

PAYLOAD="$(cat 2>/dev/null || true)"

# Pull a task description/title with jq if available; fall back to a grep heuristic.
desc=""
if command -v jq >/dev/null 2>&1 && [ -n "$PAYLOAD" ]; then
  desc="$(printf '%s' "$PAYLOAD" | jq -r '
    (.task.description // .task.title // .description // .title // .task.content // "")
  ' 2>/dev/null)"
fi
[ "$desc" = "null" ] && desc=""

# Heuristic: a real deliverable names an artifact/outcome. Too-short or imperative-only
# strings ("fix it", "look into this") fail. Count words after trimming.
words="$(printf '%s' "$desc" | tr -s '[:space:]' ' ' | wc -w | tr -d ' ')"

if [ "${TEAM_GOVERNANCE_STRICT:-0}" = "1" ] && [ -n "$desc" ] && [ "${words:-0}" -lt 4 ]; then
  printf 'TaskCreated rejected: task "%s" has no clear deliverable. Restate it as a ' "$desc" >&2
  printf 'self-contained unit with a named artifact/outcome (agent-team best practice: ' >&2
  printf 'size tasks appropriately). See plans/agent-teams-incorporation.md.' >&2
  exit 2
fi

# Advisory (non-blocking) when not strict.
if [ -n "$desc" ] && [ "${words:-0}" -lt 4 ]; then
  printf '[team-governance] note: task "%s" looks thin — prefer a named deliverable.\n' "$desc"
fi
exit 0
