#!/usr/bin/env bash
# enhance-process-guard.sh — Stop hook (PLUGIN version)
#
# Enforces ONLY that the prompt-auto-enhance FULL PROCESS was rendered on a substantive
# turn — its own self-governance. Two settings-gated blocking classes:
#   A. reviewer-card missing  (enforce.reviewer_card = block|telemetry|off)
#   B. card present but diagnose->fix substance missing (enforce.diagnosis_substance = ...)
# Plus non-blocking telemetry (enforce.telemetry).
#
# DELIBERATELY NOT PORTED (hub-wide governance, excluded from this plugin per design D4):
# over-ask / decide-don't-ask, narrate-and-stop, keepgoing cap, plan-before-coding, role
# routing. Those live in the hub's own hook, not here.
#
# Settings read FRESH each turn (project override else plugin default). Requires jq.
exec 2>/dev/null
input=$(cat)
command -v jq >/dev/null || exit 0

plugin_root="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
override="$root/.claude/enhance-settings.json"
settings="$plugin_root/enhance-settings.default.json"
[ -f "$override" ] && settings="$override"
[ -n "$ENHANCE_SETTINGS_FILE" ] && [ -f "$ENHANCE_SETTINGS_FILE" ] && settings="$ENHANCE_SETTINGS_FILE"
getj() { jq -r "$1 // empty" "$settings" 2>/dev/null; }

# Master switch + run_mode gates: no enforcement when the pipeline isn't rendering.
# (raw read: jq's `// empty` would collapse boolean false to empty)
[ "$(jq -r '.enabled' "$settings" 2>/dev/null)" = "false" ] && exit 0
mode="$(getj '.run_mode')"; case "$mode" in ask|silent|off) exit 0 ;; esac

tp=$(printf '%s' "$input" | jq -r '.transcript_path // ""')
[ -z "$tp" ] || [ ! -f "$tp" ] && exit 0

# Aggregate this turn's assistant text (everything after the last real user prompt).
last_text=$(jq -r '
  if .type=="user" and ((.message.content|type)=="string" or ([.message.content[]?|.type]|index("tool_result")|not))
  then "@@TURN@@"
  elif .type=="assistant"
  then ((.message.content[]? | select(.type=="text") | .text) + "\n")
  else empty end' "$tp" 2>/dev/null | awk 'BEGIN{RS="@@TURN@@"} END{printf "%s", $0}')
[ -z "$last_text" ] && exit 0
full=$(printf '%s' "$last_text" | tr '[:upper:]' '[:lower:]' | sed -e '/./,$!d')

subchars="$(getj '.triggers.substantive_output_chars')"; case "$subchars" in ''|*[!0-9]*) subchars=300 ;; esac
[ "${#last_text}" -lt "$subchars" ] && exit 0

# Trivial-declaration exemption (a short "ran as-is" turn).
trivial=""
printf '%s' "$full" | head -1 | grep -qE "ran (your )?input as-is|no change — ran|no enhancement" && [ "${#last_text}" -lt 600 ] && trivial="1"
[ -n "$trivial" ] && exit 0

card=""
printf '%s' "$full" | grep -qE "reviewer-after|reviewer col|blind re-?grade|independent[ -]reviewer" && card="1"
substance=""
printf '%s' "$full" | grep -qE "diagnosis:|changes applied|missing_role|missing_context|missing_output|vague_intent|under_constrained|missing_structure|missing_constraint|grade: a|grade a[^a-z]|0 fix|no fix|zero fix" && substance="1"

block() { jq -nc --arg r "$1" '{decision:"block", reason:$r}'; exit 0; }

# A. reviewer-card enforcement. If the user turned the independent reviewer OFF, there is no
# card to demand — disable this block (else we'd loop-block a turn for omitting a disabled component).
mode_card="$(getj '.enforce.reviewer_card')"; [ -z "$mode_card" ] && mode_card="block"
[ "$(jq -r '.run.independent_reviewer' "$settings" 2>/dev/null)" = "false" ] && mode_card="off"
if [ -z "$card" ] && [ "$mode_card" = "block" ]; then
  block "STOP BLOCKED (prompt-auto-enhance: full process not rendered). This substantive turn shows no independent-reviewer 'Reviewer-after' per-dimension card. Render the FULL process UP FRONT: *Enhanced banner + transcript + grade card WITH the Reviewer-after column + Original->Final prompt + Role line. If the prompt was trivial, make the first line '*Enhanced: no change — ran your input as-is*'."
fi

# B. diagnose->fix substance enforcement. Decoupled from the card (so it still fires when the
# reviewer is off) — gated instead on the diagnosis/grade-card components being expected.
mode_sub="$(getj '.enforce.diagnosis_substance')"; [ -z "$mode_sub" ] && mode_sub="block"
want_sub=""
{ [ "$(getj '.show.grade_card')" = "true" ] || [ "$(getj '.show.diagnosis')" = "true" ]; } && want_sub="1"
if [ -n "$want_sub" ] && [ -z "$substance" ] && [ "$mode_sub" = "block" ]; then
  block "STOP BLOCKED (prompt-auto-enhance: per-step substance missing). The card shows scores but not the diagnose->fix substance — add a 'Diagnosis:' block, a per-dimension Fix column, and a 'Changes Applied' list (taxonomy: VAGUE_INTENT, MISSING_CONTEXT, UNDER_CONSTRAINED, MISSING_OUTPUT_SPEC, MISSING_ROLE...)."
fi

# C. Telemetry (non-blocking)
if [ "$(getj '.enforce.telemetry')" = "true" ]; then
  log="$root/.claude/.enhance-plugin-misses.log"
  [ -z "$card" ] && printf '%s\treviewer-card-miss (len=%s)\n' "$(jq -rn 'now|todate' 2>/dev/null || echo now)" "${#last_text}" >> "$log" 2>/dev/null
fi
exit 0
