#!/usr/bin/env bash
# run_agent_team.sh — run an agent-team task FULLY AUTONOMOUSLY on Windows.
#
# Agent teams are an interactive feature: headless `claude -p` forms NO real team, and the
# only PTY available here is `winpty` (no util-linux `script`). A winpty-wrapped `claude`
# with a prompt arg forms a real team and SELF-EXITS on stdin-EOF once the team finishes —
# but winpty's console allocation is FLAKY (~half the launches fail fast with
# "stdin is not a tty"). This launcher makes it reliable: retry-on-flaky + verify a REAL
# team via the durable activity-log signal (TaskCompleted by=<teammate>, NOT lead/unattributed)
# + extract the lead's final synthesis. No terminal interaction required.
#
# PLATFORM CAVEAT (measured 2026-06-23): winpty PTY allocation is UNRELIABLE inside the
# Claude Code Bash-tool sandbox on Windows — it worked ~twice then degraded to 0% across
# every invocation pattern (foreground, `timeout`-wrapped, backgrounded subshell). This
# launcher is therefore the CORRECT design but only reliable where a REAL/clean PTY exists:
# a util-linux `script -qec` host (Linux/WSL/macOS) or a fresh interactive terminal. On a
# WSL distro, swap the winpty line for: script -qec "claude --settings ... '<prompt>'" /dev/null
# Headless `claude -p` forms NO team, so a PTY is mandatory. See
# docs/contracts/2026-06-23-agent-teams-readonly-validation-attempt.md for the full finding.
#
# Usage: run_agent_team.sh "<team prompt>" [label] [max_retries] [timeout_sec]
set -u

HUB="D:/Abhay/VibeCoding/claude-best-practices"
SETTINGS="$HUB/.claude/.team-demo/settings.json"
LOG="$HUB/.claude/.team-activity.log"
PROMPT="${1:?need a team prompt}"
LABEL="${2:-team}"
MAX="${3:-5}"
TIMEOUT="${4:-300}"
cd "$HUB" || exit 3

teammate_completions() {  # count of REAL teammate-attributed completions
  grep "TaskCompleted" "$LOG" 2>/dev/null | grep -v "by=lead/unattributed" | grep -c "by=" || echo 0
}

echo "=== run_agent_team [$LABEL] : up to $MAX attempts, ${TIMEOUT}s each ==="
for attempt in $(seq 1 "$MAX"); do
  before=$(teammate_completions)
  out="$HUB/.claude/.team-run-${LABEL}-${attempt}.out"
  echo "--- attempt $attempt: launching winpty claude (before=$before) ---"
  # IMPORTANT: winpty must run in a BACKGROUNDED subshell (proven pattern) — a `timeout`
  # wrapper or foreground run detaches stdin and winpty fails "stdin is not a tty".
  ( winpty claude --settings "$SETTINGS" --permission-mode bypassPermissions "$PROMPT" > "$out" 2>&1 ) &
  pid=$!
  waited=0
  while kill -0 "$pid" 2>/dev/null && [ "$waited" -lt "$TIMEOUT" ]; do sleep 5; waited=$((waited+5)); done
  kill "$pid" 2>/dev/null; wait "$pid" 2>/dev/null
  rc=0
  after=$(teammate_completions)
  echo "    rc=$rc  teammate_completions: $before -> $after"
  if [ "$after" -gt "$before" ]; then
    echo "RESULT: REAL TEAM FORMED + completed on attempt $attempt (label=$LABEL)"
    echo "NEW teammate-attributed completions:"
    grep "TaskCompleted" "$LOG" | grep -v "by=lead/unattributed" | grep "by=" | tail -n $((after-before))
    exit 0
  fi
  if grep -q "stdin is not a tty" "$out" 2>/dev/null; then
    echo "    flaky winpty PTY allocation failed (stdin is not a tty) — retrying"
    continue
  fi
  echo "    no real team formed (lead-only or other). out tail:"
  tail -4 "$out" 2>/dev/null | tr -d '\000' | grep -avE '^[[:space:]]*$'
done
echo "RESULT: FAILED to form a real team for [$LABEL] after $MAX attempts"
exit 1
