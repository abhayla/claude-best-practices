#!/usr/bin/env bash
# enhance-process-guard.sh — Stop hook (PLUGIN version)
#
# Enforces ONLY that the prompt-improver's full process was shown on a substantive turn —
# its own self-check, governed by `make_sure_steps_were_shown` (strict|relaxed|off):
#   * strict  -> block (stop and redo) when the score-table/review or fix-details are missing
#   * relaxed -> don't block; just keep a quiet log
#   * off     -> no check
# DELIBERATELY NOT PORTED (hub-wide governance, excluded by design): decide-don't-ask,
# narrate-and-stop, plan-before-coding, role routing.
#
# Settings read FRESH each turn (precedence: env > project > global ~/.claude > default). Requires jq.
exec 2>/dev/null
input=$(cat)
command -v jq >/dev/null || exit 0

plugin_root="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"

# ── Coexistence guard: stand down where a SUPERSET enforcer already runs (hub dedup) ──
# Some hosts (the hub itself) wire an operational Stop hook, .claude/hooks/no-overask-guard.sh,
# that enforces THIS exact card/Overall block PLUS over-ask + narrate-and-stop governance. Where
# that hook is present AND wired into the repo's Stop hooks, this plugin's card block is fully
# redundant and would double-fire — two `decision:block` stops and two log lines per single miss
# (the enhance-block-miss double-count). Stand down there. Downstream projects that provisioned
# the plugin but have NO no-overask-guard.sh do not match, so their enforcement is unchanged (no
# regression). Detection: the hook file exists AND settings.json references it in a Stop entry.
if [ -f "$root/.claude/hooks/no-overask-guard.sh" ] && \
   grep -q "no-overask-guard.sh" "$root/.claude/settings.json" 2>/dev/null; then
  exit 0
fi

settings="$plugin_root/enhance-settings.default.json"
[ -f "$HOME/.claude/enhance-settings.json" ] && settings="$HOME/.claude/enhance-settings.json"
[ -f "$root/.claude/enhance-settings.json" ] && settings="$root/.claude/enhance-settings.json"
[ -n "$ENHANCE_SETTINGS_FILE" ] && [ -f "$ENHANCE_SETTINGS_FILE" ] && settings="$ENHANCE_SETTINGS_FILE"
getj() { jq -r "$1 // empty" "$settings" 2>/dev/null; }

# ── Shared turn-origin classifier (fire-where-it-pays) — ships with the plugin; fail-open. ──
[ -f "$plugin_root/hooks/turn-origin.sh" ] && . "$plugin_root/hooks/turn-origin.sh"
command -v classify_turn >/dev/null 2>&1 || classify_turn() { echo human; }

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

# Final-user-SUBMISSION extraction (issue #331) — shared by the slash exemption and the
# machine-origin scope below. The harness writes a slash invocation as TWO consecutive user
# entries (the <command-name> marker entry + the fully-expanded marker-less BODY entry), so
# inspecting only the last entry (`tail -1`) missed the exemption and false-blocked /command
# turns (live repro: session 889094c3 2026-07-12). A SUBMISSION = the maximal run of
# consecutive real-user entries; origin classification walks BACK past "Stop hook feedback:"
# submissions so a blocked slash/machine turn keeps its exemption through the block chain.
last_sub=$(jq -s -r '
  [ .[]
    | if .type=="user" and ((.message.content|type)=="string" or ([.message.content[]?|.type]|index("tool_result")|not))
      then {k:"U", t:(if (.message.content|type)=="string" then .message.content else ([.message.content[]?|select(.type=="text")|.text]|join(" ")) end)}
      elif .type=="assistant" then {k:"A", t:""}
      else empty end ]
  | reduce .[] as $e ({runs:[], prev:""};
      if $e.k=="A" then {runs:.runs, prev:"A"}
      elif .prev=="U" then {runs:(.runs[0:-1] + [(.runs[-1] + "\n" + $e.t)]), prev:"U"}
      else {runs:(.runs + [$e.t]), prev:"U"} end)
  | .runs
  | ((map(select(startswith("Stop hook feedback:") | not)) | last) // (last // ""))
' "$tp" 2>/dev/null)

# Slash-command exemption — mirror the UserPromptSubmit hook: when enhance_slash_commands is not
# true (default false), a /command (user-made OR Anthropic-provided) is run as-is and is NEVER
# enhanced. This guard only enforces the enhance process, so a slash-command turn exits entirely.
if [ "$(getj '.enhance_slash_commands')" != "true" ]; then
  case "$last_sub" in
    *'<command-name>'*) exit 0 ;;
    # Skill-execution turn: the harness-injected skill body carries this stable marker.
    # Skills are enhance-exempt, so exit even when the banner fell into the pre-split segment.
    *'Base directory for this skill:'*) exit 0 ;;
  esac
  # Raw-client shape: the submission text IS the literal "/command args" prompt; tolerate
  # leading whitespace/newlines (H4, issue #279) — matched on decoded text, not JSON escapes.
  case "$(printf '%s' "$last_sub" | sed -E 's/^[[:space:]]+//' | head -c 1)" in
    /) exit 0 ;;
  esac
fi

# ── full_process_scope: fire-where-it-pays — exempt MACHINE-origin turns from the process-guard
# block (mirrors the reminder hook). "everywhere" keeps enforcement on every substantive turn. ──
fps="$(getj '.full_process_scope')"; [ -z "$fps" ] && fps="human-prompts"
if [ "$fps" != "everywhere" ]; then
  [ "$(classify_turn "$last_sub")" = "machine" ] && exit 0
fi

full=$(printf '%s' "$last_text" | tr '[:upper:]' '[:lower:]' | sed -e '/./,$!d')

subchars="$(getj '.when_to_enhance.min_response_size_to_check_characters')"; case "$subchars" in ''|*[!0-9]*) subchars=300 ;; esac
[ "${#last_text}" -lt "$subchars" ] && exit 0

trivial=""
printf '%s' "$full" | head -1 | grep -qE "ran (your )?input as-is|ran as-is|no change —|no enhancement|already strong" && [ "${#last_text}" -lt 600 ] && trivial="1"
[ -n "$trivial" ] && exit 0

# GRADE-A LITE PATH (issue #290, owner-approved ceremony downgrade): mirrors the hub guard's
# gradea detector byte-for-byte (H6 consistency) — a turn that explicitly declares
# Grade-A/no-strengthening in its first 3 lines is exempt from the full-card block below even
# when make_sure_steps_were_shown=strict; it only owes the banner + a one-line declaration.
gradea=""
printf '%s' "$full" | head -3 | grep -qE "grade a[^a-z]|grade: a|no strengthening needed|no change —|ran (your )?input as-is|ran as-is|0 fix|no fix|prompt already strong \(grade [0-9]" && gradea="1"

card=""
# H1 (issue #279): also credit the enhance card's HEADER ROW — a markdown row that pairs
# "reviewer" with a before/after/self column (e.g. "| Dimension | Before | After | Blind
# reviewer |") — even when it uses none of the fixed prose tokens below. The before/after/self
# co-requirement keeps an UNRELATED table row that merely contains "reviewer" from counting.
printf '%s' "$full" | grep -qE "^[[:space:]]*\|.*(before|after|self).*reviewer.*\||reviewer-after|reviewer col|blind re-?grade|independent[ -]reviewer" && card="1"
# The card MUST close with an Overall/total row (weighted sum + letter-grade transition); a
# per-dimension table with no total is an incomplete card (regression guard for the dropped total row).
overall=""
printf '%s' "$full" | grep -qE "overall|[a-f] *(→|->) *[a-f]|weighted total" && overall="1"
substance=""
printf '%s' "$full" | grep -qE "diagnosis:|changes applied|missing_role|missing_context|missing_output|vague_intent|under_constrained|missing_structure|missing_constraint|grade: a|grade a[^a-z]|0 fix|no fix|zero fix" && substance="1"

block() { jq -nc --arg r "$1" '{decision:"block", reason:$r}'; exit 0; }

# Self-check strictness. strict -> block; relaxed/off -> don't block.
strictness="$(getj '.make_sure_steps_were_shown')"; [ -z "$strictness" ] && strictness="strict"
enforce="off"; [ "$strictness" = "strict" ] && enforce="block"
# Issue #290: "only_for_weak_prompts" is now the DEFAULT sampled mode — it stays enforced
# (weak prompts still owe the full card), and the per-turn `gradea` gate below is what exempts
# an explicitly-declared Grade-A/no-strengthening turn, not a blanket disable. Only
# "scale_to_prompt_quality" (a free-form adaptive scale with no fixed declaration format the
# guard can verify) still disables enforcement wholesale.
case "$(getj '.display.how_much_to_show')" in scale_to_prompt_quality) enforce="off" ;; esac

# A. require the score-table + second-opinion review (unless that component is off).
mode_card="$enforce"
[ "$(jq -r '.display.show.second_opinion_review' "$settings" 2>/dev/null)" = "false" ] && mode_card="off"
if [ "$mode_card" = "block" ] && { [ -z "$card" ] || [ -z "$overall" ]; } && [ -z "$gradea" ]; then
  block "STOP BLOCKED (prompt-auto-enhance: full process not shown). This substantive turn is missing the second-opinion 'Reviewer-after' score table and/or its closing 'Overall' total row. Render the FULL process UP FRONT: *Enhanced summary + step log + score table WITH the Reviewer-after column AND an Overall row (weighted total per column + letter-grade transition, e.g. F -> B) + Original->Improved prompt + Role line. If the prompt was trivial, make the first line '*Enhanced: no change — ran your input as-is*'. If this was a STRONG/Grade-A prompt needing no strengthening (#290 sampled ceremony), the full table is OPTIONAL — but declare it in the first 3 lines, e.g. '*Enhanced: … — Grade A, no strengthening needed*'."
fi

# B. require fix-details (gated on the diagnosis/score-table being expected).
# A declared Grade-A / strong-banner turn ($gradea) owes NO diagnosis (nothing was strengthened),
# so it is exempt from this fix-details block too — mirrors section A above (which already skips on
# $gradea) and the hub guard, whose substance block only fires when a card is actually present.
want_sub=""
{ [ "$(getj '.display.show.score_table')" = "true" ] || [ "$(getj '.display.show.whats_wrong')" = "true" ]; } && want_sub="1"
if [ -n "$want_sub" ] && [ -z "$substance" ] && [ -z "$gradea" ] && [ "$enforce" = "block" ]; then
  block "STOP BLOCKED (prompt-auto-enhance: fix-details missing). The score table shows numbers but not the diagnose->fix detail — add a 'Diagnosis:' block, a per-dimension Fix column, and a 'Changes Applied' list (taxonomy: VAGUE_INTENT, MISSING_CONTEXT, UNDER_CONSTRAINED, MISSING_OUTPUT_SPEC, MISSING_ROLE...)."
fi

# C. Quiet log (non-blocking)
if [ "$(getj '.keep_a_quiet_log')" = "true" ]; then
  log="$root/.claude/.enhance-plugin-misses.log"
  [ -z "$card" ] && printf '%s\treview-table-miss (len=%s)\n' "$(jq -rn 'now|todate' 2>/dev/null || echo now)" "${#last_text}" >> "$log" 2>/dev/null
  [ -n "$card" ] && [ -z "$overall" ] && printf '%s\toverall-total-row-miss (len=%s)\n' "$(jq -rn 'now|todate' 2>/dev/null || echo now)" "${#last_text}" >> "$log" 2>/dev/null
fi
exit 0
