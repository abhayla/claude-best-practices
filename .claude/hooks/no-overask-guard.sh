#!/usr/bin/env bash
# Stop hook — deterministic STOP-DISCIPLINE guard (over-ask + narrate-and-stop).
#
# WHY: advisory rules ("decide reversible work, don't ask" + "build, don't
# narrate-and-stop") lose under long context — turns end either asking a
# question the assistant should have decided (decision-authority.md), OR
# DESCRIBING the next step ("next step is edit/delete") and stopping instead of
# doing it. Per rule-writing-meta.md, zero-exception behaviour needs a HOOK,
# not prose. This hook BLOCKS the stop and RE-INJECTS the rule so the model
# keeps going.
#
# Two BLOCKING stop-violation classes detected:
#   A. OVER-ASK — trailing offer / multiple-choice / recommendation+question.
#   B. NARRATE-AND-STOP — ending by describing the NEXT reversible step
#      ("next step is…", "next I'll…", "continuation…", "remaining … tracked",
#      "from here…") instead of executing it.
# On either (and NOT a genuine blocker), it emits {"decision":"block","reason":…}
# to force continuation. A per-user-turn counter (.claude/.keepgoing-count, reset
# by prompt-enhance-reminder.sh) caps auto-continues at 12 to prevent any loop.
#
# Plus one NON-BLOCKING telemetry class (the output-side backstop):
#   C. ENHANCE-BANNER MISS — a substantive assistant turn (>=300 chars) that does
#      NOT open with the *Enhanced:* governance banner. WHY: prompt-enhance-reminder.sh
#      gates on PROMPT shape, so it stays silent on short/command/continuation prompts
#      that still spawn real work (the /init class). The banner should fire on OUTPUT
#      blast-radius, not prompt shape — the prompt hook can't see output, this Stop
#      hook can. We LOG the miss to .claude/.enhance-misses.log (telemetry first —
#      escalate to a block only if the log shows it's frequent). The behavioral fix
#      is the rule wording in prompt-auto-enhance-rule.md.
exec 2>/dev/null
input=$(cat)
command -v jq >/dev/null || exit 0
tp=$(printf '%s' "$input" | jq -r '.transcript_path // ""')
if [ -z "$tp" ] || [ ! -f "$tp" ]; then exit 0; fi

# Aggregate ALL assistant text of the FINAL turn — everything after the last REAL
# user prompt. Tool-result entries are type "user" too and must NOT split the turn.
# WHY: analyzing only the LAST text block produces false positives — the
# *Enhanced:* banner lives on the FIRST block of a multi-block (tool-using) turn
# (measured: 58 of 59 logged banner-misses in 7 days were this false positive).
# Per-turn aggregation restores telemetry precision.
last_text=$(jq -r '
  if .type=="user" and ((.message.content|type)=="string" or ([.message.content[]?|.type]|index("tool_result")|not))
  then "@@TURN@@"
  elif .type=="assistant"
  then ((.message.content[]? | select(.type=="text") | .text) + "\n")
  else empty end' "$tp" 2>/dev/null | awk 'BEGIN{RS="@@TURN@@"} END{printf "%s", $0}')
[ -z "$last_text" ] && exit 0

# Drop leading blank lines: the turn-aggregate starts with the newline that
# followed the @@TURN@@ sentinel; head -1 on a blank line would re-create the
# banner false-positive this aggregation exists to kill.
full=$(printf '%s' "$last_text" | tr '[:upper:]' '[:lower:]' | sed -e '/./,$!d')
tail_part=$(printf '%s' "$full" | tail -c 900)
root="$(git rev-parse --show-toplevel 2>/dev/null)"

# ── Full-process enforcement: the independent-reviewer grade card (PRE-exemption) ──
# The prompt-auto-enhance pipeline MUST render the FULL process — whose definitive tell is the
# INDEPENDENT REVIEWER's per-dimension "reviewer-after" card column (skill STEP 3.6/4) — on
# EVERY substantive enhanced turn. Block when: the turn is substantive (>=300), opens with the
# *Enhanced banner, is NOT the trivial "ran as-is" one-liner, and the "reviewer-after" column
# is ABSENT — REGARDLESS of whether a partial strengthened-prompt block was shown. WHY drop the
# old "block-present" gate: keying on "self-after|final prompt|what changed" let a banner-ONLY
# turn (whole process omitted, none of those tokens present) EVADE the block and be merely
# logged — omitting MORE escaped while omitting less got caught (backwards). Now any
# substantive enhanced turn must render the reviewer card OR declare the prompt trivial. Runs
# BEFORE the sync-check exemption. Loop-guard (.reviewcard-count, reset per turn), cap 4.
trivial="";  printf '%s' "$full" | grep -qE "ran (your )?input as-is|ran as-is|no change — ran|no enhancement" && trivial="1"
if [ "${#last_text}" -ge 300 ] && [ -z "$trivial" ] \
   && printf '%s' "$full" | head -1 | grep -qE '^\*enhanced' \
   && ! printf '%s' "$full" | grep -qE "reviewer-after"; then
  rc="$root/.claude/.reviewcard-count"
  rn=$(cat "$rc" 2>/dev/null || echo 0); case "$rn" in ''|*[!0-9]*) rn=0 ;; esac
  printf '%s\treviewer-card-miss — autocontinue #%s\n' "$(jq -rn 'now|todate' 2>/dev/null || echo now)" "$((rn+1))" >> "$root/.claude/.overask-violations.log" 2>/dev/null
  if [ "$rn" -lt 4 ]; then
    printf '%s' "$((rn+1))" > "$rc" 2>/dev/null
    jq -nc --arg r "STOP BLOCKED (enhance: full process not rendered). This substantive enhanced turn opened with the *Enhanced banner but did NOT render the full prompt-auto-enhance process — the tell is the missing independent-reviewer 'Reviewer-after' per-dimension card column (skill STEP 3.6/4). Render the FULL process now: pipeline transcript + before→after grade card WITH the Reviewer-after column (Before · Self-after · Reviewer-after · Weight) + Original→Final prompt + Role line. If the user's prompt was genuinely trivial/continuation, render the '*Enhanced: no change — ran your input as-is*' one-liner instead." '{decision:"block", reason:$r}'
    exit 0
  fi
fi

# ── Exemption: a GENUINE blocker / escalation / user-input-needed stop is legitimate. ──
# Includes the deliberate `*Sync-check:*` INTENT-GRILL marker: when the assistant is
# genuinely NOT SURE WHAT THE USER IS ASKING (intent ambiguity OR a consequential design fork
# with 2+ valid builds, and the user hasn't delegated), it opens the clarifying question with a
# `*Sync-check:*` banner and grills ONE question at a time — that is REQUIRED, not over-ask, so
# it must NOT be blocked. (The ban stays for permission-to-START / "shall I go ahead" offers
# when already in sync — those carry no marker and still match the over-ask patterns below.)
# Honest use is governed by decision-authority.md "Confidence gate"; abuse is visible (the
# banner renders to the user).
if printf '%s' "$full" | grep -qE "push to prod|deploy|dns|cutover|force[- ]push|--force|spend|publish|destructive|drop (table|column)|delete (the )?(branch|remote)|escalat|blocked on|need (your|you to)|your (credential|password|approval|login|call)|waiting on (you|the user)|log in yourself|run .* yourself|requires? your|sync-check"; then
  exit 0
fi

# ── C. Enhance-banner miss (output-side telemetry, NON-BLOCKING) ──
# Substantive proxy: assistant text >= 300 chars. Banner = first line opens with
# "*enhanced" (case-insensitive). Log-only; never blocks, never sets $flag.
# Limitation (v1, KISS): a short message that nonetheless made tool edits is not
# caught by the length proxy — revisit with a tool_use scan if the log warrants.
if [ "${#last_text}" -ge 300 ] && ! printf '%s' "$full" | head -1 | grep -qE '^\*enhanced'; then
  printf '%s\tenhance-banner-miss (len=%s)\n' "$(jq -rn 'now|todate' 2>/dev/null || echo now)" "${#last_text}" >> "$root/.claude/.enhance-misses.log" 2>/dev/null
fi
# Block-miss: substantive turn that HAS the banner but shows NEITHER the
# enhanced-prompt block ("final prompt"/"what changed") NOR the trivial "ran as-is"
# one-liner → the user can't see what was enhanced. Non-blocking telemetry (the
# behavioral fix is the MANDATORY OUTPUT section in prompt-auto-enhance-rule.md).
if [ "${#last_text}" -ge 300 ] && printf '%s' "$full" | head -1 | grep -qE '^\*enhanced' && ! printf '%s' "$full" | grep -qE "final prompt|what changed|ran (your )?input as-is|ran as-is|no change — ran|no enhancement"; then
  printf '%s\tenhance-block-miss (len=%s)\n' "$(jq -rn 'now|todate' 2>/dev/null || echo now)" "${#last_text}" >> "$root/.claude/.enhance-misses.log" 2>/dev/null
fi
# Role-miss (R1 persona): a final-prompt block whose text lacks "act as" — the R1 role
# line is missing from the strengthened prompt (see the prompt-auto-enhance skill's Role
# Selection Guide: mandatory when the Role dimension scores < 7, at EVERY grade incl. A).
# Limitation (v1, telemetry-only): role-sufficient prompts (Role >= 7) legitimately lack
# it, so this LOGS, never blocks — escalate to a block only if the log shows it stays frequent.
if [ "${#last_text}" -ge 300 ] && printf '%s' "$full" | grep -qE "final (strengthened )?prompt" && ! printf '%s' "$full" | grep -qE "act as"; then
  printf '%s\trole-miss (len=%s)\n' "$(jq -rn 'now|todate' 2>/dev/null || echo now)" "${#last_text}" >> "$root/.claude/.enhance-misses.log" 2>/dev/null
fi

# ── A. Over-ask detection ──
flag=""
printf '%s' "$tail_part" | grep -qE "want me to|should i |shall i |would you like me to|do you want me to|let me know if|say the word|which (would|do) you|or (should|do|leave) (i|we|them|it)" && flag="over-ask: trailing offer"
[ -z "$flag" ] && printf '%s' "$tail_part" | grep -qE "q[0-9]+ of|which (option|default|one|approach|do you want)|,? or [a-d]\?|\b[a-d], [a-d],? (or )?[a-d]\?|which —|which\?" && flag="over-ask: multiple-choice"
ends_q=$(printf '%s' "$tail_part" | grep -qE '\?[[:space:]]*$' && echo 1 || echo 0)
[ -z "$flag" ] && [ "$ends_q" = "1" ] && printf '%s' "$full" | grep -qE "recommend" && flag="over-ask: recommendation+question"

# ── B. Narrate-and-stop detection (deferred next-step language) ──
[ -z "$flag" ] && printf '%s' "$tail_part" | grep -qE "next step|next, i|next i('|’)?ll|the continuation|continuation from here|from here[.:]|immediate next|next up|i('|’)?ll (work|tackle|start|do|continue|extend|implement|build|close|fix|add|wire|drive|cover)|remaining[^.]{0,40}(tracked|stays|remain|in #)|the rest[^.]{0,40}(tracked|stays|remain|in #)|that('|’)?s the continuation|is the continuation|work #[0-9]|items? (left|remain)|the only[^.]{0,40}(left|remain|item)|remainder|narrow (remainder|bit|layer|follow|scope|item)|separate[, ]{0,3}(thin )?scope|thin scope|follow-?up|noted in #[0-9]|tracked in #[0-9]|are (genuinely )?separate|stays? (a |as )?follow|two items|one (narrow|thin)" && flag="narrate-and-stop"

[ -z "$flag" ] && exit 0

# ── Loop-guard: cap auto-continues per user turn ──
cf="$root/.claude/.keepgoing-count"
n=$(cat "$cf" 2>/dev/null || echo 0); case "$n" in ''|*[!0-9]*) n=0 ;; esac
log="$root/.claude/.overask-violations.log"
printf '%s\tstop-violation (%s) — autocontinue #%s\n' "$(jq -rn 'now|todate' 2>/dev/null || echo now)" "$flag" "$((n+1))" >> "$log" 2>/dev/null

if [ "$n" -ge 12 ]; then
  echo "STOP-DISCIPLINE: auto-continue cap (12) hit this turn — yielding. If real reversible work remains, you are over-stopping; if you're blocked, state the blocker explicitly."
  exit 0
fi
printf '%s' "$((n+1))" > "$cf" 2>/dev/null

reason="STOP BLOCKED ($flag). decision-authority.md + build-don't-narrate: you ended your turn with a stop-violation on REVERSIBLE work. DO NOT ask, and DO NOT narrate-and-stop (describe the next step then stop). EXECUTE the next item NOW in this same turn — if it's reversible/internal (edit/delete coverage, the next tracked #issue item, the next fix, a commit, the next queued task) just DO it; chain through the WHOLE queue until ONLY a genuine blocker remains (your credentials, a destructive/irreversible op, spend, deploy, a true product fork — then state it in one line). Keep going."
jq -nc --arg r "$reason" '{decision:"block", reason:$r}'
exit 0
