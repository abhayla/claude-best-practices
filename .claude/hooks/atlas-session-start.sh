#!/usr/bin/env bash
# Atlas SessionStart — runs the Goal Pulse (and a first scaffold+scan if no Index yet),
# so Atlas surfaces the project's goal status hands-free every session.
#
# FAIL-OPEN: never blocks a session. No-op if the Atlas engine (../atlas, a sibling repo)
# is absent. The Atlas Index it writes (.atlas/) stays gitignored — no factory pollution.
# stdout (the pulse) is injected as session context; stderr is suppressed.
ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
ENGINE="$ROOT/../atlas/hooks/session_start.py"
[ -f "$ENGINE" ] || exit 0
CLAUDE_PROJECT_DIR="$ROOT" python "$ENGINE" 2>/dev/null || true
exit 0
