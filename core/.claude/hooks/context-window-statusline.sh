#!/bin/bash
# context-window-statusline.sh — Statusline script + PostToolUse bridge
# Precise context window monitoring using Claude Code's statusline feature.
#
# HOW IT WORKS (two-part system):
#
#   Part 1 — Statusline script (this file, dual-purpose):
#     Claude Code calls this script to render the status bar. It receives
#     context window metrics as environment variables and writes them to
#     a bridge file for the hook to read.
#
#   Part 2 — PostToolUse hook reads the bridge file and warns Claude
#     when remaining context drops below thresholds.
#
# SETUP (two settings needed):
#
#   1. Configure statusline in settings.json:
#      {
#        "statusline": ".claude/hooks/context-window-statusline.sh"
#      }
#
#   2. Configure the PostToolUse hook in settings.json:
#      {
#        "hooks": {
#          "PostToolUse": [
#            {
#              "matcher": "*",
#              "command": ".claude/hooks/context-window-statusline-hook.sh"
#            }
#          ]
#        }
#      }
#
# Environment variables provided by Claude Code statusline:
#   CLAUDE_CONTEXT_WINDOW_TOKENS  — total context window size
#   CLAUDE_CONTEXT_CURRENT_TOKENS — tokens currently used
#
# If your Claude Code version does not expose these variables,
# use context-window-monitor.sh (tool-count heuristic) instead.

SESSION_ID=${CLAUDE_SESSION_ID:-default}
BRIDGE_DIR="${TMPDIR:-/tmp}/claude-context-monitor"
BRIDGE_FILE="$BRIDGE_DIR/session-$SESSION_ID.metrics"

mkdir -p "$BRIDGE_DIR"

# --- Statusline output ---
TOTAL=${CLAUDE_CONTEXT_WINDOW_TOKENS:-0}
USED=${CLAUDE_CONTEXT_CURRENT_TOKENS:-0}

if [[ $TOTAL -gt 0 ]]; then
  # Account for auto-compact buffer (~16.5% reserved by Claude Code)
  COMPACT_BUFFER=$(( TOTAL * 165 / 1000 ))
  USABLE=$(( TOTAL - COMPACT_BUFFER ))
  if [[ $USABLE -le 0 ]]; then
    USABLE=$TOTAL
  fi
  PCT_USED=$(( USED * 100 / USABLE ))
  PCT_REMAINING=$(( 100 - PCT_USED ))
  if [[ $PCT_REMAINING -lt 0 ]]; then
    PCT_REMAINING=0
  fi

  # Write metrics to bridge file for the hook
  echo "$PCT_REMAINING" > "$BRIDGE_FILE"

  # Statusline display
  if [[ $PCT_REMAINING -le 25 ]]; then
    echo "CTX: ${PCT_REMAINING}% remaining [CRITICAL]"
  elif [[ $PCT_REMAINING -le 35 ]]; then
    echo "CTX: ${PCT_REMAINING}% remaining [WARNING]"
  else
    echo "CTX: ${PCT_REMAINING}% remaining"
  fi
else
  echo "CTX: --"
fi
