#!/usr/bin/env bash
# web-analytics-reminder.sh — SessionStart, ADVISORY only.
#
# Nudges once at session start when THIS looks like a web project that has NOT been instrumented
# yet (no .claude/analytics-inventory.json). Reminds the owner that the auto-google-analytics plugin can
# set up GA4 autonomously with /auto-google-analytics. It NEVER provisions, edits, or blocks — just prints.
#
# FAIL-SAFE: always exits 0. OFF-SWITCH: AUTO_GOOGLE_ANALYTICS_REMINDER_DISABLE=1 (or enabled:false /
# web_analytics_reminder:false in auto-google-analytics-settings.json, applied by _settings.sh).
set -uo pipefail

SELFDIR="${CLAUDE_PLUGIN_ROOT:+$CLAUDE_PLUGIN_ROOT/hooks}"
SELFDIR="${SELFDIR:-$(cd "$(dirname "$0")" 2>/dev/null && pwd)}"

ROOT="$(git rev-parse --show-toplevel 2>/dev/null || pwd)" || exit 0

# Map auto-google-analytics-settings.json -> env (a pre-set env var still wins).
PROJECT_ROOT="$ROOT"
# shellcheck source=/dev/null
[ -f "$SELFDIR/_settings.sh" ] && . "$SELFDIR/_settings.sh"

[ "${AUTO_GOOGLE_ANALYTICS_REMINDER_DISABLE:-0}" = "1" ] && exit 0
[ "${AUTO_GOOGLE_ANALYTICS_DISABLE:-0}" = "1" ] && exit 0

# Already instrumented? Then nothing to nudge.
[ -f "$ROOT/.claude/analytics-inventory.json" ] && exit 0

# Web project heuristic: any HTML, or a package.json naming a web framework.
is_web=0
if ls "$ROOT"/*.html >/dev/null 2>&1 || ls "$ROOT"/public/*.html >/dev/null 2>&1; then
  is_web=1
elif [ -f "$ROOT/package.json" ] \
     && grep -qiE '"(next|nuxt|vue|astro|svelte|@sveltejs|react-dom|vite|gatsby)"' "$ROOT/package.json" 2>/dev/null; then
  is_web=1
fi
[ "$is_web" = 0 ] && exit 0

echo "AUTO-ANALYTICS: this looks like a web project with no analytics yet (no .claude/analytics-inventory.json)."
echo "  Run /auto-google-analytics to set up GA4 end-to-end autonomously (provision -> inject -> verify)."
echo "  Needs a service-account key (set sa_key_path in auto-google-analytics-settings.json); without it you get guided manual setup."
exit 0
