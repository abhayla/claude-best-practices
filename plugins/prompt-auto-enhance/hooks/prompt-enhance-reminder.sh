#!/usr/bin/env bash
# prompt-enhance-reminder.sh — UserPromptSubmit hook (PLUGIN version)
#
# Settings-driven prompt-improver trigger + display injector. Reads the effective
# enhance-settings FRESH every turn (precedence: env > project > global ~/.claude > default),
# so edits auto-adjust with no reinstall. Honors the master switch, when_to_run, the skip
# rules (incl. the deterministic slash-command skip), the display master + condition +
# per-part checkboxes, the model-judged directives, and after_improving (review-first).
#
# SCOPE: ships ONLY prompt-auto-enhance's own behavior — NOT the hub-wide governance tail.
# Always exits 0 (non-blocking). Requires jq; degrades to always-emit if absent.
exec 2>/dev/null

plugin_root="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
global_cfg="$HOME/.claude/enhance-settings.json"
project_cfg="$root/.claude/enhance-settings.json"
settings="$plugin_root/enhance-settings.default.json"
[ -f "$global_cfg" ] && settings="$global_cfg"
[ -f "$project_cfg" ] && settings="$project_cfg"
[ -n "$ENHANCE_SETTINGS_FILE" ] && [ -f "$ENHANCE_SETTINGS_FILE" ] && settings="$ENHANCE_SETTINGS_FILE"

input=$(cat)

emit_full() {
  echo "REMINDER: Start your response with *Enhanced: <what context was checked>* (under 15 words)."
  echo "Run the Grade -> Diagnose -> Fix prompt-auto-enhance pipeline and render the FULL process UP FRONT: (1) *Enhanced:* summary line; (2) step-by-step log; (3) before->after score table WITH the second-opinion 'Reviewer-after' per-dimension column; (4) Original->Improved prompt (Improved opens with 'Act as ...' when role/framing < threshold); (5) 'Role: <name> — <why>'. Clarification gate: ask one question at a time until intent is clear."
}
if ! command -v jq >/dev/null; then emit_full; exit 0; fi

getj() { jq -r "$1 // empty" "$settings" 2>/dev/null; }

# ── Master switch ── (raw read: jq's `// empty` would collapse boolean false to empty)
[ "$(jq -r '.enabled' "$settings" 2>/dev/null)" = "false" ] && exit 0

prompt=$(printf '%s' "$input" | jq -r '.prompt // ""')
trimmed=$(printf '%s' "$prompt" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')
lower=$(printf '%s' "$trimmed" | tr '[:upper:]' '[:lower:]' | tr -s '[:space:]' ' ')

write_override() {
  mkdir -p "$HOME/.claude" 2>/dev/null
  jq "$1" "$settings" > "$global_cfg.tmp" 2>/dev/null && mv "$global_cfg.tmp" "$global_cfg" 2>/dev/null
}

# ── Inline set-commands (run BEFORE skip filters so short control phrases register) ──
case "$lower" in
  "enhance off"|"enhance disable") write_override '.enabled = false'; echo "prompt-auto-enhance: turned OFF. Turn it back on with 'enhance on'."; exit 0 ;;
  "enhance on"|"enhance enable")   write_override '.enabled = true';  echo "prompt-auto-enhance: turned ON."; exit 0 ;;
  "enhance mode auto"|"enhance mode automatic") write_override '.when_to_run = "automatic"'; echo "prompt-auto-enhance: when_to_run = automatic."; exit 0 ;;
  "enhance mode ask"|"enhance mode ask_first")  write_override '.when_to_run = "ask_first"';  echo "prompt-auto-enhance: when_to_run = ask_first."; exit 0 ;;
  "enhance mode off") write_override '.when_to_run = "off"'; echo "prompt-auto-enhance: when_to_run = off."; exit 0 ;;
esac
case "$lower" in
  enhance|/enhance|"enhance this"|"enhance it")
    emit_full
    echo "ONE-SHOT: re-run the PREVIOUS prompt through the full pipeline now, then answer it."; exit 0 ;;
esac

# ── when_to_run (automatic | ask_first | off) ──
mode="$(getj '.when_to_run')"; case "$mode" in automatic|ask_first|off) : ;; *) mode="automatic" ;; esac
case "$mode" in
  off) echo "prompt-auto-enhance when_to_run=off: improver disabled this turn; answer directly."; exit 0 ;;
  ask_first) echo "prompt-auto-enhance when_to_run=ask_first: do NOT auto-render the process. Answer directly, then append exactly one line: *Enhance available — reply 'enhance' to improve this prompt.*"; exit 0 ;;
esac

# ── Display master OFF == silent ──
if [ "$(jq -r '.display.show_the_process' "$settings" 2>/dev/null)" = "false" ]; then
  echo "prompt-auto-enhance display.show_the_process=false: improve the prompt INTERNALLY and act on the improved version, but render NONE of the process. Output only the answer."; exit 0
fi

# ── Skip slash-command / saved custom prompts (deterministic) ──
# enhance_slash_commands=false → a prompt that is a /command (user-made OR Anthropic-provided)
# is run as-is, any size. VERIFIED 2026-06-22 (empirically, via this hub's prompt-logger history):
# UserPromptSubmit fires for slash commands and .prompt holds the RAW "/command args" text
# (e.g. /init, /grill-me, /save-session, /loop all logged raw). Pure client-side built-ins like
# /clear /exit are intercepted upstream and never reach this hook — correct, they aren't prompts.
if [ "$(jq -r '.enhance_slash_commands' "$settings" 2>/dev/null)" = "false" ]; then
  case "$trimmed" in /*) exit 0 ;; esac
fi

# ── Skip rules (each honored only if its .enabled is true) ──
if [ "$(getj '.when_to_enhance.skip_short_prompts.enabled')" = "true" ]; then
  unit="$(getj '.when_to_enhance.skip_short_prompts.count_by')"; min="$(getj '.when_to_enhance.skip_short_prompts.minimum')"
  case "$min" in ''|*[!0-9]*) min=0 ;; esac
  if [ "$unit" = "words" ]; then n=$(printf '%s' "$trimmed" | wc -w | tr -d ' '); else n=${#trimmed}; fi
  [ "$n" -lt "$min" ] && exit 0
fi
if [ "$(getj '.when_to_enhance.skip_these_phrases.enabled')" = "true" ]; then
  jq -e --arg p "$lower" '.when_to_enhance.skip_these_phrases.list | index($p)' "$settings" >/dev/null 2>&1 && exit 0
fi
if [ "$(getj '.when_to_enhance.skip_phrases_starting_with.enabled')" = "true" ]; then
  maxlen="$(getj '.when_to_enhance.skip_phrases_starting_with.only_if_under_characters')"; case "$maxlen" in ''|*[!0-9]*) maxlen=40 ;; esac
  if [ "${#trimmed}" -le "$maxlen" ]; then
    while IFS= read -r pre; do [ -z "$pre" ] && continue; case "$lower" in "$pre"*) exit 0 ;; esac; done < <(jq -r '.when_to_enhance.skip_phrases_starting_with.list[]?' "$settings" 2>/dev/null)
  fi
fi

# ── Display condition (adaptive verbosity) ──
howmuch="$(getj '.display.how_much_to_show')"; [ -z "$howmuch" ] && howmuch="every_time"
wmax="$(getj '.display.weak_prompt_score_below')"; case "$wmax" in ''|*[!0-9.]*) wmax=7 ;; esac
case "$howmuch" in
  only_for_weak_prompts)
    echo "DISPLAY CONDITION (only_for_weak_prompts): grade the prompt FIRST. Only if its weighted grade is BELOW ${wmax}, render the full process. If it grades ${wmax}+ (strong), emit ONLY '*Enhanced: prompt already strong (grade N) — ran as-is*' and proceed." ;;
  scale_to_prompt_quality)
    echo "DISPLAY CONDITION (scale_to_prompt_quality): grade FIRST, then scale the display: grade >=8 (great) -> one-line *Enhanced:* note only; grade ${wmax}-8 (okay) -> COMPACT (1-2 key fixes); grade below ${wmax} (weak) -> the FULL process below." ;;
esac

# ── Emit the reminder, listing only the display.show parts that are ON ──
parts=""
add() { parts="$parts$1"; }
[ "$(getj '.display.show.summary_line')" = "true" ]          && add "(1) *Enhanced:* summary line; "
[ "$(getj '.display.show.step_by_step_log')" = "true" ]      && add "(2) step-by-step pipeline log; "
[ "$(getj '.display.show.whats_wrong')" = "true" ]           && add "(3) what's-wrong Diagnosis block; "
[ "$(getj '.display.show.score_table')" = "true" ]           && add "(4) before->after score table (grade card); "
[ "$(getj '.display.show.second_opinion_review')" = "true" ] && add "(4b) second-opinion independent-reviewer 'Reviewer-after' per-dimension column (fire a context-blind re-grade); "
[ "$(getj '.display.show.list_of_fixes')" = "true" ]         && add "(5) list of fixes (Changes Applied); "
[ "$(getj '.display.show.improved_prompt')" = "true" ]       && add "(6) Original->Improved prompt; "
[ "$(getj '.display.show.assigned_role')" = "true" ]         && add "(7) 'Role: <name> — <why>'; "
echo "REMINDER: Run the prompt-auto-enhance Grade -> Diagnose -> Fix pipeline and render UP FRONT, in order: ${parts}"

# ── Model-judged directives (each gated by its setting) ──
[ "$(getj '.when_to_enhance.skip_if_just_a_question')" = "true" ]                && echo "SKIP-IF-QUESTION: if this prompt is purely a factual question (not a request to DO something), skip strengthening and just answer it."
[ "$(getj '.when_to_enhance.skip_tip_for_simple_tasks')" = "true" ]             && echo "SKIP-TIP: for a direct/mechanical/bug-fix/lookup/documentation prompt, do not append the optional 'better phrasing' skill hint."
[ "$(getj '.when_to_enhance.also_check_when_short_prompt_makes_big_work')" = "true" ] && echo "BIG-WORK: even if this prompt is short, if it triggers substantial work, still apply the full process (judge by the output's blast radius, not the prompt's length)."
[ "$(getj '.display.show_step_log_only_for_multipart')" = "true" ]              && echo "MULTIPART-LOG: show the step-by-step log ONLY if the request has 3+ distinct parts; for a single-intent request, omit the log."
[ "$(getj '.improving.always_add_a_role')" = "true" ]                           && echo "ALWAYS-ROLE: always add an 'Act as ...' role to the improved prompt, regardless of its score."
[ "$(getj '.ask_clarifying_questions.enabled')" = "true" ]                       && echo "CLARIFY (via $(getj '.ask_clarifying_questions.method' || echo grill-me)): if intent confidence < threshold, ask ONE question at a time (open with *Sync-check:*) until clear, before improving."

# ── after_improving (run now vs. wait for user review) ──
after="$(getj '.after_improving')"; [ -z "$after" ] && after="run_immediately"
if [ "$after" = "let_me_review_first" ]; then
  echo "AFTER IMPROVING (let_me_review_first): render the IMPROVED prompt and STOP. Do NOT execute it. Wait for the user to approve, edit, or trigger it before doing the work."
fi
exit 0
