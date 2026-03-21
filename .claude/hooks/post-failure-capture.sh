#!/bin/bash
# post-failure-capture.sh — PostToolUse hook for Bash
# When a Bash command fails (non-zero exit) and looks like a test command,
# logs the failure context for the learning pipeline.
#
# Configuration:
#   Event: PostToolUse
#   Matcher: Bash
#   Exit codes: 0 = allow (advisory only, never blocks)
#
# Writes to: /tmp/claude-failure-log/session-{id}.jsonl
# Read by: /learn-n-improve session (gathers evidence from this log)

SESSION_ID=${CLAUDE_SESSION_ID:-default}
LOG_DIR="${TMPDIR:-/tmp}/claude-failure-log"
LOG_FILE="$LOG_DIR/session-$SESSION_ID.jsonl"

mkdir -p "$LOG_DIR"

# Parse tool output for exit code
EXIT_CODE=$(echo "$TOOL_OUTPUT" | jq -r '.exit_code // empty' 2>/dev/null)
if [[ -z "$EXIT_CODE" ]] || [[ "$EXIT_CODE" == "0" ]]; then
  exit 0
fi

# Extract the command that failed
COMMAND=$(echo "$TOOL_INPUT" | jq -r '.command // empty' 2>/dev/null)
if [[ -z "$COMMAND" ]]; then
  exit 0
fi

# Only capture test-related and build-related failures
if ! echo "$COMMAND" | grep -qiE '(pytest|jest|vitest|test|build|lint|check|compile|tsc|mypy|gradle)'; then
  exit 0
fi

# Extract first 500 chars of output for context
OUTPUT_PREVIEW=$(echo "$TOOL_OUTPUT" | jq -r '.stdout // .stderr // empty' 2>/dev/null | head -20)

# Log as JSONL entry
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date +"%Y-%m-%dT%H:%M:%SZ")
jq -nc \
  --arg ts "$TIMESTAMP" \
  --arg cmd "$COMMAND" \
  --arg exit "$EXIT_CODE" \
  --arg preview "$OUTPUT_PREVIEW" \
  '{timestamp: $ts, command: $cmd, exit_code: $exit, output_preview: $preview}' \
  >> "$LOG_FILE" 2>/dev/null

# Advisory only — never block
exit 0
