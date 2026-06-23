#!/usr/bin/env bash
# TaskCompleted hook (agent teams) — extends the hub's "reproduce the gate before
# accepting a worker's done-claim" doctrine (supervisor-verification.md /
# verifier-edge-guard.sh) to the teammate boundary: a teammate may not mark a task
# COMPLETE without evidence that the work was actually verified.
#
# Contract (per docs/claude-references/agent-teams.md): TaskCompleted runs when a task
# is being marked complete; **exit code 2 prevents completion + sends the stderr text
# back as feedback**. Any other exit code allows completion.
#
# DESIGN (telemetry-first, fail-open — matches verifier-edge-guard.sh):
#   - Allow (exit 0) on any parse uncertainty.
#   - Hard-block (exit 2) ONLY when TEAM_GOVERNANCE_STRICT=1 AND the completion text
#     carries NO verification evidence. Otherwise emit an advisory note and allow.
#   - SHIPS UNWIRED. TaskCompleted payload schema unconfirmed on a live run; confirm then
#     tighten the field list + evidence regex.
#
# NOTE: stderr is intentionally NOT redirected — the exit-2 feedback to a teammate is
# delivered via stderr. Helper-command noise is suppressed inline (2>/dev/null) instead.

PAYLOAD="$(cat 2>/dev/null || true)"

result=""
if command -v jq >/dev/null 2>&1 && [ -n "$PAYLOAD" ]; then
  result="$(printf '%s' "$PAYLOAD" | jq -r '
    (.task.result // .task.summary // .result // .summary // .task.completion // "")
  ' 2>/dev/null)"
fi
[ "$result" = "null" ] && result=""

# Evidence signal: test output, an explicit verification verb, a gate/pass marker, or a
# command/log reference. Conservative — absence of ALL of these is the only block trigger.
has_evidence=0
if printf '%s' "$result" | grep -Eiq \
  'test|pass(ed)?|verif|coverage|gate|assert|reproduc|✓|✅|exit code|stdout|lint|build (ok|green|succeed)'; then
  has_evidence=1
fi

if [ "${TEAM_GOVERNANCE_STRICT:-0}" = "1" ] && [ -n "$result" ] && [ "$has_evidence" -eq 0 ]; then
  printf 'TaskCompleted blocked: no verification evidence in the completion summary. ' >&2
  printf 'A task is not done until its gate is reproduced (supervisor-verification.md). ' >&2
  printf 'Re-run the relevant tests/checks and include the evidence (command + result), ' >&2
  printf 'then mark complete. See plans/agent-teams-incorporation.md.' >&2
  exit 2
fi

if [ -n "$result" ] && [ "$has_evidence" -eq 0 ]; then
  printf '[team-governance] note: completion of a task lacks verification evidence.\n'
fi
exit 0
