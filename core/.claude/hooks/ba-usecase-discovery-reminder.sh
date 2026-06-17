#!/bin/bash
# ba-usecase-discovery-reminder.sh — UserPromptSubmit hook
# Fires the BA discipline so it cannot be skipped under context pressure: on a
# build/feature-shaped prompt, inject the load-bearing ORDER from the PM mandate
# (engineering-roles.md) — discover the use-case space FIRST, then questions,
# then UI, then build.
#
# This is the SALIENCE layer (deterministic trigger, advisory injection). It does
# NOT enforce quality — completeness of the use-case discovery is enforced by the
# rule + an independent-review/eval (L4), and the hard step/order gate is the
# pipeline's use-case-artifact contract (L3). A reminder keeps step 1 unmissable;
# it cannot judge whether the use-cases are complete.
#
# Configuration:
#   Event: UserPromptSubmit   Matcher: "" (all prompts)   Exit: always 0 (non-blocking)
#   Stdin: JSON payload with a `prompt` field (parsed via jq).

exec 2>/dev/null
input=$(cat)
prompt=$(printf '%s' "$input" | jq -r '.prompt // empty' 2>/dev/null)
[ -z "$prompt" ] && exit 0

# Trim; skip trivial / continuation prompts (the build intent isn't here).
trimmed=$(printf '%s' "$prompt" | tr '[:upper:]' '[:lower:]' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
[ "${#trimmed}" -le 15 ] && exit 0
case "$trimmed" in
  yes|ok|okay|sure|thanks|next|go\ ahead|proceed|continue|done|same*|also*|now\ *) exit 0 ;;
esac

# Build/feature intent → inject the BA-order reminder. (Keyword gate is the
# deterministic trigger; the model still owns judgment.)
if printf '%s' "$trimmed" | grep -Eq '\b(build|create|implement|develop|design|scaffold|make)\b.*\b(app|feature|page|tool|calculator|screen|module|product|website|dashboard|api)\b|\b(new (app|feature|tool|product|calculator))\b|let.?s build'; then
  cat <<'REMINDER'
BA ORDER REMINDER (engineering-roles.md PM mandate) — before any questions or UI:
  1. DISCOVER the full use-case space FIRST — domain perspective AND user/personal
     perspective; do a WEB SEARCH to enumerate all possible use cases when the
     domain isn't fully known. State the VALUE PROPOSITION (who is the primary
     user + why they'd use it). Map ALL meaningful combinations, not the literal spec.
  2. THEN clarifying questions — one at a time, each with a recommended option +
     why alternatives are weaker, sequenced on prior answers.
  3. THEN design the UI (show a sample, get G1 approval).
  4. THEN build.
  Use-case discovery is step 1 — never backfilled after building. If you cannot
  state a concrete benefit, challenge whether to build it at all.
REMINDER
fi
exit 0
