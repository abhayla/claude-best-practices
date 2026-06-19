#!/usr/bin/env bash
# SubagentStart hook — deterministically injects the load-bearing dispatch
# mandates into EVERY worker subagent's context. plan-before-coding.md
# §"Propagation to dispatched workers" requires the orchestrator to paste
# "plan first + root-cause-not-patch + return a structured contract" into every
# code-changing worker — but that is advisory prose that loses to time pressure.
# A SubagentStart hook makes it a harness guarantee instead of a remembered step.
#
# Emits the documented `additionalContext` envelope. Non-blocking; always exit 0.
# RUNTIME NOTE: this hook is unit-verified + wired, but whether SubagentStart
# fires in a given Claude Code version (and the exact context-injection format)
# must be confirmed by a live dispatch after a session restart — newly-wired
# hooks are not picked up mid-session (same session-pinning caveat as agents).
exec 2>/dev/null

read -r -d '' GUIDANCE <<'EOF'
=== DISPATCH MANDATES (auto-injected by subagent-governance-inject hook) ===
If your task changes code:
1. PLAN FIRST — before the first edit, map the root cause to its single source AND
   enumerate EVERY consumer/surface the change touches. If you cannot list them, you
   are not ready to edit (plan-before-coding.md).
2. ROOT CAUSE, NOT PATCH — fix the underlying cause across ALL affected surfaces;
   never patch the first visible symptom and leave siblings live.
3. RETURN A STRUCTURED CONTRACT — finish by returning {gate, artifacts, decisions,
   blockers, summary} so the T0 supervisor can reproduce your gate, not just read
   your claim (supervisor-verification.md). A self-reported "done/clean/passing" is
   a claim, not proof.
EOF

# Emit the documented additionalContext envelope. If the running version instead
# adds plain stdout to context, the JSON is still harmless inert text — the live
# probe after restart confirms which form this version honors.
printf '{"hookSpecificOutput":{"hookEventName":"SubagentStart","additionalContext":%s}}\n' \
  "$(printf '%s' "$GUIDANCE" | python -c 'import json,sys; print(json.dumps(sys.stdin.read()))' 2>/dev/null || echo '""')"
exit 0
