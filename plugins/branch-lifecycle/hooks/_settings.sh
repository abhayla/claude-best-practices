#!/usr/bin/env bash
# _settings.sh — sourceable settings shim for the branch-lifecycle plugin.
#
# Reads branch-lifecycle-settings.json and EXPORTS the env off-switches the hooks already honor,
# mapping the plain-English JSON keys onto the env vars. This is the ONE place JSON->env happens,
# so the hooks themselves only ever read env vars.
#
# SETTINGS FILE precedence (first existing wins):
#   1. $PROJECT_ROOT/.claude/branch-lifecycle-settings.json   (per-project)
#   2. $HOME/.claude/branch-lifecycle-settings.json           (per-user global default)
#   3. <plugin>/branch-lifecycle-settings.default.json        (shipped default)
#
# VALUE precedence: a pre-set environment variable ALWAYS wins — we export a value ONLY when the
# var is unset, so a user's inline `AUTO_MERGE=0 claude ...` is never clobbered by the JSON.
#
# SAFE TO SOURCE: no `set -e`/`set -u` side effects, never exits the parent, tolerates a missing
# jq AND a missing python3 (in which case no value is read and the shipped defaults apply).

# --- locate the settings file --------------------------------------------------------------------
if [ -n "${CLAUDE_PLUGIN_ROOT:-}" ]; then
  _bl_default="$CLAUDE_PLUGIN_ROOT/branch-lifecycle-settings.default.json"
else
  _bl_hooks_dir="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd)"
  _bl_default="$_bl_hooks_dir/../branch-lifecycle-settings.default.json"
fi
_bl_root="${PROJECT_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"

_bl_settings="$_bl_default"
[ -f "$HOME/.claude/branch-lifecycle-settings.json" ] && _bl_settings="$HOME/.claude/branch-lifecycle-settings.json"
[ -f "$_bl_root/.claude/branch-lifecycle-settings.json" ] && _bl_settings="$_bl_root/.claude/branch-lifecycle-settings.json"

# --- helpers -------------------------------------------------------------------------------------
# Read one top-level JSON key. jq if present, else python3, else empty (defaults apply). Always 0.
_bl_read_json() {
  local file="$1" key="$2" out=""
  [ -f "$file" ] || { printf '%s' ""; return 0; }
  if command -v jq >/dev/null 2>&1; then
    out="$(jq -r --arg k "$key" '.[$k] // empty' "$file" 2>/dev/null)" || out=""
  elif command -v python3 >/dev/null 2>&1; then
    out="$(python3 -c 'import json,sys
try:
    d=json.load(open(sys.argv[1]))
    v=d.get(sys.argv[2])
    if isinstance(v,bool): print("true" if v else "false")
    elif v is not None: print(v)
except Exception: pass' "$file" "$key" 2>/dev/null)" || out=""
  fi
  printf '%s' "$out"
}

# Export VAR=VAL only if VAR is currently unset (a user-set env var wins, even if empty).
_bl_export() {
  local var="$1" val="$2"
  if [ -z "${!var+x}" ]; then
    export "$var=$val"
  fi
}

# --- map JSON -> env -----------------------------------------------------------------------------
_bl_apply_settings() {
  local f="$_bl_settings"
  [ -f "$f" ] || return 0

  # Master switch: enabled:false turns EVERYTHING off.
  if [ "$(_bl_read_json "$f" enabled)" = "false" ]; then
    _bl_export AUTO_GIT_DISABLE 1
    _bl_export AUTO_PR_DISABLE 1
    _bl_export STALE_REAPER_DISABLE 1
    _bl_export CONCURRENCY_GUARD_DISABLE 1
    _bl_export BRANCH_CHOICE_GATE_DISABLE 1
    return 0
  fi

  [ "$(_bl_read_json "$f" auto_commit_and_push)" = "false" ] && _bl_export AUTO_GIT_DISABLE 1
  [ "$(_bl_read_json "$f" auto_push)" = "false" ]            && _bl_export AUTO_GIT_PUSH 0

  [ "$(_bl_read_json "$f" auto_open_pr)" = "false" ] && _bl_export AUTO_PR_DISABLE 1
  [ "$(_bl_read_json "$f" auto_merge)" = "false" ]   && _bl_export AUTO_MERGE 0

  [ "$(_bl_read_json "$f" branch_choice_menu)" = "false" ]  && _bl_export BRANCH_CHOICE_GATE_DISABLE 1
  [ "$(_bl_read_json "$f" stale_branch_report)" = "false" ] && _bl_export STALE_REAPER_DISABLE 1

  local v
  v="$(_bl_read_json "$f" stale_branch_hours)";       [ -n "$v" ] && _bl_export STALE_BRANCH_HOURS "$v"
  [ "$(_bl_read_json "$f" concurrency_guard)" = "false" ] && _bl_export CONCURRENCY_GUARD_DISABLE 1
  v="$(_bl_read_json "$f" concurrency_stale_minutes)"; [ -n "$v" ] && _bl_export CONCURRENCY_STALE_MIN "$v"
  v="$(_bl_read_json "$f" secret_scan_cmd)";           [ -n "$v" ] && _bl_export SECRET_SCAN_CMD "$v"
}

_bl_apply_settings
