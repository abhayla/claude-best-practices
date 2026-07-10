#!/usr/bin/env bash
# inject-operating-core.sh — deliver the Fable 5 Operating Core into the session/subagent context.
# Wired for SessionStart AND SubagentStart (hooks.json): every session and every dispatched worker
# receives the distilled discipline automatically, regardless of which model runs it.
# Fail-open: any problem -> exit 0 with no output (never block a session on a missing file).

set -u

CORE_FILE="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}/manual/distilled-core.md"

[ -f "$CORE_FILE" ] || exit 0

CORE_CONTENT="$(cat "$CORE_FILE" 2>/dev/null)" || exit 0
[ -n "$CORE_CONTENT" ] || exit 0

# Emit as additionalContext via the hook JSON output contract. jq guarantees safe JSON string
# encoding; without jq, fall back to plain stdout (SessionStart hooks append stdout to context).
if command -v jq >/dev/null 2>&1; then
  jq -n --arg ctx "$CORE_CONTENT" '{hookSpecificOutput: {additionalContext: $ctx}}'
else
  printf '%s\n' "$CORE_CONTENT"
fi

exit 0
