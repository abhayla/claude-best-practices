#!/usr/bin/env bash
# turn-origin.sh — shared turn-origin classifier (SSOT for the "fire-where-it-pays" predicate).
#
# Owner decision (2026-07-10, LOCKED): the FULL visible prompt-auto-enhance process (transcript +
# grade card + independent reviewer + final prompt) fires ONLY on HUMAN-typed prompts. Autonomous
# continuations, background task-notifications, scheduled wakeups, and skill-execution turns are
# MACHINE turns — they get at most a one-line banner, never the full ceremony. Live evidence that
# motivated this: .claude/.enhance-misses.log had 416 entries, largely autonomous turns being
# graded like human prompts.
#
# This file is the ONE definition of that predicate, sourced by BOTH the UserPromptSubmit reminder
# hook (prompt-enhance-reminder.sh) and the Stop guard (no-overask-guard.sh) so the two hooks can
# never drift on what counts as a machine turn.
#
#   classify_turn "<prompt text>"   ->  echoes "human" or "machine"
#
# Design guarantees pinned by the trap-test (scripts/tests/test_turn_origin_classifier.py):
#   * A genuine machine notification is caught: the machine marker sits at the START of the payload
#     (task-notification / [SYSTEM NOTIFICATION), or is a harness-only marker a human never types
#     (skill body, <command-name>), or the WHOLE payload is a <system-reminder> block.
#   * A human is NOT silenced: a human who merely QUOTES a task-notification INSIDE their prose
#     keeps human text before the marker -> the anchored check does not fire -> stays human.
#   * Documented judgment call: a human prompt that OPENS with pasted notification XML and then adds
#     a real request is classified MACHINE (marker at start). This is the cheap-error side — such a
#     turn still gets an answer + the governance tail; it just skips the enhance card. Biasing the
#     anchor toward "machine when it leads with the block" keeps the EXPENSIVE error (a real machine
#     turn slipping through and being graded like a human) from recurring.
#
# Unverified (2026-07-10): the exact UserPromptSubmit payload shape for a ScheduleWakeup continuation
# is not confirmed from a live fixture; the wakeup markers below are conservative literals a human is
# extremely unlikely to open a prompt with. Extend them here (the single SSOT) if a real payload differs.

classify_turn() {
  local prompt="$1"
  local trimmed lead
  # Trim leading whitespace/newlines for the anchored (starts-with) checks.
  trimmed="$(printf '%s' "$prompt" | sed -E 's/^[[:space:]]+//')"
  lead="$(printf '%s' "$trimmed" | tr '[:upper:]' '[:lower:]')"

  # 1. Task / system notification block AT THE START of the payload. Anchored (not "contains")
  #    so a human who quotes a notification inside their own prose is NOT misclassified.
  case "$trimmed" in
    '<task-notification'*|'<task_notification'*) echo machine; return 0 ;;
  esac
  case "$lead" in
    '[system notification'*|'[system-notification'*|'[task notification'*) echo machine; return 0 ;;
  esac

  # 2. Scheduled-wakeup continuation (ScheduleWakeup / /loop / schedule skill). Anchored + token.
  case "$trimmed" in
    '<schedule-wakeup'*|'<scheduled-wakeup'*|'<scheduled-task'*) echo machine; return 0 ;;
  esac
  case "$lead" in
    '[scheduled wakeup'*|'[schedule wakeup'*|'[wakeup]'*|'scheduled wakeup:'*|'schedulewakeup'*|'this is a scheduled wakeup'*|'this is an automated wakeup'*) echo machine; return 0 ;;
  esac

  # 3. Skill-execution turn — the harness injects the skill body (carrying this stable marker) or a
  #    <command-name> tag for a /command. Both are harness-generated; a human never types them.
  case "$prompt" in
    *'Base directory for this skill:'*|*'<command-name>'*) echo machine; return 0 ;;
  esac

  # 4. Hook-generated system-reminder-only turn: the WHOLE payload is a <system-reminder> block with
  #    no human request outside it. Detect: trimmed opens with <system-reminder AND (after trimming
  #    trailing whitespace) closes with </system-reminder>. A human who pastes a reminder then writes
  #    a request ends with THEIR text, not the closing tag -> stays human.
  case "$trimmed" in
    '<system-reminder'*)
      local rtrim
      rtrim="$(printf '%s' "$trimmed" | sed -E 's/[[:space:]]+$//')"
      case "$rtrim" in
        *'</system-reminder>') echo machine; return 0 ;;
      esac
      ;;
  esac

  echo human
}

# Direct-invocation entry point (for tests + ad-hoc use): `bash turn-origin.sh "<prompt>"` or pipe on
# stdin. When SOURCED, this block does not run — only the function is exported into the caller.
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
  if [ "$#" -ge 1 ]; then
    classify_turn "$1"
  else
    classify_turn "$(cat)"
  fi
fi
