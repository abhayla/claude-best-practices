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
# Hardening (flagged in the 2026-06-24 audit): $PROMPT is interpolated into a generated .cmd inside a
# double-quoted arg. This launcher is internal tooling — pass TRUSTED prompts only. Fail closed on the
# one metacharacter that would break/escape the .cmd arg (a double-quote); rephrase without it.
case "$PROMPT" in
  *'"'*) echo "ERROR: prompt contains a double-quote — unsupported (would break the generated .cmd). Rephrase without quotes."; exit 4 ;;
esac
LABEL="${2:-team}"
TIMEOUT="${3:-600}"
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
# Clear inherited psmux/tmux env so the launched lead does not think it is a NESTED tmux session
# (psmux sets PSMUX_SESSION/TMUX inside its panes → agent-teams would refuse to nest). The ConPTY
# TTY remains, so the lead is still interactive and spawns in-process teammates.
# --append-system-prompt injects an anti-deliberation TEAM-LEAD directive at the system level (read
# first, always) — stronger than skill prose at overriding governance-induced over-deliberation.
printf '@echo off\r\ncd /d "%s"\r\nset "PSMUX_SESSION="\r\nset "TMUX="\r\nset "TMUX_PANE="\r\n"%s" --settings "%s" --permission-mode bypassPermissions --append-system-prompt "TEAM-LEAD MODE: this session runs an agent-team task. When the task uses --team, your VERY FIRST tool call MUST spawn the teammates. Do NOT deliberate, plan, ground-truth the team mechanism, run checks yourself, or review solo before spawning - the --team flag already decided a team is warranted. Spawn immediately; verify and synthesize only AFTER teammates return." "%s"\r\n' \
  "$WORKDIR_WIN" "$CLAUDE_WIN" "$SETTINGS_WIN" "$PROMPT" > "$CMDFILE"

sess="t_${LABEL}"
"$PSMUX" kill-session -t "$sess" 2>/dev/null
# UNIVERSAL durable detection: a real team writes a `subagents/` dir with >=2 teammate transcripts under
# the lead session's transcript dir — this catches BOTH named in-process teammates (alpha/correctness)
# AND agent-type teammates (code-reviewer-agent/planner-researcher-agent), unlike config.json (ephemeral)
# or the named-only team hooks. Snapshot the lead's project transcript dir before launch; the NEW session
# dir with subagents/>=2 is this run's real team. RUN SEQUENTIALLY for clean attribution.
PROJDIR="$HOME/.claude/projects/$(echo "$WORKDIR_WIN" | sed 's#[:\\/]#-#g')"
pre_sessions=$(ls "$PROJDIR" 2>/dev/null | grep -E '\.jsonl$' | sort)
echo "=== run_agent_team [$LABEL]: launching claude in psmux (timeout=${TIMEOUT}s) ==="
"$PSMUX" new-session -d -s "$sess" -x 220 -y 50 "cmd /c \"$(cygpath -w "$CMDFILE")\"" \
  || { echo "psmux new-session failed"; exit 2; }

real_team_dir() {  # echo "<session>:<teammates>" for a NEW lead session with a subagents/ dir of >=2
  local f sid n
  for f in $(comm -13 <(echo "$pre_sessions") <(ls "$PROJDIR" 2>/dev/null | grep -E '\.jsonl$' | sort)); do
    sid="${f%.jsonl}"
    n=$(ls "$PROJDIR/$sid/subagents/" 2>/dev/null | grep -c '\.jsonl$')
    [ "$n" -ge 2 ] 2>/dev/null && { echo "$sid:$n"; return; }
  done
}

waited=0
while [ "$waited" -lt "$TIMEOUT" ]; do
  sleep 6; waited=$((waited+6))
  hit=$(real_team_dir)
  alive=$("$PSMUX" ls 2>/dev/null | grep -c "^${sess}:")
  if [ -n "$hit" ]; then
    echo "RESULT: REAL TEAM FORMED — lead session ${hit%%:*} spawned ${hit##*:} teammate sessions (subagents/) for [$LABEL]"
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
