#!/bin/bash
# auto-learn-trigger.sh — PostToolUse hook for all tools
# Triggers learning capture reminder at configurable intervals.
# Sits between session-reminder (40) and context-monitor (50).
#
# Configuration:
#   Event: PostToolUse
#   Matcher: * (all tools)
#   Exit codes: 0 = no action (advisory only, never blocks)
#
# Environment variables (optional):
#   LEARN_TRIGGER_THRESHOLD — tool uses before first reminder (default: 60)
#   LEARN_TRIGGER_INTERVAL  — tool uses between repeated reminders (default: 20)

THRESHOLD=${LEARN_TRIGGER_THRESHOLD:-60}
INTERVAL=${LEARN_TRIGGER_INTERVAL:-20}

SESSION_ID=${CLAUDE_SESSION_ID:-default}
COUNTER_DIR="${TMPDIR:-/tmp}/claude-context-monitor"
COUNTER_FILE="$COUNTER_DIR/session-$SESSION_ID.count"

# Read current counter (shared with context-window-monitor)
if [[ ! -f "$COUNTER_FILE" ]]; then
  exit 0
fi

COUNT=$(cat "$COUNTER_FILE")

# Below threshold — silent
if [[ $COUNT -lt $THRESHOLD ]]; then
  exit 0
fi

# At threshold or at interval
OVER=$((COUNT - THRESHOLD))
if [[ $OVER -eq 0 ]] || [[ $((OVER % INTERVAL)) -eq 0 ]]; then
  echo "LEARN TRIGGER: $COUNT tool uses — consider running /learn-n-improve session"
  echo ""
  echo "This captures error-fix-lesson triples from this session's work."
  echo "Also check /self-improve for pending external discoveries."
fi

# Advisory only — never block
exit 0
