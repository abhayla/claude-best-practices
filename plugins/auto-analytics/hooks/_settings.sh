#!/usr/bin/env bash
# _settings.sh — sourceable settings shim for the auto-analytics plugin.
#
# Reads auto-analytics-settings.json and EXPORTS the env vars the hooks + bundled scripts honor,
# mapping plain-English JSON keys onto env vars. This is the ONE place JSON->env happens.
#
# SETTINGS FILE precedence (first existing wins):
#   1. $PROJECT_ROOT/.claude/auto-analytics-settings.json   (per-project)
#   2. $HOME/.claude/auto-analytics-settings.json           (per-user global default)
#   3. <plugin>/auto-analytics-settings.default.json        (shipped default)
#
# VALUE precedence: a pre-set environment variable ALWAYS wins — we export a value ONLY when the
# var is unset, so an inline `GA_PROVISION_SA_KEY=... claude ...` is never clobbered by the JSON.
#
# SAFE TO SOURCE: no set -e/-u side effects, never exits the parent, tolerates missing jq/python3.

if [ -n "${CLAUDE_PLUGIN_ROOT:-}" ]; then
  _aa_default="$CLAUDE_PLUGIN_ROOT/auto-analytics-settings.default.json"
else
  _aa_hooks_dir="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd)"
  _aa_default="$_aa_hooks_dir/../auto-analytics-settings.default.json"
fi
_aa_root="${PROJECT_ROOT:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"

_aa_settings="$_aa_default"
[ -f "$HOME/.claude/auto-analytics-settings.json" ] && _aa_settings="$HOME/.claude/auto-analytics-settings.json"
[ -f "$_aa_root/.claude/auto-analytics-settings.json" ] && _aa_settings="$_aa_root/.claude/auto-analytics-settings.json"

# Read one top-level JSON key. jq if present, else python3, else empty (defaults apply). Always 0.
_aa_read_json() {
  local file="$1" key="$2" out=""
  [ -f "$file" ] || { printf '%s' ""; return 0; }
  if command -v jq >/dev/null 2>&1; then
    out="$(jq -r --arg k "$key" '.[$k] | values' "$file" 2>/dev/null)" || out=""
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

_aa_export() {
  local var="$1" val="$2"
  if [ -z "${!var+x}" ]; then
    export "$var=$val"
  fi
}

_aa_apply_settings() {
  local f="$_aa_settings" v
  [ -f "$f" ] || return 0

  # Master switch: enabled:false turns the plugin off (reminder silent; scripts still runnable manually).
  if [ "$(_aa_read_json "$f" enabled)" = "false" ]; then
    _aa_export AUTO_ANALYTICS_DISABLE 1
    _aa_export AUTO_ANALYTICS_REMINDER_DISABLE 1
    return 0
  fi

  [ "$(_aa_read_json "$f" web_analytics_reminder)" = "false" ] && _aa_export AUTO_ANALYTICS_REMINDER_DISABLE 1

  v="$(_aa_read_json "$f" sa_key_path)";  [ -n "$v" ] && _aa_export GA_PROVISION_SA_KEY "$v"
  v="$(_aa_read_json "$f" time_zone)";    [ -n "$v" ] && _aa_export GA_PROVISION_TZ "$v"
  v="$(_aa_read_json "$f" currency)";     [ -n "$v" ] && _aa_export GA_PROVISION_CURRENCY "$v"
  v="$(_aa_read_json "$f" gcloud_path)";  [ -n "$v" ] && _aa_export GCLOUD_PATH "$v"
}

_aa_apply_settings
