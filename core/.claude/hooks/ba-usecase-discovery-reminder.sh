#!/bin/bash
# ba-usecase-discovery-reminder.sh — UserPromptSubmit hook
# Fires the BA discipline so it cannot be skipped under context pressure: on a
# build / extend / work-on prompt for a product / feature / domain-logic surface,
# inject a *Sync-check:* OFFER to run full BA discovery / deep research FIRST.
#
# Behavior (decided 2026-06-18): the hook does NOT silently force BA and does NOT
# let it be silently skipped — it makes the model OFFER the choice to the user
# (recommended-on for domain/user-facing builds). The offer is a required
# *Sync-check:*, which the over-ask guard exempts.
#
# This is the SALIENCE layer (deterministic trigger, advisory injection). It does
# NOT enforce quality — completeness of the use-case discovery is enforced by the
# rule (ba-discovery-checklist.md) + an independent-review/eval, and the hard
# step/order gate is the pipeline's use-case-artifact contract. A reminder keeps
# the offer unmissable; it cannot judge whether the use-cases are complete.
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

# Build/extend/work-on intent → OFFER BA discovery. The keyword gate is the
# deterministic trigger; the model still owns judgment (and the user owns the choice).
# Fires when ANY holds:
#   A) a build/extend/work-on verb AND a product/feature/domain noun, OR
#   B) a domain/decision signal (finance, tax, pricing, a calculator/comparison tool), OR
#   C) an explicit "new <thing>" / "let's build" intent.
verb='\b(build|create|implement|develop|design|scaffold|make|add|extend|improve|set ?up|work on|put together|i need|i want|help me|can you (build|make|create|add|design))\b'
noun='\b(app|feature|page|tool|calculator|calc|screen|module|product|website|dashboard|api|flow|form|report|widget|integration|logic|model|system|comparison)\b'
domain='\b(tax|gst|loan|emi|invest|pricing|financ|interest|depreciat|resale|lifecycle|cost.?benefit|break.?even|decision tool|calculator)\b'
explicit='\b(new (app|feature|tool|product|calculator|screen|flow|module))\b|let.?s build'

if { printf '%s' "$trimmed" | grep -Eq "$verb" && printf '%s' "$trimmed" | grep -Eq "$noun"; } \
   || printf '%s' "$trimmed" | grep -Eq "$domain" \
   || printf '%s' "$trimmed" | grep -Eq "$explicit"; then
  cat <<'REMINDER'
BA-GATE (engineering-roles.md PM mandate) — this prompt looks like a product / feature /
domain build. Before questions, UI, or code, OFFER the user a choice (a required
*Sync-check:*, exempt from the over-ask guard). Do NOT silently skip it; do NOT silently force it:

  *Sync-check:* "This looks like a <domain/product> build. Want me to run full BA discovery /
  deep research first — actors, value-per-actor, the full economic LIFECYCLE, and the
  ACTORS x COMPONENTS x LIFECYCLE matrix (ba-discovery-checklist.md) — before we build?
  Recommended for anything domain- or user-facing; skip for a quick/throwaway build."

  - User opts IN  -> run full-space-first.md + ba-discovery-checklist.md, then G1 (mockup) before build.
  - User opts OUT -> proceed, state the narrowing as an **Assumption:**, keep the offer on record.
  - Pure-technical / refactor / bugfix with no domain or end-user surface -> no offer needed.
  When chosen, use-case discovery is step 1 — never backfilled after building. If you cannot
  state a concrete user benefit, challenge whether to build it at all.
REMINDER
fi
exit 0
