#!/usr/bin/env bash
# One-command entry point for the clean-room plugin-validation pipeline.
# See docs/plugin-validation-pipeline.md. All logic lives in the Python module
# below; this wrapper only exists so the command reads as a single verb.
set -euo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python "$SCRIPT_DIR/validate_plugin_cleanroom.py" "$@"
