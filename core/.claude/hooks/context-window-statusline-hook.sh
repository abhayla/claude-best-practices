#!/bin/bash
# context-window-statusline-hook.sh — PostToolUse hook (bridge reader)
# Reads context window metrics written by context-window-statusline.sh
# and warns Claude when remaining context drops below thresholds.
#
# This is Part 2 of the statusline-bridge system.
# See context-window-statusline.sh for setup instructions.
#
# Configuration:
#   Event: PostToolUse
#   Matcher: * (all tools)
#   Exit codes: 0 = no warning, 2 = critical warning fed back to Claude
#
# Environment variables (optional):
#   CONTEXT_WARN_PCT   — remaining % before WARNING (default: 35)
#   CONTEXT_CRIT_PCT   — remaining % before CRITICAL (default: 25)
#   CONTEXT_DEBOUNCE   — tool uses between repeated warnings (default: 10)

WARN_PCT=${CONTEXT_WARN_PCT:-35}
CRIT_PCT=${CONTEXT_CRIT_PCT:-25}
DEBOUNCE=${CONTEXT_DEBOUNCE:-10}

SESSION_ID=${CLAUDE_SESSION_ID:-default}
BRIDGE_DIR="${TMPDIR:-/tmp}/claude-context-monitor"
BRIDGE_FILE="$BRIDGE_DIR/session-$SESSION_ID.metrics"
DEBOUNCE_FILE="$BRIDGE_DIR/session-$SESSION_ID.debounce"

# If no bridge file exists, statusline hasn't written yet — skip silently
if [[ ! -f "$BRIDGE_FILE" ]]; then
  exit 0
fi

PCT_REMAINING=$(cat "$BRIDGE_FILE")

# Validate it's a number
if ! [[ "$PCT_REMAINING" =~ ^[0-9]+$ ]]; then
  exit 0
fi

# No threshold reached
if [[ $PCT_REMAINING -gt $WARN_PCT ]]; then
  # Reset debounce counter when context is healthy
  rm -f "$DEBOUNCE_FILE" 2>/dev/null
  exit 0
fi

# Debounce: increment counter, only warn every N calls
DEBOUNCE_COUNT=0
if [[ -f "$DEBOUNCE_FILE" ]]; then
  DEBOUNCE_COUNT=$(cat "$DEBOUNCE_FILE")
fi
DEBOUNCE_COUNT=$((DEBOUNCE_COUNT + 1))
echo "$DEBOUNCE_COUNT" > "$DEBOUNCE_FILE"

if [[ $((DEBOUNCE_COUNT % DEBOUNCE)) -ne 1 ]] && [[ $DEBOUNCE_COUNT -ne 1 ]]; then
  exit 0
fi

# Emit warning based on severity
if [[ $PCT_REMAINING -le $CRIT_PCT ]]; then
  echo "CONTEXT MONITOR [CRITICAL]: Only ${PCT_REMAINING}% context remaining."
  echo ""
  echo "Context window is nearly full. Output quality will degrade significantly."
  echo "Recommended actions (pick one):"
  echo "  1. Run /handover to save session state and start fresh"
  echo "  2. Use the context-reducer-agent to compress completed work"
  echo "  3. Delegate remaining sub-tasks to subagents (separate context windows)"
  echo ""
  echo "See context-management rule #7: break work into atomic plans of 2-3 tasks in fresh subagent contexts."
  exit 2
else
  echo "CONTEXT MONITOR [WARNING]: ${PCT_REMAINING}% context remaining."
  echo ""
  echo "Context window is getting large. Consider:"
  echo "  - Write critical state to scratchpad.md (survives compaction)"
  echo "  - Delegate bulk work to subagents to preserve main context"
  echo "  - Run /handover if switching tasks or nearing completion"
  # WARNING is non-blocking
  exit 0
fi
