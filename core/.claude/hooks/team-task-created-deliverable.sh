#!/usr/bin/env bash
# TaskCreated hook (agent teams) — extends the hub's "size tasks appropriately"
# best practice to the teammate boundary: a shared-task-list item must name a
# clear, self-contained DELIVERABLE, not a vague directive.
#
# Contract (per docs/claude-references/agent-teams.md): TaskCreated runs when a task
# is being created; **exit code 2 prevents creation + sends the stderr text back as
# feedback**. Any other exit code allows creation.
#
# REAL PAYLOAD SCHEMA (captured from a live in-process team, 2026-06-23 — see
# plans/agent-teams-incorporation.md §11):
#   { session_id, transcript_path, cwd, hook_event_name,
#     task_id, task_subject, task_description }
#
# DESIGN (telemetry-first, fail-open — matches verifier-edge-guard.sh):
#   - FAIL-OPEN by default — exit 0 (allow) on any parse uncertainty.
#   - Hard-block (exit 2) ONLY when TEAM_GOVERNANCE_STRICT=1 AND the task clearly lacks
#     a deliverable (subject + description together < 5 words). Otherwise advise + allow.
#
# NOTE: stderr is intentionally NOT redirected — the exit-2 feedback to a teammate is
# delivered via stderr. Helper-command noise is suppressed inline (2>/dev/null) instead.

PAYLOAD="$(cat 2>/dev/null || true)"

# Read the REAL fields. If jq is absent the values stay empty and the hook fails open.
subject="" ; desc=""
if command -v jq >/dev/null 2>&1 && [ -n "$PAYLOAD" ]; then
  subject="$(printf '%s' "$PAYLOAD" | jq -r '(.task_subject // "")'     2>/dev/null)"
  desc="$(printf    '%s' "$PAYLOAD" | jq -r '(.task_description // "")' 2>/dev/null)"
fi
[ "$subject" = "null" ] && subject=""
[ "$desc" = "null" ] && desc=""

# A real deliverable names an artifact/outcome. Judge subject+description together.
combined="$subject $desc"
words="$(printf '%s' "$combined" | tr -s '[:space:]' ' ' | wc -w | tr -d ' ')"
have_text=0
[ -n "$(printf '%s' "$combined" | tr -d '[:space:]')" ] && have_text=1

if [ "${TEAM_GOVERNANCE_STRICT:-0}" = "1" ] && [ "$have_text" -eq 1 ] && [ "${words:-0}" -lt 5 ]; then
  printf 'TaskCreated rejected: task "%s" has no clear deliverable. Restate it as a ' "$combined" >&2
  printf 'self-contained unit with a named artifact/outcome (agent-team best practice: ' >&2
  printf 'size tasks appropriately). See plans/agent-teams-incorporation.md.' >&2
  exit 2
fi

if [ "$have_text" -eq 1 ] && [ "${words:-0}" -lt 5 ]; then
  printf '[team-governance] note: task "%s" looks thin — prefer a named deliverable.\n' "$combined"
fi
exit 0
