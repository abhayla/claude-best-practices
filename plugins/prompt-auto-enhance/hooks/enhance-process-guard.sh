#!/usr/bin/env bash
# enhance-process-guard.sh — Stop hook (PLUGIN version)
#
# Enforces ONLY that the prompt-improver's full process was shown on a substantive turn —
# its own self-check. Two settings-gated blocking classes:
#   A. score-table/review missing  (quality_checks.require_review_table = block|warn|off)
#   B. table shown but fix-details missing (quality_checks.require_fix_details = block|warn|off)
# Plus non-blocking logging (quality_checks.log_misses).
#
# DELIBERATELY NOT PORTED (hub-wide governance, excluded by design): decide-don't-ask,
# narrate-and-stop, plan-before-coding, role routing. Those live in the hub's own hook.
#
# Settings read FRESH each turn (project override else plugin default). Requires jq.
exec 2>/dev/null
input=$(cat)
command -v jq >/dev/null || exit 0

plugin_root="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
# Same precedence as the reminder hook: default -> GLOBAL (~/.claude) -> project -> env.
settings="$plugin_root/enhance-settings.default.json"
[ -f "$HOME/.claude/enhance-settings.json" ] && settings="$HOME/.claude/enhance-settings.json"
[ -f "$root/.claude/enhance-settings.json" ] && settings="$root/.claude/enhance-settings.json"
[ -n "$ENHANCE_SETTINGS_FILE" ] && [ -f "$ENHANCE_SETTINGS_FILE" ] && settings="$ENHANCE_SETTINGS_FILE"
getj() { jq -r "$1 // empty" "$settings" 2>/dev/null; }

# No enforcement when the improver isn't running / isn't displaying.
[ "$(jq -r '.enabled' "$settings" 2>/dev/null)" = "false" ] && exit 0
mode="$(getj '.when_to_run')"; case "$mode" in ask_first|off) exit 0 ;; esac
[ "$(jq -r '.display.show_the_process' "$settings" 2>/dev/null)" = "false" ] && exit 0

tp=$(printf '%s' "$input" | jq -r '.transcript_path // ""')
[ -z "$tp" ] || [ ! -f "$tp" ] && exit 0

last_text=$(jq -r '
  if .type=="user" and ((.message.content|type)=="string" or ([.message.content[]?|.type]|index("tool_result")|not))
  then "@@TURN@@"
  elif .type=="assistant"
  then ((.message.content[]? | select(.type=="text") | .text) + "\n")
  else empty end' "$tp" 2>/dev/null | awk 'BEGIN{RS="@@TURN@@"} END{printf "%s", $0}')
[ -z "$last_text" ] && exit 0
full=$(printf '%s' "$last_text" | tr '[:upper:]' '[:lower:]' | sed -e '/./,$!d')

subchars="$(getj '.when_to_enhance.min_response_size_to_check_characters')"; case "$subchars" in ''|*[!0-9]*) subchars=300 ;; esac
[ "${#last_text}" -lt "$subchars" ] && exit 0

trivial=""
printf '%s' "$full" | head -1 | grep -qE "ran (your )?input as-is|no change — ran|no enhancement" && [ "${#last_text}" -lt 600 ] && trivial="1"
[ -n "$trivial" ] && exit 0

card=""
printf '%s' "$full" | grep -qE "reviewer-after|reviewer col|blind re-?grade|independent[ -]reviewer" && card="1"
substance=""
printf '%s' "$full" | grep -qE "diagnosis:|changes applied|missing_role|missing_context|missing_output|vague_intent|under_constrained|missing_structure|missing_constraint|grade: a|grade a[^a-z]|0 fix|no fix|zero fix" && substance="1"

block() { jq -nc --arg r "$1" '{decision:"block", reason:$r}'; exit 0; }

# A. require the score-table + second-opinion review.
mode_card="$(getj '.quality_checks.require_review_table')"; [ -z "$mode_card" ] && mode_card="block"
# If the user turned the second-opinion review OFF, there's no table to demand.
[ "$(jq -r '.display.show.second_opinion_review' "$settings" 2>/dev/null)" = "false" ] && mode_card="off"
# Adaptive display: in only_weak_prompts a strong prompt legitimately renders a one-liner (no table).
[ "$(getj '.display.show_when')" = "only_weak_prompts" ] && mode_card="off"
if [ -z "$card" ] && [ "$mode_card" = "block" ]; then
  block "STOP BLOCKED (prompt-auto-enhance: full process not shown). This substantive turn shows no second-opinion 'Reviewer-after' score table. Render the FULL process UP FRONT: *Enhanced summary + step log + score table WITH the Reviewer-after column + Original->Improved prompt + Role line. If the prompt was trivial, make the first line '*Enhanced: no change — ran your input as-is*'."
fi

# B. require fix-details (decoupled from the table so it survives review-off).
mode_sub="$(getj '.quality_checks.require_fix_details')"; [ -z "$mode_sub" ] && mode_sub="block"
[ "$(getj '.display.show_when')" = "only_weak_prompts" ] && mode_sub="off"
want_sub=""
{ [ "$(getj '.display.show.score_table')" = "true" ] || [ "$(getj '.display.show.whats_wrong')" = "true" ]; } && want_sub="1"
if [ -n "$want_sub" ] && [ -z "$substance" ] && [ "$mode_sub" = "block" ]; then
  block "STOP BLOCKED (prompt-auto-enhance: fix-details missing). The score table shows numbers but not the diagnose->fix detail — add a 'Diagnosis:' block, a per-dimension Fix column, and a 'Changes Applied' list (taxonomy: VAGUE_INTENT, MISSING_CONTEXT, UNDER_CONSTRAINED, MISSING_OUTPUT_SPEC, MISSING_ROLE...)."
fi

# C. Logging (non-blocking)
if [ "$(getj '.quality_checks.log_misses')" = "true" ]; then
  log="$root/.claude/.enhance-plugin-misses.log"
  [ -z "$card" ] && printf '%s\treview-table-miss (len=%s)\n' "$(jq -rn 'now|todate' 2>/dev/null || echo now)" "${#last_text}" >> "$log" 2>/dev/null
fi
exit 0
