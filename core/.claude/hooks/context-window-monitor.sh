#!/bin/bash
# context-window-monitor.sh — PostToolUse hook for all tools
# Tracks tool use count per session and warns when context may be degrading.
#
# Rationale: Long sessions degrade output quality (context rot). This hook
# counts tool invocations and emits warnings at configurable thresholds,
# prompting Claude to use /handover or the context-reducer agent.
#
# This is the portable version — works everywhere without statusline.
# For precise context % monitoring, see context-window-statusline.sh.
#
# Configuration:
#   Event: PostToolUse
#   Matcher: * (all tools)
#   Exit codes: 0 = no warning, 2 = critical warning fed back to Claude
#
# Environment variables (optional):
#   CONTEXT_WARN_THRESHOLD  — tool uses before WARNING (default: 50)
#   CONTEXT_CRIT_THRESHOLD  — tool uses before CRITICAL (default: 80)
#   CONTEXT_DEBOUNCE        — tool uses between repeated warnings (default: 10)
#
# Settings.json entry:
#   {
#     "hooks": {
#       "PostToolUse": [
#         {
#           "matcher": "*",
#           "command": ".claude/hooks/context-window-monitor.sh"
#         }
#       ]
#     }
#   }

WARN_THRESHOLD=${CONTEXT_WARN_THRESHOLD:-50}
CRIT_THRESHOLD=${CONTEXT_CRIT_THRESHOLD:-80}
DEBOUNCE=${CONTEXT_DEBOUNCE:-10}

# Session-scoped counter file
SESSION_ID=${CLAUDE_SESSION_ID:-default}
COUNTER_DIR="${TMPDIR:-/tmp}/claude-context-monitor"
COUNTER_FILE="$COUNTER_DIR/session-$SESSION_ID.count"

mkdir -p "$COUNTER_DIR"

# Increment counter
if [[ -f "$COUNTER_FILE" ]]; then
  COUNT=$(cat "$COUNTER_FILE")
  COUNT=$((COUNT + 1))
else
  COUNT=1
fi
echo "$COUNT" > "$COUNTER_FILE"

# Determine severity
SEVERITY=""
if [[ $COUNT -ge $CRIT_THRESHOLD ]]; then
  SEVERITY="CRITICAL"
elif [[ $COUNT -ge $WARN_THRESHOLD ]]; then
  SEVERITY="WARNING"
fi

# No threshold reached — allow silently
if [[ -z "$SEVERITY" ]]; then
  exit 0
fi

# Debounce: only warn every N tool uses after threshold
OVER_THRESHOLD=$((COUNT - WARN_THRESHOLD))
if [[ $OVER_THRESHOLD -gt 0 ]] && [[ $((OVER_THRESHOLD % DEBOUNCE)) -ne 0 ]]; then
  exit 0
fi

# Emit warning
if [[ "$SEVERITY" == "CRITICAL" ]]; then
  echo "CONTEXT MONITOR [$SEVERITY]: $COUNT tool uses in this session."
  echo ""
  echo "Context window is likely heavily consumed. Output quality degrades in long sessions."
  echo "Recommended actions (pick one):"
  echo "  1. Run /handover to save session state and start fresh"
  echo "  2. Use the context-reducer agent to compress completed work"
  echo "  3. Delegate remaining sub-tasks to subagents (separate context windows)"
  echo ""
  echo "See context-management rule #7: break work into atomic plans of 2-3 tasks in fresh subagent contexts."
  exit 2
else
  echo "CONTEXT MONITOR [$SEVERITY]: $COUNT tool uses in this session."
  echo ""
  echo "Consider whether context is getting large. If working on many files or sub-tasks:"
  echo "  - Write critical state to scratchpad.md (survives compaction)"
  echo "  - Delegate bulk work to subagents to preserve main context"
  echo "  - Run /handover if switching tasks or nearing completion"
  # WARNING is non-blocking (exit 0), only CRITICAL blocks
  exit 0
fi
