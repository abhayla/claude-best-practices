#!/bin/bash
# prompt-enhance-reminder.sh — UserPromptSubmit hook
# Injects the *Enhanced:* indicator + Tier-1 + Grade pipeline reminder so the
# advisory rule cannot be skipped under context pressure.
#
# Trigger gate (added v2): the hook itself filters trivial prompts so the
# strengthening pipeline never runs on continuations or one-word replies.
# This moves the "skip for direct instructions" rule from the model layer
# (where it can be missed) to the deterministic layer.
#
# Skip conditions (no reminder injected):
#   1. Prompt length ≤ 15 characters (after trimming whitespace)
#   2. Prompt matches a known continuation phrase (yes / ok / thanks / next /
#      go ahead / proceed / continue / now do … / same for … / also …)
#
# Configuration:
#   Event: UserPromptSubmit
#   Matcher: (empty — matches all prompts)
#   Exit codes: always 0 (non-blocking)
#   Stdin: JSON payload with `prompt` field (parsed via jq)
#
# Settings.json entry:
#   {
#     "hooks": {
#       "UserPromptSubmit": [
#         {
#           "matcher": "",
#           "hooks": [
#             { "type": "command", "command": ".claude/hooks/prompt-enhance-reminder.sh", "timeout": 3 }
#           ]
#         }
#       ]
#     }
#   }

# Stderr is silenced so a missing jq never surfaces in the conversation.
exec 2>/dev/null

input=$(cat)

# If jq is unavailable, fall back to always-emit (safer than always-skip — the
# rule still applies, we just lose the trigger gate optimization).
if ! command -v jq >/dev/null; then
  emit_reminder() {
    echo "REMINDER: Start your response with *Enhanced: <what context was checked>* (under 15 words)."
    echo "Gather Tier 1 context (patterns, CLAUDE.md, git state) before responding."
    echo "For non-trivial prompts (ambiguous, multi-file, multi-step): run the Grade → Diagnose → Fix pipeline from /prompt-auto-enhance. Grade on 6 dimensions first — only fix dimensions scoring below 4. Skip for direct instructions, single-file changes, and questions."
  }
  emit_reminder
  exit 0
fi

prompt=$(printf '%s' "$input" | jq -r '.prompt // ""')

# Trim leading/trailing whitespace for length check
trimmed=$(printf '%s' "$prompt" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')

# Skip 1: empty or short prompts (≤15 chars trimmed)
if [ "${#trimmed}" -le 15 ]; then
  exit 0
fi

# Skip 2: known continuation phrases — case-insensitive, anchored to whole prompt
# (so "yes" matches but "yes, do this whole other thing" does not)
lower=$(printf '%s' "$trimmed" | tr '[:upper:]' '[:lower:]')
case "$lower" in
  yes|ok|okay|thanks|thank\ you|sure|got\ it|sounds\ good|proceed|continue|go|go\ ahead|go\ on|next|done|good|"yes please"|"yes, please")
    exit 0
    ;;
esac

# Skip 3: continuation prefixes — short prompts that begin with a continuation
# verb followed by very little ("now do X", "also Y", "same for Z") — these
# carry prior context, not new tasks. We require the total length to remain
# short (≤40 chars) so genuinely substantive continuations still get the gate.
if [ "${#trimmed}" -le 40 ]; then
  case "$lower" in
    "now do "*|"also "*|"same for "*|"and "*|"then "*|"next "*)
      exit 0
      ;;
  esac
fi

# Default: emit the full reminder
echo "REMINDER: Start your response with *Enhanced: <what context was checked>* (under 15 words)."
echo "Gather Tier 1 context (patterns, CLAUDE.md, git state) before responding."
echo "For non-trivial prompts (>15 chars, not a continuation): run the Grade → Diagnose → Fix pipeline from /prompt-auto-enhance. Show the step transcript and the final strengthened prompt before executing. Clarification Gate: ask one question at a time, no upper limit, until you have full confidence in user intent."
exit 0
