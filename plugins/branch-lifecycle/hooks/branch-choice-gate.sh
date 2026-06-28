#!/usr/bin/env bash
# PreToolUse(Edit|Write|MultiEdit) — deterministic first-edit reminder for the branch-choice menu.
#
# Fires ONLY until THIS session's marker .claude/.branch-choice-active.<session_id> exists; then
# silent. The marker is keyed by session_id (NOT one shared file) so two concurrent sessions sharing
# one working tree each get their own once-per-session menu — fixes the shared-marker collision where
# the first session to choose silenced the menu for every other session in the same tree.
#
# It ALSO does an EDIT-TIME concurrency check: if a DIFFERENT, still-live session holds the working-
# tree lock (.claude/.session-active.lock), the reminder escalates to recommend a git worktree. This
# fires at the first repo edit — the moment isolation actually matters — so it catches the collision
# regardless of which session started first (the SessionStart guard only ever warns the SECOND-
# arriving session, never the one already running).
#
# NON-BLOCKING (exit 0): injects an additionalContext reminder, NEVER denies the edit. A hard block
# would risk deadlocking subagent/automated edits and the menu's own git commands.
# FAIL-SAFE: always exits 0. OFF-SWITCH: BRANCH_CHOICE_GATE_DISABLE=1.
set -uo pipefail

SELFDIR="${CLAUDE_PLUGIN_ROOT:+$CLAUDE_PLUGIN_ROOT/hooks}"
SELFDIR="${SELFDIR:-$(cd "$(dirname "$0")" && pwd)}"

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0

# Map branch-lifecycle-settings.json -> env off-switches (a pre-set env var still wins).
PROJECT_ROOT="$ROOT"
# shellcheck source=/dev/null
[ -f "$SELFDIR/_settings.sh" ] && . "$SELFDIR/_settings.sh"

[ "${BRANCH_CHOICE_GATE_DISABLE:-0}" = "1" ] && exit 0

mkdir -p "$ROOT/.claude" 2>/dev/null || true   # so the model's `touch .claude/...marker` lands

input="$(cat 2>/dev/null || true)"
sid="$(printf '%s' "$input" | jq -r '.session_id // empty' 2>/dev/null || true)"
[ -z "$sid" ] && sid="unknown"

MARKER="$ROOT/.claude/.branch-choice-active.$sid"
[ -f "$MARKER" ] && exit 0   # THIS session already chose -> silent

# Edit-time concurrency check: is a DIFFERENT, still-live session sharing this working tree?
concurrency=""
LOCK="$ROOT/.claude/.session-active.lock"
STALE_MIN="${CONCURRENCY_STALE_MIN:-30}"
if [ -f "$LOCK" ]; then
  prev_sid="$(awk 'NR==1{print $1}' "$LOCK" 2>/dev/null)"
  prev_ts="$(awk 'NR==1{print $2}' "$LOCK" 2>/dev/null)"
  case "$prev_ts" in ''|*[!0-9]*) prev_ts=0;; esac
  age_min=$(( ( $(date +%s) - prev_ts ) / 60 ))
  if [ -n "$prev_sid" ] && [ "$prev_sid" != "$sid" ] && [ "$age_min" -lt "$STALE_MIN" ]; then
    concurrency=" CONCURRENCY: another live session ($prev_sid, ~${age_min}m ago) shares this working tree — two sessions share ONE checked-out branch and WILL collide on commits; isolate this work in a git worktree before editing: /git-branch-lifecycle work <name> (or git worktree add ../<dir> -b <branch>)."
  fi
fi

# Reminder names THIS session's exact marker path to touch (backtick-quoted for the model to copy).
reminder="BRANCH-CHOICE GATE: no branch chosen yet this session. Before this file edit, run the /branch-choice skill: present the menu (new-from-main / keep existing / switch / merge-then-new / stash), act on the owner pick, then \`touch .claude/.branch-choice-active.$sid\`. If the owner pre-authorized, pick new-from-main with a derived name and create the marker.$concurrency"

if command -v jq >/dev/null 2>&1; then
  jq -cn --arg ctx "$reminder" '{hookSpecificOutput:{hookEventName:"PreToolUse",additionalContext:$ctx}}'
else
  # Fallback (jq absent): content is controlled (no embedded double-quotes/backslashes) so static JSON is safe.
  printf '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"%s"}}\n' "$reminder"
fi
exit 0
