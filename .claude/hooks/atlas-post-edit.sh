#!/usr/bin/env bash
# Atlas PostToolUse (Edit|Write|MultiEdit) — auto-refreshes the edited file's Index shard,
# keeping the goal map current on every change with no manual /atlas scan.
#
# FAIL-OPEN: never blocks. No-op if the Atlas engine (../atlas) is absent. The tool payload
# (which file was edited) arrives on stdin and is passed through to Atlas's post_edit.py.
# Writes only the gitignored .atlas/ Index — no factory pollution.
ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
ENGINE="$ROOT/../atlas/hooks/post_edit.py"
[ -f "$ENGINE" ] || exit 0
CLAUDE_PROJECT_DIR="$ROOT" python "$ENGINE" 2>/dev/null || true
exit 0
