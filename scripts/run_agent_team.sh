#!/usr/bin/env bash
# run_agent_team.sh — run an agent-team task FULLY AUTONOMOUSLY on Windows via psmux.
#
# Agent teams need an interactive TTY (headless `claude -p` forms none). On Windows the reliable
# way to give claude a TTY from a plain shell is **psmux** — a native ConPTY tmux clone (Rust),
# installed without WSL or admin (winget `psmux`, scoop, or the portable zip from
# github.com/psmux/psmux; this repo uses C:\Users\itsab\.local\psmux\psmux.exe). winpty is
# UNRELIABLE here (degraded to 0%); psmux is reliable — VERIFIED 2026-06-23 forming real teams
# (TaskCompleted by=<teammate>) driven entirely headlessly.
#
# CRITICAL: do NOT redirect claude's stdout (e.g. `claude ... > file`) — a redirected stdout is
# non-tty and claude falls back to non-team mode. Let claude write to the psmux pane; read it with
# `capture-pane`. The ground-truth signal that a REAL team formed is a NEW
# `TaskCompleted by=<teammate>` line in .claude/.team-activity.log (NOT by=lead/unattributed).
#
# Usage: run_agent_team.sh "<team prompt>" [label] [timeout_sec]
set -u

HUB="D:/Abhay/VibeCoding/claude-best-practices"
SETTINGS_WIN='D:\Abhay\VibeCoding\claude-best-practices\.claude\.team-demo\settings.json'
CLAUDE_WIN='C:\Users\itsab\.local\bin\claude.exe'
PSMUX="$(command -v psmux 2>/dev/null || echo /c/Users/itsab/.local/psmux/psmux.exe)"
LOG="$HUB/.claude/.team-activity.log"
PROMPT="${1:?need a team prompt}"
LABEL="${2:-team}"
TIMEOUT="${3:-300}"
WORKDIR_WIN="${4:-D:\\Abhay\\VibeCoding\\claude-best-practices}"  # cwd the claude lead runs in
export TMUX_TMPDIR=/tmp
cd "$HUB" || exit 3
[ -x "$PSMUX" ] || { echo "psmux not found at $PSMUX — install: winget install psmux (or portable zip)"; exit 2; }

teammate_completions() {
  # Count REAL teammate-attributed events. Two durable signals: `TaskCompleted by=<teammate>`
  # (task-driven modes) AND `TeammateIdle teammate=<name>` (message-driven modes like brainstorm,
  # where teammates communicate via messages rather than marking tasks complete). Excludes the
  # lead's own/unattributed completions.
  grep -E "(TaskCompleted.*\bby=)|(TeammateIdle.*\bteammate=)" "$LOG" 2>/dev/null \
    | grep -v "by=lead/unattributed" | grep -c . || echo 0
}

# Write the launcher .cmd (NO stdout redirect — that would defeat claude's tty).
CMDFILE="$HUB/.claude/.team-cmd-${LABEL}.cmd"
printf '@echo off\r\ncd /d "%s"\r\n"%s" --settings "%s" --permission-mode bypassPermissions "%s"\r\n' \
  "$WORKDIR_WIN" "$CLAUDE_WIN" "$SETTINGS_WIN" "$PROMPT" > "$CMDFILE"

before=$(teammate_completions)
sess="t_${LABEL}"
"$PSMUX" kill-session -t "$sess" 2>/dev/null
echo "=== run_agent_team [$LABEL]: launching claude in psmux (before=$before, timeout=${TIMEOUT}s) ==="
"$PSMUX" new-session -d -s "$sess" -x 220 -y 50 "cmd /c \"$(cygpath -w "$CMDFILE")\"" \
  || { echo "psmux new-session failed"; exit 2; }

waited=0
while [ "$waited" -lt "$TIMEOUT" ]; do
  sleep 6; waited=$((waited+6))
  now=$(teammate_completions)
  alive=$("$PSMUX" ls 2>/dev/null | grep -c "^${sess}:")
  if [ "$now" -gt "$before" ]; then
    echo "RESULT: REAL TEAM FORMED ($((now-before)) teammate-attributed completions) for [$LABEL]"
    grep "TaskCompleted" "$LOG" | grep -v "by=lead/unattributed" | grep "by=" | tail -n $((now-before))
    sleep 10  # allow the lead to finish synthesizing
    "$PSMUX" capture-pane -t "$sess" -p 2>/dev/null | tr -d '\000' > "$HUB/.claude/.team-out-${LABEL}.txt"
    echo "synthesis captured -> .claude/.team-out-${LABEL}.txt"
    "$PSMUX" kill-session -t "$sess" 2>/dev/null
    exit 0
  fi
  [ "$alive" -eq 0 ] && { echo "psmux session ended before a real team formed"; break; }
done
echo "--- last pane content (diagnostic) ---"
"$PSMUX" capture-pane -t "$sess" -p 2>/dev/null | tr -d '\000' | grep -avE '^[[:space:]]*$' | tail -15
"$PSMUX" kill-session -t "$sess" 2>/dev/null
echo "RESULT: FAILED to form a real team for [$LABEL] within ${TIMEOUT}s"
exit 1
