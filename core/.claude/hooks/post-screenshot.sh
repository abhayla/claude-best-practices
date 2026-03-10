#!/bin/bash
# =============================================================================
# Claude Code Screenshot Post-Processing Hook (PostToolUse)
# =============================================================================
# Combines resize + validation into a single hook for efficiency.
# 1. Resizes screenshots >1800px to prevent Claude API 400 errors
# 2. Retries failed ADB captures (< 1KB)
# 3. Records screenshot metadata in workflow state
#
# Triggers: PostToolUse on browser_take_screenshot and Bash (screencap commands)
# Replaces: post-screenshot-resize.sh + post-screenshot-validate.sh
# =============================================================================

# Source shared utilities for consistent stdin parsing
trap 'exit 0' ERR
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
source "$SCRIPT_DIR/hook-utils.sh" 2>/dev/null || exit 0
parse_hook_input || exit 0

TOOL_NAME="$HOOK_TOOL_NAME"
TOOL_INPUT="$HOOK_TOOL_INPUT"

SCREENSHOT_PATH=""
SCREENSHOT_SOURCE=""

# --- Phase 1: Identify screenshot and resize ---

case "$TOOL_NAME" in
  *browser_take_screenshot*)
    SCREENSHOT_PATH=$(printf '%s' "$TOOL_INPUT" | python -c "import sys,json; print(json.load(sys.stdin).get('filename',''))" 2>/dev/null)
    SCREENSHOT_SOURCE="playwright"
    if [ -n "$SCREENSHOT_PATH" ] && [ -f "$SCREENSHOT_PATH" ]; then
      python "$SCRIPT_DIR/resize_screenshot.py" "$SCREENSHOT_PATH"
    fi
    ;;
  Bash)
    CMD=$(printf '%s' "$TOOL_INPUT" | python -c "import sys,json; print(json.load(sys.stdin).get('command',''))" 2>/dev/null)
    if ! printf '%s' "$CMD" | grep -qE "screencap|screenshot"; then
      exit 0
    fi
    SCREENSHOT_SOURCE="adb"

    # Ensure screenshots directory exists
    mkdir -p docs/testing/screenshots 2>/dev/null

    # Extract actual output file path from redirect (> path.png)
    SCREENSHOT_PATH=$(printf '%s' "$CMD" | grep -oE '>\s*[^ ]+\.png' | sed 's/^>\s*//')

    # Resolve known shell variables before the unresolved-variable check
    if [ -n "$SCREENSHOT_PATH" ]; then
      SCREENSHOT_PATH=$(printf '%s' "$SCREENSHOT_PATH" | sed 's|\$SCREENSHOT_DIR|docs/testing/screenshots|g')
    fi

    # If path still contains unresolved shell variables ($), clear it
    if [ -n "$SCREENSHOT_PATH" ] && printf '%s' "$SCREENSHOT_PATH" | grep -qF '$'; then
      SCREENSHOT_PATH=""
    fi

    if [ -n "$SCREENSHOT_PATH" ] && [ -f "$SCREENSHOT_PATH" ]; then
      python "$SCRIPT_DIR/resize_screenshot.py" "$SCREENSHOT_PATH"
      # Check if file is still invalid (< 1KB = failed capture)
      FILE_SIZE=$(wc -c < "$SCREENSHOT_PATH" 2>/dev/null | tr -d ' ')
      if [ "${FILE_SIZE:-0}" -lt 1000 ]; then
        # Re-capture without -d flag
        adb exec-out screencap -p > "$SCREENSHOT_PATH" 2>/dev/null
        python "$SCRIPT_DIR/resize_screenshot.py" "$SCREENSHOT_PATH"
      fi
    else
      # Fallback: process recently modified screenshots
      python "$SCRIPT_DIR/resize_screenshot.py" --recent
      # Try to extract path for validation phase
      SCREENSHOT_PATH=$(extract_screenshot_path "$CMD" 2>/dev/null)
    fi
    ;;
  *)
    exit 0
    ;;
esac

# --- Phase 2: Validate and record metadata in workflow state ---

if [ -z "$SCREENSHOT_PATH" ]; then exit 0; fi
if [ ! -f "$WORKFLOW_STATE_FILE" ]; then exit 0; fi

# Determine screenshot type from filename
SCREENSHOT_TYPE="unknown"
if printf '%s' "$SCREENSHOT_PATH" | grep -qi "_before"; then
  SCREENSHOT_TYPE="before"
elif printf '%s' "$SCREENSHOT_PATH" | grep -qi "_after"; then
  SCREENSHOT_TYPE="after"
fi

# Validate file exists and has content
FILE_SIZE=0
FILE_VALID="false"
if [ -f "$SCREENSHOT_PATH" ]; then
  FILE_SIZE=$(wc -c < "$SCREENSHOT_PATH" 2>/dev/null | tr -d ' ')
  if [ "${FILE_SIZE:-0}" -gt 100 ]; then
    FILE_VALID="true"
  fi
fi

# Record metadata in workflow state
TIMESTAMP=$(date -Iseconds 2>/dev/null || date +"%Y-%m-%dT%H:%M:%S")
python -c "
import json, os, tempfile
sf = '$WORKFLOW_STATE_FILE'
if not os.path.exists(sf):
    exit(0)
with open(sf) as f:
    d = json.load(f)

# Ensure screenshotsCaptured list exists
if 'screenshotsCaptured' not in d:
    d['screenshotsCaptured'] = []

# Append screenshot metadata
d['screenshotsCaptured'].append({
    'path': '$SCREENSHOT_PATH',
    'timestamp': '$TIMESTAMP',
    'source': '$SCREENSHOT_SOURCE',
    'type': '$SCREENSHOT_TYPE',
    'validated': True if '$FILE_VALID' == 'true' else False,
    'fileSize': int('$FILE_SIZE') if '$FILE_SIZE'.isdigit() else 0
})

# Update step6_screenshots before/after paths
steps = d.get('steps', {})
s6 = steps.get('step6_screenshots', {})
if '$SCREENSHOT_TYPE' == 'before':
    s6['before'] = '$SCREENSHOT_PATH'
elif '$SCREENSHOT_TYPE' == 'after':
    s6['after'] = '$SCREENSHOT_PATH'
steps['step6_screenshots'] = s6
d['steps'] = steps

fd, tmp = tempfile.mkstemp(dir='.claude')
with os.fdopen(fd, 'w') as f:
    json.dump(d, f, indent=2)
os.replace(tmp, sf)
" 2>/dev/null

# Print status message
if [ "$FILE_VALID" = "true" ]; then
  echo "Screenshot processed: $SCREENSHOT_PATH (${FILE_SIZE} bytes, type=$SCREENSHOT_TYPE, source=$SCREENSHOT_SOURCE)"
else
  echo "WARNING: Screenshot validation failed for $SCREENSHOT_PATH"
  if [ ! -f "$SCREENSHOT_PATH" ]; then
    echo "  File does not exist"
  elif [ "${FILE_SIZE:-0}" -le 100 ]; then
    echo "  File too small (${FILE_SIZE} bytes) - may be empty or corrupt"
  fi
fi

log_event "SCREENSHOT_CAPTURED" "path=$SCREENSHOT_PATH" "source=$SCREENSHOT_SOURCE" "type=$SCREENSHOT_TYPE" "valid=$FILE_VALID" "size=$FILE_SIZE"

exit 0
