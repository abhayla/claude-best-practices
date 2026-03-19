#!/bin/bash
# session-reminder.sh — PostToolUse hook for all tools
# Reminds Claude to checkpoint progress via /save-session at configurable intervals.
#
# Complements context-window-monitor.sh: session-reminder fires first (default: 40)
# as a save checkpoint prompt, then context-monitor fires later (default: 50) for
# handover/compaction. Natural escalation: save → compress → start fresh.
#
# Configuration:
#   Event: PostToolUse
#   Matcher: * (all tools)
#   Exit codes: always 0 (non-blocking, advisory only)
#
# Environment variables (optional):
#   SESSION_REMIND_THRESHOLD — tool uses before first reminder (default: 40)
#   SESSION_REMIND_DEBOUNCE  — tool uses between repeated reminders (default: 20)
#
# Settings.json entry:
#   {
#     "hooks": {
#       "PostToolUse": [
#         {
#           "matcher": "*",
#           "command": ".claude/hooks/session-reminder.sh"
#         }
#       ]
#     }
#   }

THRESHOLD=${SESSION_REMIND_THRESHOLD:-40}
DEBOUNCE=${SESSION_REMIND_DEBOUNCE:-20}

SESSION_ID=${CLAUDE_SESSION_ID:-default}
COUNTER_DIR="${TMPDIR:-/tmp}/claude-session-reminder"
COUNTER_FILE="$COUNTER_DIR/session-$SESSION_ID.count"

mkdir -p "$COUNTER_DIR"

if [[ -f "$COUNTER_FILE" ]]; then
  COUNT=$(cat "$COUNTER_FILE")
  COUNT=$((COUNT + 1))
else
  COUNT=1
fi
echo "$COUNT" > "$COUNTER_FILE"

# Not yet at threshold
if [[ $COUNT -lt $THRESHOLD ]]; then
  exit 0
fi

# Debounce: only remind at threshold, then every DEBOUNCE calls after
OVER=$((COUNT - THRESHOLD))
if [[ $OVER -gt 0 ]] && [[ $((OVER % DEBOUNCE)) -ne 0 ]]; then
  exit 0
fi

echo "SESSION REMINDER: $COUNT tool uses in this session."
echo ""
echo "Consider running /save-session to checkpoint your progress."
echo "This creates a resumable session file in .claude/sessions/ that"
echo "/start-session can restore in a future conversation."
exit 0
