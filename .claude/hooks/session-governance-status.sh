#!/usr/bin/env bash
# SessionStart hook — emits role/governance STATE as variables so every session
# boots with a machine-readable status block. Advisory MUSTs (supervisor
# verification, role routing) get silently dropped under task-focus; a
# deterministic session-start surface fixes that class of miss.
# Non-blocking: prints to stdout (added to session context), always exit 0.
exec 2>/dev/null
root=$(git rev-parse --show-toplevel 2>/dev/null) || root="."

echo "=== GOVERNANCE (session-start variables) ==="
echo "ORCHESTRATOR_SUPERVISOR=on  rule=.claude/rules/supervisor-verification.md"
echo "SUPERVISOR_DUTY=reproduce-gate+inspect-substance-before-accepting-any-worker-output"

echo "GIT_BRANCH=$(git -C "$root" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"
echo "GIT_UNCOMMITTED=$(git -C "$root" status --porcelain 2>/dev/null | grep -c .)"
echo "ROLE_CODEQUALITY=required-after-any-build (independent pass — see independent-test-verification.md)"
echo "ROLE_ROUTER=.claude/rules/engineering-roles.md  (state Role:<name> on non-trivial tasks)"

# Enhance-misses telemetry loop: the prompt-enhance pipeline (no-overask-guard.sh)
# logs banner/block/role misses to .enhance-misses.log, but a write-only log is
# governance theater — surface a 7-day summary every session so drift is SEEN.
# ISO timestamps sort lexicographically, so a string compare against the 7-day
# cutoff works.
ml="$root/.claude/.enhance-misses.log"
if [ -f "$ml" ] && command -v jq >/dev/null; then
  cutoff=$(jq -rn 'now-604800|todate')
  recent=$(awk -v c="$cutoff" '$1 >= c' "$ml" | grep -c .)
  newest=$(tail -1 "$ml" | cut -f2)
  echo "ENHANCE_MISSES_7D=$recent  (total: $(grep -c . "$ml"); newest: ${newest:-none})"
  [ "$recent" -gt 5 ] && echo "ENHANCE_MISSES_ALERT=miss-rate-high — review .claude/.enhance-misses.log + tighten the failing class"
else
  # Explicit zero: "silent because clean" is indistinguishable from "summary
  # not wired" — always emit the variable, even when the log is absent.
  echo "ENHANCE_MISSES_7D=0  (log absent — no misses recorded)"
fi
exit 0
