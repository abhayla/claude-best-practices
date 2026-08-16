#!/usr/bin/env bash
# Stop hook — TELEMETRY-ONLY stop-discipline logger (over-ask + narrate-and-stop).
#
# T-143 (owner-approved 2026-08-16, review Fix 3): this hook used to BLOCK the stop and
# RE-INJECT a rule to force continuation. Evidence across 3 months of rule-tightening (840
# stop-violation auto-continues, 534 enhance-misses) showed compliance never converged and
# each block cost a paid extra model turn. Owner decision: the logs stay (they are the
# instrument), the whip goes. This hook now ONLY LOGS every miss class below — it NEVER
# emits {"decision":"block"} and NEVER re-opens a turn. Log file paths and line formats are
# UNCHANGED so lint_rule_compliance.py keeps working off the same telemetry.
#
# Logged stop-violation classes (never blocking):
#   A. OVER-ASK — trailing offer / multiple-choice / recommendation+question.
#   B. NARRATE-AND-STOP — ending by describing the NEXT reversible step
#      ("next step is…", "next I'll…", "continuation…", "remaining … tracked",
#      "from here…") instead of executing it.
#   Plus the enhance reviewer-card / diagnosis-substance miss classes (G7/substance, below) —
#   all now single log writes, no cap/loop-guard needed since nothing blocks.
#
# Plus the pre-existing NON-BLOCKING telemetry class (the output-side backstop):
#   C. ENHANCE-BANNER MISS — a substantive assistant turn (>=300 chars) that does
#      NOT open with the *Enhanced:* governance banner. WHY: prompt-enhance-reminder.sh
#      gates on PROMPT shape, so it stays silent on short/continuation prompts that
#      still spawn real work. The banner should fire on OUTPUT blast-radius, not prompt
#      shape — the prompt hook can't see output, this Stop hook can. We LOG the miss to
#      .claude/.enhance-misses.log. The behavioral fix is the rule wording in prompt-auto-enhance.md.
#      EXCEPTION: a slash-command turn ($is_slash) is exempt from ALL of class C and the
#      enhance-card/diagnosis telemetry — a /command (user- or Anthropic-made) is run as-is
#      and never enhanced (enhance_slash_commands=false, the canonical plugin default).
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

# ── Slash-command exemption (enhance side only) ──
# A /command — user-made OR Anthropic-provided (/init, /end-session, /grill-me, …) — is run
# EXACTLY as-is and is NEVER routed through the prompt-enhancement pipeline (enhance_slash_commands
# =false, the canonical plugin default; SSOT plugins/prompt-auto-enhance/enhance-settings.default.json).
# So the enhance-card / diagnosis-substance blocks + enhance telemetry below MUST NOT fire on a
# slash-command turn. The over-ask + narrate-and-stop GOVERNANCE guards further down still apply.
# Detect by inspecting the FINAL USER SUBMISSION — not just the last user entry (issue #331).
# The harness writes a slash invocation as TWO consecutive user entries: the <command-name>
# marker entry AND the fully-expanded command BODY as a separate marker-less plain-text entry
# (live repro: session 889094c3 2026-07-12 lines 17-18 — the exact shape H4/issue #279 left
# uncovered as unreproduced). `tail -1` saw only the body and missed the exemption, so /init
# turns were false-blocked. A SUBMISSION = the maximal run of consecutive real-user entries
# (attachment/system entries interleave freely and are ignored). For ORIGIN we walk BACK past
# "Stop hook feedback:" submissions: a stop-block feedback entry is never a real prompt, and it
# must not strip the original turn's slash/machine origin (that stripping caused the /init
# DOUBLE-block — the retry turn was judged as human because its last entry was the feedback).
is_slash=""
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
case "$last_sub" in
  *'<command-name>'*) is_slash="1" ;;
  # A skill EXECUTION turn (reached via /command OR natural language): the harness injects the
  # skill body as a plain user message carrying this stable marker. Skills are enhance-exempt
  # (enhance_slash_commands=false). Anchored to the harness's literal marker.
  *'Base directory for this skill:'*) is_slash="1" ;;
esac
# Raw-client shape: the submission text IS the literal "/command args" prompt; tolerate leading
# whitespace/newlines (H4, issue #279) — now matched on decoded text, not JSON escapes.
if [ -z "$is_slash" ]; then
  case "$(printf '%s' "$last_sub" | sed -E 's/^[[:space:]]+//' | head -c 1)" in
    /) is_slash="1" ;;
  esac
fi

# Drop leading blank lines: the turn-aggregate starts with the newline that
# followed the @@TURN@@ sentinel; head -1 on a blank line would re-create the
# banner false-positive this aggregation exists to kill.
full=$(printf '%s' "$last_text" | tr '[:upper:]' '[:lower:]' | sed -e '/./,$!d')
tail_part=$(printf '%s' "$full" | tail -c 900)
root="$(git rev-parse --show-toplevel 2>/dev/null)"
# T-143: now that this hook is telemetry-only, the log writes below are the SOLE signal (there
# is no block message as a fallback) — make sure the directory exists so a fresh repo/worktree
# with no .claude/ yet doesn't silently swallow every log line (latent pre-existing gap,
# harmless while blocking carried the signal; now load-bearing).
[ -n "$root" ] && mkdir -p "$root/.claude" 2>/dev/null

# ── Banner-present short-circuit (T-116, owner-approved 2026-08-13 evidence-based curation) ──
# WHY: 9 blocks in one session were turns that DID render the *Enhanced:* banner as their first
# line but lacked the full card, or ended on a genuine external blocker — the attest-marker
# workaround (touch .claude/.enhance-card-rendered) was costing a full extra round-trip on
# ordinary tool-heavy turns. A banner-first turn is now its own evidence: it exempts the card
# (G7) and diagnosis-substance ceremony blocks below WITHOUT needing the marker. Does NOT touch
# the #290 WEAK-prompt sampling rule (gradea path unchanged) or the machine/slash exemptions.
banner_present=""
printf '%s' "$full" | head -1 | grep -qE '^\*enhanced' && banner_present="1"

# ── MACHINE-origin turn: exempt the ENHANCE enforcement exactly like a slash command (owner
# 2026-07-10, fire-where-it-pays). A task-notification / scheduled-wakeup / skill-execution /
# system-reminder-only turn is not a human-typed prompt, so its full-process card + banner + role
# telemetry below MUST NOT fire (that was the .enhance-misses.log noise). We reuse the $is_slash
# plumbing: setting it here makes the 5 enhance gates below skip. The OVER-ASK + NARRATE-AND-STOP
# governance guards further down deliberately do NOT consult $is_slash, so they STAY active on
# machine turns (autonomous work still owes decide-don't-ask). SSOT for the predicate: the shared
# turn-origin.sh classifier; fail-open (missing lib => classify_turn stub => human => unchanged).
if [ -f "$root/.claude/hooks/turn-origin.sh" ]; then
  . "$root/.claude/hooks/turn-origin.sh"
fi
command -v classify_turn >/dev/null 2>&1 || classify_turn() { echo human; }
if [ -z "$is_slash" ]; then
  [ "$(classify_turn "$last_sub")" = "machine" ] && is_slash="1"
fi

# ── ENHANCE_MODE gate (auto | ask | off; absent = auto) ──
# Gates ONLY the prompt-enhancement enforcement (reviewer-card + diagnosis-substance
# blocks and the enhance telemetry). The over-ask + narrate-and-stop guards below are
# NOT gated — decide-don't-ask is governance, not the enhancement process. Set by
# prompt-enhance-reminder.sh on an `enhance auto|ask|off` prompt.
emode="$(tr -d '[:space:]' < "$root/.claude/.enhance-mode" 2>/dev/null)"
case "$emode" in auto|ask|off) : ;; *) emode="auto" ;; esac

# ── Full-process enforcement: the independent-reviewer grade card (PRE-exemption) ──
# The prompt-auto-enhance pipeline MUST render the FULL process on EVERY substantive turn; its
# definitive tell is the INDEPENDENT REVIEWER's per-dimension card. This guard blocks when a
# substantive turn (>=300 chars) is NOT a verifiable trivial declaration and shows NO reviewer
# card — INDEPENDENT of banner shape, so the strongest omission (disguised/missing banner)
# cannot escape (gaps G3/G4/G7/G9/G11 from the 2026-06-18 enforcement audit). Runs BEFORE the
# sync-check exemption. Loop-guard (.reviewcard-count, reset per turn), cap 4.
# G4: a turn is exempt only if its FIRST line declares "ran as-is" AND the turn is short —
# a long working turn cannot dodge by mentioning the phrase somewhere in prose.
trivial=""
printf '%s' "$full" | head -1 | grep -qE "ran (your )?input as-is|ran as-is|no change —|no enhancement" && [ "${#last_text}" -lt 600 ] && trivial="1"
# GRADE-A LITE PATH (issue #290, owner-approved ceremony downgrade): the full grade-card +
# independent-reviewer is now SAMPLED — required only on WEAK prompts (that needed
# strengthening). A turn that explicitly declares Grade-A/no-strengthening in its FIRST 3
# LINES is exempt from the full-card enforcement below; it only owes the banner + a one-line
# declaration. The 3-line window (vs. the 1-line/short-only `trivial` check above) lets a
# longer substantive Grade-A turn still qualify — length alone no longer forces the full table.
gradea=""
printf '%s' "$full" | head -3 | grep -qE "grade a[^a-z]|grade: a|no strengthening needed|no change —|ran (your )?input as-is|ran as-is|0 fix|no fix|prompt already strong \(grade [0-9]" && gradea="1"
# G11: detect the full process by the reviewer-card token SET (not one literal), so a
# legitimately-worded card is not false-blocked. H1 (issue #279): also credit the enhance
# card's HEADER ROW — a markdown row that pairs "reviewer" with a before/after/self column
# (e.g. "| Dimension | Before | After | Blind reviewer |") — even when it uses none of the
# fixed prose tokens below. The before/after/self co-requirement keeps an UNRELATED table row
# that merely contains "reviewer" (e.g. "| File | Reviewer |") from counting as a card.
card=""
printf '%s' "$full" | grep -qE "^[[:space:]]*\|.*(before|after|self).*reviewer.*\||reviewer-after|reviewer col|blind re-?grade|independent[ -]reviewer" && card="1"
# H2 (issue #279): also require the closing Overall/total row (mirrors the plugin guard's
# overall check) — a per-dimension table with no total row is an incomplete card, not a
# rendered one.
overall=""
printf '%s' "$full" | grep -qE "overall|[a-f] *(→|->) *[a-f]|weighted total" && overall="1"
# ── Marker attestation (2026-07-15, session fedaf490 root-cause): the harness DROPS assistant
# text blocks that share one API response with tool_use blocks — a correctly-rendered
# pre-execution card (the owner-mandated ordering, prompt-auto-enhance.md) never persists to
# the transcript on such turns, so its absence there is NOT evidence it wasn't rendered.
# The model attests the render by touching .claude/.enhance-card-rendered.<session_id> in the
# same turn (reset per real user prompt by prompt-enhance-reminder.sh). SESSION-SCOPED (live
# incident 2026-07-15: a concurrent worker session's reminder wiped the shared marker) — each
# session touches/checks only its own; the guard also accepts the legacy unscoped name from
# the same fix-day so an in-flight session isn't re-broken.
sid=$(printf '%s' "$input" | jq -r '.session_id // ""')
card_marker=""
if { [ -n "$sid" ] && [ -f "$root/.claude/.enhance-card-rendered.$sid" ]; } || [ -f "$root/.claude/.enhance-card-rendered" ]; then
  card_marker="1"; card="1"; overall="1"
fi
# G7: block on substantive + not-trivial + (NO card OR NO overall row), regardless of banner
# shape — AND not-grade-a-declared (#290: an explicitly-declared Grade-A/no-strengthening
# turn is sampled OUT of this gate; the base substantive/not-trivial/no-card condition below
# is preserved byte-for-byte so it stays a pure ADDITIVE exemption, never a rewrite).
# T-116: AND not-banner-present — a turn whose FIRST visible line IS the *Enhanced:* banner is
# its own evidence the process ran; it is never blocked here for a missing card (see the
# banner_present short-circuit above). Pure ADDITIVE exemption on top of the #290 gate.
# T-143 (owner-approved 2026-08-16, Fix 3): this guard is TELEMETRY-ONLY — it must never
# emit {"decision":"block"} or re-open a turn. Every miss still gets logged (same log file,
# same line formats, so lint_rule_compliance.py keeps working) — only the block+exit+loop-cap
# mechanics are gone; a single log write replaces the old "block, then cap-exhausted log" pair.
if [ "$emode" = "auto" ] && [ -z "$is_slash" ] && [ "${#last_text}" -ge 300 ] && [ -z "$trivial" ] && { [ -z "$card" ] || [ -z "$overall" ]; } && [ -z "$gradea" ] && [ -z "$banner_present" ]; then
  printf '%s\treviewer-card-miss (len=%s)\n' "$(jq -rn 'now|todate' 2>/dev/null || echo now)" "${#last_text}" >> "$root/.claude/.overask-violations.log" 2>/dev/null
fi

# ── Substance enforcement: the diagnose→fix linkage, not just the score card (2026-06-19) ──
# WHY: the card block above enforces the reviewer COLUMN (shape) — but the hook could not see
# whether the per-step IMPROVEMENT substance was present, so it silently rotted to a scores-only
# card. The skill (STEP 1 Diagnose / STEP 2 Map Fixes / STEP 4 Changes Applied) mandates a
# numbered Diagnosis block, a per-dimension Fix column, and a canonical Changes Applied list —
# "every raised After score MUST be earned by a listed Fix [n]". Enforcing only the reviewer
# column let the diagnose→fix chain disappear (the exact shape-vs-substance drift
# output-plausibility-verification.md warns about; user-reported 2026-06-19). This guard fires
# when an enhancement card IS rendered (card="1") on a substantive, non-trivial turn but shows
# NONE of the diagnosis/fix substance tokens. Grade-A / zero-fix turns legitimately have no
# diagnosis, so the token set treats "grade a"/"0 fix" as substance-accounted. Own loop-guard
# (.diagnosis-count, reset per turn by prompt-enhance-reminder.sh), cap 4.
substance=""
printf '%s' "$full" | grep -qE "diagnosis:|changes applied|missing_role|missing_context|missing_output|vague_intent|under_constrained|missing_structure|missing_example|missing_constraint|grade: a|grade a[^a-z]|0 fix|no fix|zero fix" && substance="1"
[ -n "$card_marker" ] && substance="1"
# T-116: banner-present is its own evidence — see G7 above for the same reasoning.
if [ "$emode" = "auto" ] && [ -z "$is_slash" ] && [ "${#last_text}" -ge 300 ] && [ -z "$trivial" ] && [ -n "$card" ] && [ -z "$substance" ] && [ -z "$banner_present" ]; then
  printf '%s\tdiagnosis-substance-miss (len=%s)\n' "$(jq -rn 'now|todate' 2>/dev/null || echo now)" "${#last_text}" >> "$root/.claude/.overask-violations.log" 2>/dev/null
fi

# ── Exemption: *Session-boundary:* — a completed-tested-chunk stop is legitimate. ──
# Mirrors *Sync-check:* but for the STOP side: when a tested/verified chunk is complete AND
# committed, AND all remaining work is owner-gated (sign-off/deploy/spend) or explicitly
# deferred-for-quality (a coherent unit needing fresh, non-saturated context), the model opens a
# line with `*Session-boundary:*` and stops — that is a LEGITIMATE boundary, not a narrate-and-stop.
# (Abhay-approved 2026-06-19; proposal in .claude/tasks/lessons.md.) The hook cannot verify the
# "tested + committed + only-gated-remainder" preconditions deterministically, so unlike sync-check
# it LOGS every use to the violations log for audit — abuse (using the marker to dodge real
# reversible work) is therefore visible in telemetry. Runs AFTER the reviewer-card guard, so a
# session-boundary wrap-up turn STILL renders the full enhance card.
if printf '%s' "$full" | grep -qE "session-boundary"; then
  printf '%s\tsession-boundary-stop (exempted, len=%s)\n' "$(jq -rn 'now|todate' 2>/dev/null || echo now)" "${#last_text}" >> "$root/.claude/.overask-violations.log" 2>/dev/null
  exit 0
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
# T-116: extended with the NAMED-EXTERNAL-BLOCKER class (background/dispatched worker in
# flight, a scheduled wakeup, an awaited async result) — evidence: the 9-block session had
# turns ending on exactly this kind of blocker, unrecognized by the prior pattern set.
if printf '%s' "$full" | grep -qE "push to prod|deploy|dns|cutover|force[- ]push|--force|spend|publish|destructive|drop (table|column)|delete (the )?(branch|remote)|escalat|blocked on|gated on (you|your)|yours to (do|run|paste)|need (your|you to)|your (credential|password|approval|login|call)|waiting on (you|the user)|log in yourself|run .* yourself|requires? your|sync-check|in flight|background (worker|task|agent)|scheduled wakeup|dispatched worker|worker (is )?(running|in progress)|await(ing)? (the )?(worker|agent|result)|will (be )?notif(y|ied)|notification (will|when) arrive"; then
  exit 0
fi

# ── C. Enhance-banner miss (output-side telemetry, NON-BLOCKING) ──
# Substantive proxy: assistant text >= 300 chars. Banner = first line opens with
# "*enhanced" (case-insensitive). Log-only; never blocks, never sets $flag.
# Limitation (v1, KISS): a short message that nonetheless made tool edits is not
# caught by the length proxy — revisit with a tool_use scan if the log warrants.
if [ "$emode" = "auto" ] && [ -z "$is_slash" ] && [ "${#last_text}" -ge 300 ] && ! printf '%s' "$full" | head -1 | grep -qE '^\*enhanced'; then
  printf '%s\tenhance-banner-miss (len=%s)\n' "$(jq -rn 'now|todate' 2>/dev/null || echo now)" "${#last_text}" >> "$root/.claude/.enhance-misses.log" 2>/dev/null
fi
# Block-miss: substantive turn that HAS the banner but shows NEITHER the
# enhanced-prompt block ("final prompt"/"what changed") NOR the trivial "ran as-is"
# one-liner → the user can't see what was enhanced. Non-blocking telemetry (the
# behavioral fix is the MANDATORY OUTPUT section in prompt-auto-enhance-rule.md).
if [ "$emode" = "auto" ] && [ -z "$is_slash" ] && [ -z "$gradea" ] && [ "${#last_text}" -ge 300 ] && printf '%s' "$full" | head -1 | grep -qE '^\*enhanced' && ! printf '%s' "$full" | grep -qE "final prompt|what changed|ran (your )?input as-is|ran as-is|no change — ran|no enhancement"; then
  printf '%s\tenhance-block-miss (len=%s)\n' "$(jq -rn 'now|todate' 2>/dev/null || echo now)" "${#last_text}" >> "$root/.claude/.enhance-misses.log" 2>/dev/null
fi
# Role-miss (R1 persona): a final-prompt block whose text lacks "act as" — the R1 role
# line is missing from the strengthened prompt (see the prompt-auto-enhance skill's Role
# Selection Guide: mandatory when the Role dimension scores < 7, at EVERY grade incl. A).
# Limitation (v1, telemetry-only): role-sufficient prompts (Role >= 7) legitimately lack
# it, so this LOGS, never blocks — escalate to a block only if the log shows it stays frequent.
if [ "$emode" = "auto" ] && [ -z "$is_slash" ] && [ "${#last_text}" -ge 300 ] && printf '%s' "$full" | grep -qE "final (strengthened )?prompt" && ! printf '%s' "$full" | grep -qE "act as"; then
  printf '%s\trole-miss (len=%s)\n' "$(jq -rn 'now|todate' 2>/dev/null || echo now)" "${#last_text}" >> "$root/.claude/.enhance-misses.log" 2>/dev/null
fi

# ── A. Over-ask detection ──
flag=""
printf '%s' "$tail_part" | grep -qE "want me to|should i |shall i |would you like me to|do you want me to|let me know if|say the word|which (would|do) you|or (should|do|leave) (i|we|them|it)" && flag="over-ask: trailing offer"
[ -z "$flag" ] && printf '%s' "$tail_part" | grep -qE "q[0-9]+ of|which (option|default|one|approach|do you want)|,? or [a-d]\?|\b[a-d], [a-d],? (or )?[a-d]\?|which —|which\?" && flag="over-ask: multiple-choice"
ends_q=$(printf '%s' "$tail_part" | grep -qE '\?[[:space:]]*$' && echo 1 || echo 0)
[ -z "$flag" ] && [ "$ends_q" = "1" ] && printf '%s' "$full" | grep -qE "recommend" && flag="over-ask: recommendation+question"

# ── B. Narrate-and-stop detection (deferred next-step language) ──
[ -z "$flag" ] && printf '%s' "$tail_part" | grep -qE "next step|next, i|next i('|’)?ll|the continuation|continuation from here|from here[.:]|immediate next|next up|i('|’)?ll (work|tackle|start|do|continue|extend|implement|build|close|fix|add|wire|drive|cover)|remaining[^.]{0,40}(tracked|stays|remain|in #)|the rest[^.]{0,40}(tracked|stays|remain|in #)|that('|’)?s the continuation|is the continuation|work #[0-9]|items? (left|remain)|the only[^.]{0,40}(left|remain|item)|remainder|narrow (remainder|bit|layer|follow|scope|item)|separate[, ]{0,3}(thin )?scope|thin scope|follow-?up|noted in #[0-9]|tracked in #[0-9]|are (genuinely )?separate|stays? (a |as )?follow|two items|one (narrow|thin)([^a-z]|$)" && flag="narrate-and-stop"

[ -z "$flag" ] && exit 0

# ── T-143 (owner-approved 2026-08-16, Fix 3): TELEMETRY-ONLY — log the stop-violation and
# release the turn. Never emit {"decision":"block"}; the loop-guard/cap machinery that used to
# gate re-opening the turn is gone (there is nothing left to cap). Log line format unchanged
# so lint_rule_compliance.py keeps working.
cf="$root/.claude/.keepgoing-count"
n=$(cat "$cf" 2>/dev/null || echo 0); case "$n" in ''|*[!0-9]*) n=0 ;; esac
log="$root/.claude/.overask-violations.log"
printf '%s\tstop-violation (%s) — autocontinue #%s\n' "$(jq -rn 'now|todate' 2>/dev/null || echo now)" "$flag" "$((n+1))" >> "$log" 2>/dev/null
printf '%s' "$((n+1))" > "$cf" 2>/dev/null
exit 0
