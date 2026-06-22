#!/usr/bin/env bash
# prompt-enhance-reminder.sh — UserPromptSubmit hook (PLUGIN version)
#
# Settings-driven prompt-auto-enhancement trigger + verbosity injector. Reads the
# effective enhance-settings (project override else plugin default) FRESH every turn,
# so edits auto-adjust with no reinstall. Honors the master switch, the per-criterion
# trigger gates, the run_mode, and the per-component verbosity toggles.
#
# SCOPE: this plugin ships ONLY prompt-auto-enhance's own behavior. It does NOT emit
# the hub-wide governance tail (decide-don't-ask / plan-before-coding / role routing /
# narrate-and-stop) — that is hub engineering governance, intentionally excluded.
#
# Exit codes: always 0 (non-blocking). Requires jq; degrades to always-emit if absent.
exec 2>/dev/null

plugin_root="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
root="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
override="$root/.claude/enhance-settings.json"
settings="$plugin_root/enhance-settings.default.json"
[ -f "$override" ] && settings="$override"
# Explicit path override (highest precedence) — for power users + deterministic tests.
[ -n "$ENHANCE_SETTINGS_FILE" ] && [ -f "$ENHANCE_SETTINGS_FILE" ] && settings="$ENHANCE_SETTINGS_FILE"

input=$(cat)

# jq missing → emit the full reminder so the pipeline is never silently skipped.
emit_full() {
  echo "REMINDER: Start your response with *Enhanced: <what context was checked>* (under 15 words)."
  echo "Run the Grade -> Diagnose -> Fix prompt-auto-enhance pipeline and render the FULL process UP FRONT: (1) *Enhanced:* banner; (2) pipeline transcript; (3) before->after grade card WITH the independent-reviewer 'Reviewer-after' per-dimension column; (4) Original->Final strengthened prompt (Final opens with 'Act as ...' when Role & Framing < 7); (5) 'Role: <name> — <why>'. Clarification gate: ask one question at a time until intent is clear."
}
if ! command -v jq >/dev/null; then emit_full; exit 0; fi

getj() { jq -r "$1 // empty" "$settings" 2>/dev/null; }

# ── Master switch ── (raw read: jq's `// empty` would collapse boolean false to empty)
[ "$(jq -r '.enabled' "$settings" 2>/dev/null)" = "false" ] && exit 0

prompt=$(printf '%s' "$input" | jq -r '.prompt // ""')
trimmed=$(printf '%s' "$prompt" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')
lower=$(printf '%s' "$trimmed" | tr '[:upper:]' '[:lower:]' | tr -s '[:space:]' ' ')

write_override() {  # $1=jq filter applied to current effective settings → override file
  mkdir -p "$root/.claude" 2>/dev/null
  jq "$1" "$settings" > "$override.tmp" 2>/dev/null && mv "$override.tmp" "$override" 2>/dev/null
}

# ── Inline set-commands (run BEFORE skip filters so short control phrases register) ──
case "$lower" in
  "enhance off"|"enhance disable")
    write_override '.enabled = false'
    echo "prompt-auto-enhance: master switch OFF (override written). Re-enable with 'enhance on'."; exit 0 ;;
  "enhance on"|"enhance enable")
    write_override '.enabled = true'
    echo "prompt-auto-enhance: master switch ON."; exit 0 ;;
  "enhance mode auto"|"enhance mode ask"|"enhance mode silent"|"enhance mode off")
    m="${lower##* }"; write_override ".run_mode = \"$m\""
    echo "prompt-auto-enhance: run_mode = $m."; exit 0 ;;
esac
# Bare 'enhance' → one-shot full render regardless of stored mode.
case "$lower" in
  enhance|/enhance|"enhance this"|"enhance it")
    emit_full
    echo "ONE-SHOT: re-run the PREVIOUS prompt through the full pipeline now, then answer it."; exit 0 ;;
esac

# ── run_mode gate (auto | ask | silent | off) ──
mode="$(getj '.run_mode')"; case "$mode" in auto|ask|silent|off) : ;; *) mode="auto" ;; esac
case "$mode" in
  off)
    echo "prompt-auto-enhance run_mode=off: pipeline disabled this turn; answer directly."; exit 0 ;;
  ask)
    echo "prompt-auto-enhance run_mode=ask: do NOT auto-render the process. Answer directly, then append exactly one line: *Enhance available — reply 'enhance' to run the full pipeline on this prompt.*"; exit 0 ;;
  silent)
    echo "prompt-auto-enhance run_mode=silent: strengthen the prompt INTERNALLY and act on the improved version, but render NONE of the process (no banner/card/transcript). Output only the answer."; exit 0 ;;
esac

# ── Trigger gates (each honored only if its .on is true) ──
# Length gate
if [ "$(getj '.triggers.length_gate.on')" = "true" ]; then
  unit="$(getj '.triggers.length_gate.unit')"; min="$(getj '.triggers.length_gate.min')"
  case "$min" in ''|*[!0-9]*) min=0 ;; esac
  if [ "$unit" = "words" ]; then
    n=$(printf '%s' "$trimmed" | wc -w | tr -d ' ')
  else
    n=${#trimmed}
  fi
  [ "$n" -lt "$min" ] && exit 0
fi
# Continuation phrases (exact match)
if [ "$(getj '.triggers.continuation_phrases.on')" = "true" ]; then
  if jq -e --arg p "$lower" '.triggers.continuation_phrases.list | index($p)' "$settings" >/dev/null 2>&1; then
    exit 0
  fi
fi
# Continuation prefixes (short + starts-with)
if [ "$(getj '.triggers.continuation_prefixes.on')" = "true" ]; then
  maxlen="$(getj '.triggers.continuation_prefixes.max_len')"; case "$maxlen" in ''|*[!0-9]*) maxlen=40 ;; esac
  if [ "${#trimmed}" -le "$maxlen" ]; then
    while IFS= read -r pre; do
      [ -z "$pre" ] && continue
      case "$lower" in "$pre"*) exit 0 ;; esac
    done < <(jq -r '.triggers.continuation_prefixes.list[]?' "$settings" 2>/dev/null)
  fi
fi

# ── Emit the enhance reminder, listing only the show-components that are ON ──
parts=""
add() { parts="$parts$1"; }
[ "$(getj '.show.banner')" = "true" ]          && add "(1) *Enhanced:* banner; "
[ "$(getj '.show.transcript')" = "true" ]      && add "(2) pipeline transcript; "
[ "$(getj '.show.diagnosis')" = "true" ]       && add "(3) Diagnosis block; "
[ "$(getj '.show.grade_card')" = "true" ]      && add "(4) before->after grade card; "
[ "$(getj '.show.reviewer_column')" = "true" ] && [ "$(jq -r '.run.independent_reviewer' "$settings" 2>/dev/null)" != "false" ] && add "(4b) independent-reviewer 'Reviewer-after' per-dimension column; "
[ "$(getj '.show.changes_applied')" = "true" ] && add "(5) Changes Applied list; "
[ "$(getj '.show.final_prompt')" = "true" ]    && add "(6) Original->Final strengthened prompt; "
[ "$(getj '.show.role_line')" = "true" ]       && add "(7) 'Role: <name> — <why>'; "

echo "REMINDER: Run the prompt-auto-enhance Grade -> Diagnose -> Fix pipeline and render UP FRONT, in order: ${parts}"
[ "$(getj '.clarify.on')" = "true" ] && echo "Clarification gate ON: if intent confidence < threshold, ask ONE question at a time (open with *Sync-check:*) until clear, before strengthening."
exit 0
