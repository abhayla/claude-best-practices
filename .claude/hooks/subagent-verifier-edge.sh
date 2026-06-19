#!/usr/bin/env bash
# SubagentStop hook — supervisor-verification salience at the WORKER boundary.
# supervisor-verification.md requires the T0 orchestrator to REPRODUCE a worker's
# claimed gate + inspect the substance before accepting it — "reading the claim is
# not verifying it." The existing verifier-edge-guard.sh catches this at the T0
# Stop boundary (main-loop done-claims); this hook adds the same salience at the
# moment a dispatched worker RETURNS, so the supervisor duty is surfaced exactly
# when a worker contract lands — not relied upon from memory.
#
# Emits additionalContext (a reminder), non-blocking, always exit 0. It does NOT
# block subagent completion — it reinforces the T0 supervisor gate, which remains
# the actual acceptance decision.
# RUNTIME NOTE: unit-verified + wired, but whether SubagentStop fires in the
# installed Claude Code version is session-pinned — confirm via a live dispatch
# after a session restart (newly-wired hooks are not active mid-session).
exec 2>/dev/null

read -r -d '' MSG <<'EOF'
=== SUPERVISOR GATE (auto-surfaced by subagent-verifier-edge at worker return) ===
A worker subagent just returned. Its "done / clean / tests pass" is a CLAIM, not proof
(supervisor-verification.md). Before accepting / building on / committing it:
1. REPRODUCE its claimed gate yourself (re-run the lint/type-check/tests it reported).
2. INSPECT the substance (read the diff/artifact for scope creep + out-of-brief changes).
3. For UI-changing output, DRIVE the running app (screenshot + interaction), not code-read.
On any divergence, return the work or fix at T0 — never accept-and-hope.
EOF

printf '{"hookSpecificOutput":{"hookEventName":"SubagentStop","additionalContext":%s}}\n' \
  "$(printf '%s' "$MSG" | python -c 'import json,sys; print(json.dumps(sys.stdin.buffer.read().decode("utf-8","replace")))' 2>/dev/null || echo '""')"
exit 0
