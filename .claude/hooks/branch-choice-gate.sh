#!/usr/bin/env bash
# PreToolUse(Edit|Write|MultiEdit) — deterministic first-edit reminder for the branch-choice menu.
#
# Fires ONLY until the per-session marker .claude/.branch-choice-active exists; then silent. This is
# the reliable, deterministic complement to the SessionStart nudge (which can rot in a long session):
# it re-injects the branch-menu instruction at the EXACT moment of the first file edit, every session.
#
# NON-BLOCKING (exit 0): it injects an additionalContext reminder, it NEVER denies the edit. A hard
# block would risk deadlocking subagent/automated edits and the menu's own git commands; the reminder
# + the marker gate is enough to make the once-per-session menu reliable without that risk.
#
# FAIL-SAFE: always exits 0. OFF-SWITCH: BRANCH_CHOICE_GATE_DISABLE=1.
set -uo pipefail

[ "${BRANCH_CHOICE_GATE_DISABLE:-0}" = "1" ] && exit 0

ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
[ -f "$ROOT/.claude/.branch-choice-active" ] && exit 0   # already chosen this session -> silent

cat <<'JSON'
{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"BRANCH-CHOICE GATE: no branch chosen yet this session. Before this file edit, run the branch-choice skill (.claude/skills/branch-choice/SKILL.md): present the menu (new-from-main / keep existing / switch / merge-then-new / stash), act on the owner's pick, then `touch .claude/.branch-choice-active`. If the owner pre-authorized, pick new-from-main with a derived name and create the marker."}}
JSON
exit 0
