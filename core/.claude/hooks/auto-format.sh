#!/bin/bash
# PostToolUse hook: Auto-format Python files after Edit/Write
# Runs black + ruff on modified Python files in backend/

# Read stdin (hook input JSON)
INPUT=$(cat)

# Extract the file path from tool input (use printf to avoid echo mangling)
FILE_PATH=$(printf '%s' "$INPUT" | python -c "
import sys, json
try:
    data = json.load(sys.stdin)
    # Handle both Edit and Write tool inputs
    path = data.get('tool_input', {}).get('file_path', '')
    print(path)
except:
    print('')
" 2>/dev/null)

# Only format Python files in the backend directory
if [[ "$FILE_PATH" == *".py" ]] && [[ "$FILE_PATH" == *"backend/"* || "$FILE_PATH" == *"backend\\"* ]]; then
    # Resolve to absolute path if needed
    if [[ ! -f "$FILE_PATH" ]]; then
        exit 0
    fi

    # Activate backend venv and run formatters
    BACKEND_DIR="$(cd "$(dirname "$0")/../.." && pwd)/backend"

    if [[ -f "$BACKEND_DIR/venv/Scripts/activate" ]]; then
        source "$BACKEND_DIR/venv/Scripts/activate" 2>/dev/null
    elif [[ -f "$BACKEND_DIR/venv/bin/activate" ]]; then
        source "$BACKEND_DIR/venv/bin/activate" 2>/dev/null
    fi

    # Run ruff for import sorting and linting fixes (fast, handles isort too)
    ruff check --fix --quiet "$FILE_PATH" 2>/dev/null

    # Run black for code formatting
    black --quiet "$FILE_PATH" 2>/dev/null
fi

exit 0
