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

# Reset the keep-going auto-continue loop-guard for this new user turn. The Stop hook
# (no-overask-guard.sh) increments + caps this; resetting per user prompt bounds it.
printf '0' > "$(git rev-parse --show-toplevel 2>/dev/null)/.claude/.keepgoing-count" 2>/dev/null
# Same for the reviewer-grade-card enforcement loop-guard (no-overask-guard.sh).
printf '0' > "$(git rev-parse --show-toplevel 2>/dev/null)/.claude/.reviewcard-count" 2>/dev/null
# Same for the diagnose→fix substance enforcement loop-guard (no-overask-guard.sh).
printf '0' > "$(git rev-parse --show-toplevel 2>/dev/null)/.claude/.diagnosis-count" 2>/dev/null

# If jq is unavailable, fall back to always-emit (safer than always-skip — the
# rule still applies, we just lose the trigger gate optimization).
if ! command -v jq >/dev/null; then
  emit_reminder() {
    echo "REMINDER: Start your response with *Enhanced: <what context was checked>* (under 15 words)."
    echo "Gather Tier 1 context (patterns, CLAUDE.md, git state) before responding."
    echo "For non-trivial prompts: render the FULL enhance process UP FRONT (before any tool call) — banner + transcript + before→after grade card WITH the reviewer's 'Reviewer-after' column + Original→Final prompt + Role line — then the governance tail (gate, decision-authority, git). Trivial/continuation → only '*Enhanced: no change — ran your input as-is*'."
    echo "PLAN BEFORE CODING: for any non-trivial change (3+ files/steps, new feature, refactor, schema, or domain-critical logic) produce a visible plan — plan mode / autonomous contract / inline plan block — BEFORE the first code edit (.claude/rules/plan-before-coding.md). Skip only trivial/mechanical edits."
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
echo "For non-trivial prompts (>15 chars, not a continuation): run the Grade → Diagnose → Fix pipeline from /prompt-auto-enhance. Clarification Gate: ask one question at a time, no upper limit, until you have full confidence in user intent."
echo "RENDER THE FULL ENHANCE PROCESS UP FRONT — as the FIRST thing in your reply, BEFORE any tool call — not a one-liner and not a compact block. Required parts, in order: (1) *Enhanced:* banner; (2) pipeline transcript (per-step); (3) a before→after grade card WITH the independent reviewer's per-dimension 'Reviewer-after' column; (4) Original→Final strengthened prompt, fenced (Final opens with 'Act as …' when Role&Framing < 7); (5) 'Role: <name> — <why>'. The compact 'What changed / Final prompt' block is a FALLBACK ONLY when the user explicitly asked to reduce verbosity — do NOT default to it. On a genuinely trivial/continuation prompt render ONLY '*Enhanced: no change — ran your input as-is*' as the first line. Deferring the process until after tool work, or omitting the reviewer card, is a defect the Stop + PreToolUse hooks BLOCK. SSOT: prompt-auto-enhance-rule.md 'MANDATORY OUTPUT'."
echo "Then the governance tail: state Role: <name> — <why> (engineering-roles.md); gate intent (grill-me/grill-with-docs if a consequential fork is <~95% clear); execute under decision-authority (decide reversible, escalate irreversible in one line); and if the turn produced changes, do git via git-manager-agent + the secret-scan hook."
echo "PLAN BEFORE CODING: for any non-trivial change (3+ files/steps, new feature, refactor, schema, or domain-critical logic) produce a visible plan — plan mode / autonomous contract / inline plan block — BEFORE the first code edit (.claude/rules/plan-before-coding.md). Skip only trivial/mechanical edits (typo, one-line fix, rename)."
echo "DECIDE, DON'T ASK (hard rule): do NOT end your response with an offer/question (\"want me to…\", \"should I…\", \"let me know…\", \"say the word\", \"or leave it?\") on reversible/internal work — just DO it (file the issue, commit, take the next queued item) and report. ONLY a genuinely irreversible/outward/strategic action (deploy, spend, DNS cutover, destructive git, a true product fork) earns a question. A Stop hook (no-overask-guard.sh) flags violations."
echo "GRILL WHEN UNSURE OF INTENT (equal-weight balance to DECIDE-DON'T-ASK): the ban above is ONLY on permission-to-START / approval questions when you ARE in sync. If you're NOT SURE WHAT THE USER IS ASKING — you may have understood something else, OR there are 2+ materially-different valid ways to build it and the user hasn't delegated — you MUST STOP and grill (grill-me), one question at a time, to get in sync BEFORE working; never start while unsure of intent (this holds even if the user said 'you decide'). Open such a genuine intent question with a *Sync-check:* banner — the no-overask hook EXEMPTS that marker (it's required clarification, not over-ask). SSOT: decision-authority.md 'Confidence gate'."
echo "DON'T NARRATE-AND-STOP (hard rule, equal to DECIDE-DON'T-ASK): do NOT end by DESCRIBING the next step (\"next step is…\", \"next I'll…\", \"the continuation is…\", \"remaining work tracked in…\", \"from here…\") and then stopping. If the next item is reversible/internal, EXECUTE it now in the same turn — keep going through the whole queue until only a genuine blocker (escalation / your credentials / a destructive op) remains. The Stop hook BLOCKS a narrate-and-stop and re-injects this rule so you continue."
exit 0
