#!/usr/bin/env bash
# Stop hook — VERIFIER-EDGE salience guard (telemetry-first).
#
# WHY: three gates share one concern — "did you run the INDEPENDENT verifier
# before claiming done?" — and all three are the advisory-only, model-self-
# classified class of governance that loses under context pressure:
#   - reviewer-edge          (engineering-roles.md): every builder role -> Code-
#                            Quality Reviewer before "done"; author never sole verifier.
#   - independent-test-verify (independent-test-verification.md): a test verdict
#                            must be re-checked by a context-blind second agent.
#   - supervisor-verify       (supervisor-verification.md): reproduce the worker's
#                            gate + inspect substance before accepting its output.
# Per rule-writing-meta.md, zero-exception behaviour needs a HOOK, not prose.
#
# This hook makes the MISS visible. It fires when a turn (a) did BUILDER work
# (Edit/Write code, dispatched a Task subagent, or ran tests) AND (b) ends with a
# DONE/PASS claim, BUT (c) shows NO evidence the independent verifier ran. It does
# NOT block (telemetry-first, like no-overask-guard class C): a blocking heuristic
# would false-positive-interrupt. It LOGS to .claude/.verifier-misses.log; escalate
# to a block only if the log shows misses are frequent. The behavioural fix lives in
# the three rules above; this is the salience backstop that keeps them unmissable.
exec 2>/dev/null
input=$(cat)
command -v jq >/dev/null || exit 0
tp=$(printf '%s' "$input" | jq -r '.transcript_path // ""')
[ -z "$tp" ] || [ ! -f "$tp" ] && exit 0
root="$(git rev-parse --show-toplevel 2>/dev/null)"

# Slice the FINAL turn (everything after the last REAL user prompt — tool_result
# entries are type "user" too and must NOT count as the boundary), then extract the
# turn's assistant text AND its tool_use lines ("<name> :: <path-or-command>").
slice=$(jq -s '
  ( [ .[] | (.type=="user" and ((.message.content|type)=="string"
      or ([.message.content[]?|.type]|index("tool_result")|not))) ]
    | (length - 1 - (reverse|index(true))) ) as $lu
  | (if $lu == null then . else .[$lu+1:] end)
  | { text: ([ .[] | select(.type=="assistant") | .message.content[]?
                | select(.type=="text") | .text ] | join("\n")),
      tools: ([ .[] | select(.type=="assistant") | .message.content[]?
                | select(.type=="tool_use")
                | (.name + " :: " + ((.input.file_path // .input.command // "")|tostring)) ] | join("\n")) }
' "$tp" 2>/dev/null)
[ -z "$slice" ] && exit 0

text=$(printf '%s' "$slice" | jq -r '.text // ""' | tr '[:upper:]' '[:lower:]')
tools=$(printf '%s' "$slice" | jq -r '.tools // ""')
[ "${#text}" -lt 200 ] && exit 0   # substantive-turn proxy; trivial turns are exempt

# (a) BUILDER signal — a code Edit/Write (NOT pure docs/.md/.txt/.json), a Task
# subagent dispatch, or a test-runner Bash command in this turn.
builder=""
printf '%s' "$tools" | grep -qE '^(Edit|Write|MultiEdit|NotebookEdit) :: .*\.(py|ts|tsx|js|jsx|go|rs|java|kt|kts|rb|php|c|cc|cpp|h|hpp|cs|swift|sh|sql|vue|svelte)\b' && builder="code-edit"
[ -z "$builder" ] && printf '%s' "$tools" | grep -qE '^Task :: ' && builder="subagent"
[ -z "$builder" ] && printf '%s' "$tools" | grep -qE '^Bash :: .*(pytest|jest|vitest|mocha|go test|cargo test|gradle.*test|npm (run )?test|yarn test|pnpm test|phpunit|rspec|playwright test)' && builder="test-run"
[ -z "$builder" ] && exit 0

# (b) DONE/PASS claim in the turn's text.
printf '%s' "$text" | grep -qE "\b(done|complete|completed|shipped|merged|all (tests )?pass|tests pass|passing|green|verified|works (now|as)|fixed|ready to (commit|merge|ship))\b" || exit 0

# (c) INDEPENDENT-VERIFIER evidence — if present, the edge was honored; stay silent.
printf '%s' "$text" | grep -qE "code[- ]review|reviewer|review-gate|request-code-review|code-quality|blind verif|independent (test )?verif|second (agent|checker)|supervisor[- ]?verif|reproduce[d]? the (gate|test)|re-?ran (the )?(test|lint|gate)|adversarial review|quality-gate-evaluator|dispatched .* review" && exit 0

# Miss: builder work + done-claim, no verifier-edge evidence → log (non-blocking).
printf '%s\tverifier-edge-miss (%s; len=%s)\n' \
  "$(jq -rn 'now|todate' 2>/dev/null || echo now)" "$builder" "${#text}" \
  >> "$root/.claude/.verifier-misses.log" 2>/dev/null
exit 0
